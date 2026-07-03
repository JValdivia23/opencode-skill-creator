"""Shared config loader for the zotero skill scripts.

Internal module — leading underscore signals "do not import directly
from outside this skill." Imported by setup.py, pdf2md.py, and
check_missing_raw.py. CPython prepends the script's directory to
sys.path[0], so `from _config import …` works whether the scripts
are invoked from the repo root, from `scripts/`, or by absolute path.
"""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path
from typing import NoReturn

CONFIG_PATH = Path.home() / ".zotero-skill" / "config.toml"


def _die(msg: str) -> NoReturn:
    """Print a one-line actionable error and exit 1."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_config() -> dict:
    """Read and parse the config file. Exits with an actionable error
    if the file is missing or malformed."""
    if not CONFIG_PATH.exists():
        _die(
            f"config not found at {CONFIG_PATH}. "
            f"Run `python scripts/setup.py` first."
        )
    try:
        return tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        _die(
            f"config at {CONFIG_PATH} is not valid TOML: {e}. "
            f"Re-run `python scripts/setup.py` to recreate it."
        )


def output_dir() -> Path:
    """Return the configured output_dir, ~-expanded and validated."""
    cfg = load_config()
    if "output_dir" not in cfg:
        _die(
            f"config at {CONFIG_PATH} is missing 'output_dir'. "
            f"Re-run `python scripts/setup.py`."
        )
    raw = cfg["output_dir"]
    expanded = Path(os.path.expanduser(raw)).resolve()
    if not expanded.exists():
        try:
            expanded.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            _die(f"cannot create output_dir {expanded}: {e}")
    return expanded
