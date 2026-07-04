#!/usr/bin/env python3
"""Stage a Zotero item to Markdown: frontmatter + body in one step.

Wraps the v1.0.2 staging workflow into a single command:
    1. zot --json read <KEY>           -> metadata
    2. resolve the PDF's local path     -> ~/Zotero/storage/<attach_key>/<file>
    3. python scripts/pdf2md.py <pdf>   -> body
    4. prepend YAML frontmatter         -> Author_Year_Title.md in output_dir

Usage:
    python scripts/stage.py <KEY>                    # full staging
    python scripts/stage.py <KEY> --dry-run          # print plan, no writes
    python scripts/stage.py <KEY> --pdf <path>       # override auto-resolved PDF
    python scripts/stage.py <KEY> -o <path>          # override output path
    python scripts/stage.py <KEY> --no-frontmatter   # raw convert only
    python scripts/stage.py <KEY> --force            # overwrite existing .md
    python scripts/stage.py --schema                 # print frontmatter schema
    python scripts/stage.py --check <file.md>        # validate existing .md

Requires: zot CLI, pymupdf4llm (via pdf2md.py), ~/.zotero-skill/config.toml.
Optional: PyYAML (for frontmatter round-trip validation; skipped if absent).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

# Internal module — leading underscore signals "skill-internal."
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config  # noqa: E402

DEFAULT_ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"
DEFAULT_ZOTERO_STORAGE = Path.home() / "Zotero" / "storage"

# The 14 frontmatter fields this script emits (sourced from zot --json read).
SCHEMA_FIELDS = [
    "title", "authors", "year", "doi", "abstract", "tags", "collections",
    "item_key", "item_type", "source_url", "date", "date_added",
    "date_modified", "pdf_path",
]


def _die(msg: str) -> int:
    print(f"Error: {msg}", file=sys.stderr)
    return 1


def _q(s: str) -> str:
    """YAML double-quoted scalar: escape backslash and double-quote."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _first_author_last(creators: list) -> str:
    """First author's last name (fallback: first creator, else 'Unknown')."""
    authors = [c for c in creators if c.get("creator_type") == "author"]
    pool = authors or creators
    if not pool:
        return "Unknown"
    return pool[0].get("last_name") or "Unknown"


def _zot_read(key: str) -> dict:
    """Run `zot --json read <KEY>` and return the item data object."""
    if not shutil.which("zot"):
        _die("zot CLI not found on PATH. Install with: uv tool install zotero-cli-cc")
        sys.exit(1)
    result = subprocess.run(
        ["zot", "--json", "read", key], capture_output=True, text=True
    )
    if result.returncode != 0:
        _die(f"zot read {key} failed:\n{result.stderr.strip()}")
        sys.exit(1)
    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        _die(f"zot read {key} returned invalid JSON: {e}")
        sys.exit(1)
    if not envelope.get("ok"):
        _die(f"zot read {key} returned ok=false:\n{envelope}")
        sys.exit(1)
    data = envelope.get("data")
    if not data:
        _die(f"Zotero item {key} not found (no data returned).")
        sys.exit(1)
    return data


def _resolve_pdf_path(item_key: str, zotero_db: Path, zotero_storage: Path) -> str | None:
    """Resolve a Zotero item's PDF via SQLite (parent key -> attachment).

    Returns ~/Zotero/storage/<attach_key>/<filename> for the first
    attachment whose file exists on disk, else the first attachment's
    path (even if missing), else None.
    """
    if not zotero_db.exists():
        _die(f"Zotero database not found: {zotero_db}")
        sys.exit(1)
    db_uri = f"file:{zotero_db}?mode=ro&immutable=1"
    try:
        conn = sqlite3.connect(db_uri, uri=True)
    except sqlite3.OperationalError as e:
        _die(
            f"cannot open Zotero database read-only: {e}\n"
            f"  Hint: if Zotero desktop is running, the SQLite file is locked.\n"
            f"  Close Zotero, or pass --pdf <path> to bypass auto-resolution."
        )
        sys.exit(1)
    try:
        cur = conn.execute(
            "SELECT attach.key, ia.path "
            "FROM items parent "
            "JOIN itemAttachments ia ON ia.parentItemID = parent.itemID "
            "  AND ia.contentType = 'application/pdf' "
            "JOIN items attach ON attach.itemID = ia.itemID "
            "WHERE parent.key = ?;",
            (item_key,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    for attach_key, attach_path in rows:
        if attach_path and attach_path.startswith("storage:"):
            filename = attach_path.replace("storage:", "", 1)
            full = zotero_storage / attach_key / filename
            if full.exists():
                return str(full)
    # Fallback: return the first attachment path even if file is missing.
    for attach_key, attach_path in rows:
        if attach_path and attach_path.startswith("storage:"):
            filename = attach_path.replace("storage:", "", 1)
            return str(zotero_storage / attach_key / filename)
    return None


def _build_frontmatter(data: dict, pdf_path: str) -> str:
    """Build the 14-field YAML frontmatter block by hand.

    - double-quoted scalars via _q() (titles/paths with colons, spaces, etc.)
    - block scalar (|) for abstract (preserves text verbatim, no escaping)
    - inline [] for empty lists; abstract omitted entirely if empty
    """
    title = data.get("title", "")
    creators = data.get("creators", []) or []
    authors = [
        f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
        for c in creators
    ]
    year = data.get("date", "")[:4]
    doi = data.get("doi", "")
    abstract = data.get("abstract", "")
    tags = data.get("tags", []) or []
    collections = data.get("collections", []) or []
    item_key = data.get("key", "")
    item_type = data.get("item_type", "")
    source_url = data.get("url", "")
    date = data.get("date", "")
    date_added = data.get("date_added", "")
    date_modified = data.get("date_modified", "")

    lines = ["---"]
    lines.append(f"title: {_q(title)}")
    if authors:
        lines.append("authors:")
        for a in authors:
            lines.append(f"  - {_q(a)}")
    else:
        lines.append("authors: []")
    lines.append(f"year: {_q(year)}")
    lines.append(f"doi: {_q(doi)}")
    if abstract:
        lines.append("abstract: |")
        for ln in abstract.splitlines() or [abstract]:
            lines.append("  " + ln)
    # (abstract omitted entirely if empty — cleaner than abstract: "")
    if tags:
        lines.append("tags:")
        for t in tags:
            lines.append(f"  - {_q(t)}")
    else:
        lines.append("tags: []")
    if collections:
        lines.append("collections:")
        for c in collections:
            lines.append(f"  - {_q(c)}")
    else:
        lines.append("collections: []")
    lines.append(f"item_key: {_q(item_key)}")
    lines.append(f"item_type: {_q(item_type)}")
    lines.append(f"source_url: {_q(source_url)}")
    lines.append(f"date: {_q(date)}")
    lines.append(f"date_added: {_q(date_added)}")
    lines.append(f"date_modified: {_q(date_modified)}")
    lines.append(f"pdf_path: {_q(pdf_path)}")
    lines.append("---")
    return "\n".join(lines)


def _validate_frontmatter(frontmatter_block: str, data: dict, key: str) -> None:
    """Round-trip check: safe_load the block and assert key fields match."""
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        print("warning: PyYAML not installed; skipping frontmatter validation",
              file=sys.stderr)
        return
    try:
        parsed = yaml.safe_load(frontmatter_block)
    except Exception as e:
        _die(f"emitted frontmatter is not valid YAML: {e}")
        sys.exit(1)
    if not isinstance(parsed, dict):
        _die(f"emitted frontmatter did not parse to a dict: {parsed!r}")
        sys.exit(1)
    assert parsed.get("item_key") == key, \
        f"item_key round-trip mismatch: {parsed.get('item_key')} != {key}"
    assert parsed.get("year") == data.get("date", "")[:4], "year round-trip mismatch"
    assert len(parsed.get("authors", [])) == len(data.get("creators", []) or []), \
        "authors count round-trip mismatch"
    assert len(parsed.get("tags", [])) == len(data.get("tags", []) or []), \
        "tags count round-trip mismatch"


def _run_pdf2md_body(pdf_path: str, output_path: Path) -> None:
    """Shell out to pdf2md.py to write the body to output_path."""
    scripts_dir = Path(__file__).resolve().parent
    pdf2md = scripts_dir / "pdf2md.py"
    if not pdf2md.exists():
        _die(f"pdf2md.py not found at {pdf2md}")
        sys.exit(1)
    cmd = [sys.executable, str(pdf2md), str(pdf_path), "-o", str(output_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        _die(f"pdf2md.py failed (exit {result.returncode}):\n{result.stderr.strip()}")
        sys.exit(1)


def cmd_schema(args) -> int:
    """Print the frontmatter schema."""
    print("# v1.0.2 frontmatter schema (14 fields, sourced from `zot --json read`)")
    print("```yaml")
    print("---")
    print('title: "<data.title>"')
    print("authors:                            # one entry per creator")
    print('  - "<first_name last_name>"')
    print('year: "<data.date, first 4 chars>"')
    print('doi: "<data.doi>"')
    print("abstract: |                         # block scalar; omitted if empty")
    print("  <data.abstract>")
    print("tags: []                            # from data.tags")
    print("collections:                        # from data.collections")
    print('  - "<collection key>"')
    print('item_key: "<data.key>"')
    print('item_type: "<data.item_type>"')
    print('source_url: "<data.url>"')
    print('date: "<data.date>"')
    print('date_added: "<data.date_added>"')
    print('date_modified: "<data.date_modified>"')
    print('pdf_path: "<resolved local PDF path>"')
    print("---")
    print("```")
    return 0


def cmd_check(args) -> int:
    """Validate an existing .md's frontmatter against the schema."""
    f = Path(args.check)
    if not f.exists():
        return _die(f"file not found: {f}")
    text = f.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return _die(f"no YAML frontmatter found in {f}")
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return _die("PyYAML required for --check (pip install pyyaml)")
    try:
        parsed = yaml.safe_load(m.group(1))
    except Exception as e:
        return _die(f"frontmatter is not valid YAML: {e}")
    if not isinstance(parsed, dict):
        return _die(f"frontmatter did not parse to a dict: {parsed!r}")
    required = ["title", "authors", "year", "item_key", "item_type"]
    missing = [k for k in required if k not in parsed]
    if missing:
        return _die(f"missing required fields: {missing}")
    print(f"OK  {f.name}")
    print(f"  title    : {parsed.get('title')}")
    print(f"  authors  : {len(parsed.get('authors', []))}")
    print(f"  year     : {parsed.get('year')}")
    print(f"  item_key : {parsed.get('item_key')}")
    print(f"  item_type: {parsed.get('item_type')}")
    present = [k for k in SCHEMA_FIELDS if k in parsed]
    print(f"  fields   : {len(present)}/{len(SCHEMA_FIELDS)} ({', '.join(present)})")
    return 0


def cmd_stage(args) -> int:
    key = args.key
    data = _zot_read(key)

    # Resolve PDF path (CLI override > SQLite).
    if args.pdf:
        pdf_path = args.pdf
        if not Path(pdf_path).exists():
            return _die(f"PDF not found (--pdf): {pdf_path}")
    else:
        pdf_path = _resolve_pdf_path(key, args.zotero_db, args.zotero_storage)
        if not pdf_path:
            return _die(
                f"Zotero item {key} has no PDF attachment. Open Zotero desktop "
                f"→ right-click → 'Find Available PDF', or attach manually, "
                f"or pass --pdf <path>."
            )
        if not Path(pdf_path).exists():
            return _die(
                f"PDF path resolved but file not on disk: {pdf_path}\n"
                f"  The attachment record exists in Zotero but the file is "
                f"missing. Re-sync Zotero, or pass --pdf <path>."
            )

    # Canonical filename.
    first_author = _first_author_last(data.get("creators", []) or [])
    stem = _config._slugify_canonical(first_author, data.get("date", ""), data.get("title", ""))

    # Output path: -o > <output_dir>/<stem>.md
    if args.output:
        out = Path(args.output)
        if not out.is_absolute():
            # Bare stem -> write into the config's output_dir.
            cfg_dir = _config.output_dir()
            cfg_dir.mkdir(parents=True, exist_ok=True)
            out = cfg_dir / (out.name if out.suffix == ".md" else f"{out}.md")
    else:
        cfg_dir = _config.output_dir()
        cfg_dir.mkdir(parents=True, exist_ok=True)
        out = cfg_dir / f"{stem}.md"

    # Overwrite guard.
    if out.exists() and not args.force and not args.dry_run:
        return _die(
            f"output file already exists: {out}\n"
            f"  Pass --force to overwrite."
        )

    frontmatter = _build_frontmatter(data, pdf_path) if not args.no_frontmatter else ""

    if args.dry_run:
        print("stage.py --dry-run (no writes)")
        print(f"  key        : {key}")
        print(f"  title      : {data.get('title', '')[:80]}")
        print(f"  first author: {first_author}")
        print(f"  pdf        : {pdf_path}")
        print(f"  output     : {out}")
        print(f"  frontmatter: {'yes (14 fields)' if frontmatter else 'no (--no-frontmatter)'}")
        if frontmatter:
            print("  --- preview ---")
            print(frontmatter)
            print("  --- end preview ---")
        return 0

    # Convert body (pdf2md writes body to `out`).
    _run_pdf2md_body(pdf_path, out)

    # Prepend frontmatter.
    if frontmatter:
        _validate_frontmatter(frontmatter, data, key)
        body = out.read_text(encoding="utf-8")
        out.write_text(frontmatter + "\n\n" + body, encoding="utf-8")

    line_count = out.read_text(encoding="utf-8").count("\n") + 1
    print(f"  ✓ Staged {key} -> {out}  ({line_count} lines)")
    if line_count < 50:
        print(
            f"  Note: output is small ({line_count} lines). Likely a scanned PDF; "
            f"see references/configuration.md for OCR (Tesseract).",
            file=sys.stderr,
        )
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Stage a Zotero item to Markdown: frontmatter + body in one step.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("key", nargs="?", help="Zotero item key (e.g. MBSPCFWE)")
    p.add_argument("--dry-run", action="store_true", help="print plan, no writes")
    p.add_argument("--pdf", help="override auto-resolved PDF path")
    p.add_argument("-o", "--output", help="output path (default: <output_dir>/<Author_Year_Title>.md)")
    p.add_argument("--no-frontmatter", action="store_true", help="raw convert only (no frontmatter)")
    p.add_argument("--force", action="store_true", help="overwrite an existing output file")
    p.add_argument("--schema", action="store_true", help="print the frontmatter schema and exit")
    p.add_argument("--check", metavar="FILE", help="validate an existing .md's frontmatter")
    p.add_argument("--zotero-db", type=Path, default=DEFAULT_ZOTERO_DB,
                   help=f"Path to zotero.sqlite (default: {DEFAULT_ZOTERO_DB})")
    p.add_argument("--zotero-storage", type=Path, default=DEFAULT_ZOTERO_STORAGE,
                   help=f"Path to Zotero storage (default: {DEFAULT_ZOTERO_STORAGE})")
    args = p.parse_args()

    if args.schema:
        return cmd_schema(args)
    if args.check:
        return cmd_check(args)
    if not args.key:
        p.print_help(sys.stderr)
        return 1
    return cmd_stage(args)


if __name__ == "__main__":
    sys.exit(main())
