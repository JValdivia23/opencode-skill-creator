#!/usr/bin/env python3
"""First-run setup for the zotero skill.

Writes ~/.zotero-skill/config.toml with the user's chosen output
directory. Validates the toolchain (zot CLI, pymupdf4llm). Does NOT
run the smoke test — the smoke test is in references/getting-started.md
step 6 and is driven by the agent interactively, so the user picks a
real paper from their own library (not a hard-coded fixture).

Usage:
    python scripts/setup.py            # first run / re-run
    python scripts/setup.py --check    # exit 0 if config is valid
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from pathlib import Path

# Internal module — leading underscore signals "skill-internal."
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config  # noqa: E402

CONFIG_PATH = _config.CONFIG_PATH

REQUIRED_DEPS = [
    ("zot", "uv tool install zotero-cli-cc", "the zotero CLI (search/read your library)"),
    ("pymupdf4llm", "pip install pymupdf4llm", "PDF-to-Markdown conversion"),
]

OPTIONAL_DEPS = [
    ("zot-add-identifier", "see references/add-by-identifier.md",
     "add papers by DOI/arXiv/ISBN/PMID with full metadata"),
    ("tesseract", "brew install tesseract   # or apt-get install tesseract-ocr",
     "OCR for scanned PDFs"),
]


def check_dependencies() -> list[str]:
    """Return a list of human-readable error strings for any missing deps.
    Empty list = everything required is present."""
    errors: list[str] = []
    for name, install, _desc in REQUIRED_DEPS:
        if name == "zot":
            if shutil.which(name) is None:
                errors.append(f"  - `{name}` not found on PATH. Install with: {install}")
        else:
            try:
                importlib.import_module(name)
            except ImportError:
                errors.append(f"  - `{name}` not importable. Install with: {install}")
    return errors


def check_optional_dependencies() -> list[str]:
    """Return a list of names of missing optional deps (for info, not error)."""
    missing: list[str] = []
    for name, _install, _desc in OPTIONAL_DEPS:
        if name == "tesseract":
            if shutil.which(name) is None:
                missing.append(name)
        else:
            if shutil.which(name) is None:
                missing.append(name)
    return missing


def write_config(output_dir: str) -> None:
    """Write ~/.zotero-skill/config.toml. Creates parent dir if needed."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"# Zotero skill config — written by scripts/setup.py\n"
        f"# Edit freely. Re-run `python scripts/setup.py` to reset.\n"
        f"\n"
        f"# Where converted Markdown files are written.\n"
        f"# ~ expands to your home directory.\n"
        f'output_dir = "{output_dir}"\n'
        f"\n"
        f"# File layout. One of:\n"
        f"#   flat          -> output_dir/Author_Year_Title.md        (default)\n"
        f"#   by-year       -> output_dir/2024/Author_Year_Title.md\n"
        f"#   by-collection -> output_dir/<Zotero collection>/Author_Year_Title.md\n"
        f'layout = "flat"\n'
        f"\n"
        f"# Optional: Zotero local database. Uncomment to override.\n"
        f"# zotero_db = \"~/Zotero/zotero.sqlite\"\n"
        f"# zotero_storage = \"~/Zotero/storage\"\n"
    )
    CONFIG_PATH.write_text(content, encoding="utf-8")


def cmd_check() -> int:
    """`--check` mode: validate config + required deps. Exit 0 on success."""
    dep_errors = check_dependencies()
    if dep_errors:
        print("Missing required dependencies:", file=sys.stderr)
        for e in dep_errors:
            print(e, file=sys.stderr)
        return 1
    try:
        cfg = _config.load_config()
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    if "output_dir" not in cfg:
        print(f"config at {CONFIG_PATH} is missing 'output_dir'", file=sys.stderr)
        return 1
    try:
        out = _config.output_dir()
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 1
    print(f"OK  config:  {CONFIG_PATH}")
    print(f"OK  output:  {out}")
    missing_opt = check_optional_dependencies()
    if missing_opt:
        print(f"info: optional deps not installed (not blocking): {', '.join(missing_opt)}")
    return 0


def cmd_setup() -> int:
    """First-run / re-run setup. Interactive: asks for output_dir."""
    print("Zotero skill — first-time setup")
    print("=" * 50)
    print()

    # 1. Required dependencies
    dep_errors = check_dependencies()
    if dep_errors:
        print("Cannot proceed: missing required dependencies.")
        print()
        for e in dep_errors:
            print(e)
        print()
        print("Install the missing tools, then re-run `python scripts/setup.py`.")
        return 1
    print("[1/3] Required dependencies OK  (zot, pymupdf4llm)")
    print()

    missing_opt = check_optional_dependencies()
    if missing_opt:
        print(f"[info] optional deps not installed: {', '.join(missing_opt)}")
        print("       these are not required for the core workflow")
        print("       (see references/add-by-identifier.md and references/configuration.md)")
        print()

    # 2. Existing config?
    if CONFIG_PATH.exists():
        print(f"[2/3] Existing config found at {CONFIG_PATH}")
        ans = input("       Overwrite? [y/N] ").strip().lower()
        if ans != "y":
            print("Setup cancelled. Existing config kept.")
            return 0
    else:
        print("[2/3] No existing config.")

    # 3. Ask for output directory
    print()
    print("[3/3] Where should converted Markdown files be stored?")
    print()
    print("       Common choices:")
    print("         1. ~/Documents/papers-md/                  (single flat folder)")
    print("         2. ~/Documents/ObsidianVault/papers/       (inside an Obsidian vault)")
    print("         3. <current-project>/raw/                  (project-local)")
    print("         4. a custom path")
    print()
    raw = input("       Path (or 1/2/3/4): ").strip()
    if raw == "1":
        out = "~/Documents/papers-md/"
    elif raw == "2":
        out = "~/Documents/ObsidianVault/papers/"
    elif raw == "3":
        cwd_name = Path.cwd().name or "project"
        out = f"./{cwd_name}-papers-md/"
    elif raw == "4":
        out = input("       Custom path: ").strip()
    else:
        out = raw  # treat as a raw path the user typed

    write_config(out)

    # Re-validate (so a typo in the path is caught now, not at first convert)
    try:
        validated = _config.output_dir()
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        print("Setup wrote the config but the path is not usable. Re-run setup.py to fix.", file=sys.stderr)
        return 1

    print()
    print("Wrote config:")
    print("-" * 50)
    print(CONFIG_PATH.read_text(encoding="utf-8").rstrip())
    print("-" * 50)
    print()
    print(f"Output dir: {validated}")
    print()
    print("Setup is done.")
    print()
    print("Next: walk through the smoke test with your agent.")
    print("      See references/getting-started.md step 6 — the agent")
    print("      will pick the first paper from your library and convert")
    print("      it to a .md file in your output_dir. If that succeeds,")
    print("      you're fully set up.")
    print()
    print("You can re-run `python scripts/setup.py` at any time to change")
    print("the output path or reset the config.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Zotero skill — first-run setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate config + required deps. Exit 0 on success, 1 on failure. "
             "Used by agents as a re-entry diagnostic.",
    )
    args = parser.parse_args()
    if args.check:
        return cmd_check()
    return cmd_setup()


if __name__ == "__main__":
    sys.exit(main())
