#!/usr/bin/env python3
"""Convert a local PDF to Markdown using pymupdf4llm.

Slimmed-down version of the wiki/tools/pdf2md.py, adapted for the
public zotero skill. Differences from the wiki version:
  - pymupdf4llm only (no marker, no arxiv2md backends)
  - No arxiv input parser — input must be a local PDF path
  - Default output_dir is read from ~/.zotero-skill/config.toml
    (see scripts/_config.py); -o still wins
  - Path-resolution fix from the wiki version preserved

Usage:
    python scripts/pdf2md.py <path-to.pdf>           # writes to config's output_dir
    python scripts/pdf2md.py <path-to.pdf> -o out.md # explicit output path
    python scripts/pdf2md.py <path-to.pdf> -o -     # write to stdout

Requires: pymupdf4llm. For scanned PDFs without native text, see
references/configuration.md (Tesseract OCR hint).
"""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from pathlib import Path

# Internal module — leading underscore signals "skill-internal."
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config  # noqa: E402


def _slugify(stem: str) -> str:
    """Turn a filename stem into a safe filename."""
    name = re.sub(r"[^\w\s-]", "", stem.lower())
    return re.sub(r"[\s_]+", "-", name).strip("-")


def _resolve_output(pdf_path: Path, output_arg: str | None) -> Path:
    """Determine the output path.

    Precedence: -o flag > config's output_dir. Auto-creates parent dirs.
    """
    if output_arg == "-":
        return None  # type: ignore[return-value]  # sentinel for stdout
    if output_arg:
        p = Path(output_arg)
        if p.is_absolute():
            p.parent.mkdir(parents=True, exist_ok=True)
            return p
        # Relative path: resolve against CWD. Don't double-nest if the
        # user passed something that's already inside their config's
        # output_dir.
        resolved = (Path.cwd() / p).resolve()
        cfg_dir = _config.output_dir()
        if str(resolved).startswith(str(cfg_dir) + "/"):
            resolved.parent.mkdir(parents=True, exist_ok=True)
            return resolved
        cfg_dir.mkdir(parents=True, exist_ok=True)
        return cfg_dir / p.name

    # No -o: write to config's output_dir, slug from PDF stem
    cfg_dir = _config.output_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / f"{_slugify(pdf_path.stem)}.md"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert a local PDF to Markdown (pymupdf4llm).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("pdf", help="path to a local PDF file")
    parser.add_argument(
        "-o", "--output",
        help="output .md path (default: <config output_dir>/<slug>.md); "
             "use '-' to write to stdout",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}", file=sys.stderr)
        return 1
    if pdf_path.suffix.lower() != ".pdf":
        print(f"Error: input is not a .pdf file: {pdf_path}", file=sys.stderr)
        return 1

    # Late import — surface a clean error if pymupdf4llm is missing
    try:
        import pymupdf4llm  # type: ignore[import-not-found]
    except ImportError:
        print(
            "Error: pymupdf4llm is not installed.\n"
            "  Install with: pip install pymupdf4llm",
            file=sys.stderr,
        )
        return 1

    print(f"pdf2md — converting {pdf_path.name}")
    md_text = pymupdf4llm.to_markdown(str(pdf_path))
    # pymupdf4llm can return either a single Markdown string or a
    # list of per-page dicts (depending on the page_chunks kwarg).
    # We want the single-string form. If a list came back, join it.
    if isinstance(md_text, list):
        md_text = "\n\n".join(
            page.get("text", "") if isinstance(page, dict) else str(page)
            for page in md_text
        )

    output_path = _resolve_output(pdf_path, args.output)
    if output_path is None:
        # -o - : stdout
        sys.stdout.write(md_text)
        return 0

    output_path.write_text(md_text, encoding="utf-8")
    line_count = md_text.count("\n") + 1
    print(f"  ✓ Wrote {output_path}  ({line_count} lines)")

    if line_count < 50:
        print(
            f"\n  Note: output is small ({line_count} lines).",
            file=sys.stderr,
        )
        print(
            "  This is normal for image-only / scanned PDFs.",
            file=sys.stderr,
        )
        print(
            "  For OCR-based conversion, see references/configuration.md.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
