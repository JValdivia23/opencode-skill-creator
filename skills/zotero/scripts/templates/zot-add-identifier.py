#!/usr/bin/env python3
"""zot-add-identifier: Add items to Zotero by identifier (DOI/arXiv/ISBN/PMID).

Uses the Zotero translation-server (Node.js, see zot-translation-server)
to resolve metadata, then creates the item in Zotero via pyzotero.

Installed by skills/zotero/scripts/install_add_identifier.sh. The
shebang is generic so this works on any Python 3.11+ install where
pyzotero, requests, and httpx are importable.

Requires:
  - ~/.config/zot/config.toml (from `zot config init`)
  - zot-translation-server on PATH (installed alongside this script)
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

TRANSLATION_SERVER_URL = "http://127.0.0.1:1969"
SERVER_START_TIMEOUT = 20  # seconds
ACTIVITY_FILE = "/tmp/translation-server.last-active"

DOI_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,}(?:\.\d+)*/.+)$", re.IGNORECASE)
ARXIV_RE = re.compile(r"^(?:https?://arxiv\.org/(?:abs|pdf)/)?(?:arxiv:)?(\d{4,5}\.\d{4,5}(?:v\d+)?)$", re.IGNORECASE)
ISBN_RE = re.compile(r"^(?:ISBN[-\s]*)?(\d{9}[\dX]|\d{13})$", re.IGNORECASE)
PMID_RE = re.compile(r"^(?:PMID[:\s]*)?(\d+)$", re.IGNORECASE)


def load_zotero_config() -> dict:
    """Load Zotero CLI config for API credentials."""
    config_path = Path.home() / ".config" / "zot" / "config.toml"
    if not config_path.exists():
        print("Error: Zotero CLI config not found at ~/.config/zot/config.toml.", file=sys.stderr)
        print("Run: zot config init", file=sys.stderr)
        sys.exit(1)
    import tomllib
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    return cfg.get("zotero", cfg)


def ensure_translation_server() -> None:
    """Start translation server if not already running."""
    try:
        import httpx
        httpx.get(TRANSLATION_SERVER_URL, timeout=2)
        Path(ACTIVITY_FILE).touch()
        return
    except Exception:
        pass

    print("Starting Zotero translation server...", file=sys.stderr)
    subprocess.run(["zot-translation-server", "start"], check=True)

    import httpx
    start = time.time()
    while time.time() - start < SERVER_START_TIMEOUT:
        try:
            httpx.get(TRANSLATION_SERVER_URL, timeout=2)
            Path(ACTIVITY_FILE).touch()
            return
        except Exception:
            time.sleep(0.5)

    print("Error: Translation server failed to start", file=sys.stderr)
    sys.exit(1)


def classify_identifier(text: str) -> tuple:
    """Classify an identifier string. Returns (type, normalized_id)."""
    text = text.strip()

    for regex, kind in [(ARXIV_RE, "arxiv"), (DOI_RE, "doi"),
                         (PMID_RE, "pmid"), (ISBN_RE, "isbn")]:
        m = regex.match(text)
        if m:
            return (kind, m.group(1))

    if text.lower().startswith("10."):
        return ("doi", text)
    return ("unknown", text)


def resolve_identifier(id_type: str, id_value: str) -> Optional[dict]:
    """Query translation-server for metadata. Returns Zotero item dict or None."""
    import httpx

    if id_type == "arxiv":
        url = f"https://arxiv.org/abs/{id_value}"
        try:
            resp = httpx.post(
                f"{TRANSLATION_SERVER_URL}/web",
                content=url,
                headers={"Content-Type": "text/plain"},
                timeout=30,
            )
            resp.raise_for_status()
            items = resp.json()
            if items:
                Path(ACTIVITY_FILE).touch()
                return items[0]
        except httpx.HTTPStatusError as e:
            print(f"Error resolving arxiv:{id_value}: HTTP {e.response.status_code}", file=sys.stderr)
        except Exception as e:
            print(f"Error resolving arxiv:{id_value}: {e}", file=sys.stderr)
        return None

    try:
        resp = httpx.post(
            f"{TRANSLATION_SERVER_URL}/search",
            content=id_value,
            headers={"Content-Type": "text/plain"},
            timeout=30,
        )
        resp.raise_for_status()
        items = resp.json()
        if items:
            Path(ACTIVITY_FILE).touch()
            return items[0]
    except httpx.HTTPStatusError as e:
        print(f"Error resolving {id_type}:{id_value}: HTTP {e.response.status_code}", file=sys.stderr)
    except Exception as e:
        print(f"Error resolving {id_type}:{id_value}: {e}", file=sys.stderr)
    return None


def create_zotero_item(item_data: dict, cfg: dict) -> Optional[str]:
    """Create item in Zotero via pyzotero. Returns item key or None."""
    library_id = cfg.get("library_id")
    api_key = cfg.get("api_key")
    library_type = cfg.get("library_type", "user")

    if not library_id or not api_key:
        print("Error: Missing Zotero API credentials in config", file=sys.stderr)
        return None

    try:
        from pyzotero import zotero
        zot = zotero.Zotero(str(library_id), library_type, api_key)
        resp = zot.create_items([item_data])
        if resp.get("successful") and "0" in resp["successful"]:
            return resp["successful"]["0"]["key"]
        msg = resp.get("failed", {}).get("0", {}).get("message", "Unknown API error")
        print(f"Zotero API error: {msg}", file=sys.stderr)
    except Exception as e:
        print(f"Error creating Zotero item: {e}", file=sys.stderr)
    return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add items to Zotero by identifier (DOI, arXiv, ISBN, PMID)."
    )
    parser.add_argument("identifiers", nargs="*", help="Identifier(s) to add")
    parser.add_argument("--doi", action="append", default=[])
    parser.add_argument("--arxiv", action="append", default=[])
    parser.add_argument("--isbn", action="append", default=[])
    parser.add_argument("--pmid", action="append", default=[])
    parser.add_argument("--batch", type=Path, help="File with one identifier per line")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating items")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    all_ids: list[tuple[str, str]] = []
    for text in args.identifiers:
        all_ids.append(classify_identifier(text))
    for v in args.doi:   all_ids.append(("doi", v))
    for v in args.arxiv: all_ids.append(("arxiv", v))
    for v in args.isbn:  all_ids.append(("isbn", v))
    for v in args.pmid:  all_ids.append(("pmid", v))

    if args.batch:
        if not args.batch.exists():
            print(f"Error: Batch file not found: {args.batch}", file=sys.stderr)
            sys.exit(1)
        for line in args.batch.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                all_ids.append(classify_identifier(line))

    if not all_ids:
        print("Error: No identifiers provided", file=sys.stderr)
        parser.print_help()
        sys.exit(1)

    if args.dry_run:
        if args.json:
            print(json.dumps({"dry_run": True, "items": [{"type": t, "identifier": v} for t, v in all_ids]}, indent=2))
        else:
            print("[dry-run] Would resolve and add:")
            for t, v in all_ids:
                print(f"  {t}: {v}")
        sys.exit(0)

    ensure_translation_server()
    cfg = load_zotero_config()

    results = []
    for id_type, id_value in all_ids:
        if not args.json:
            print(f"Resolving {id_type}: {id_value} ...", file=sys.stderr)
        item_data = resolve_identifier(id_type, id_value)
        if not item_data:
            results.append({"identifier": id_value, "type": id_type, "status": "failed",
                            "error": "Could not resolve metadata"})
            continue
        key = create_zotero_item(item_data, cfg)
        if key:
            title = item_data.get("title", "[No Title]")
            results.append({"identifier": id_value, "type": id_type, "status": "success",
                            "key": key, "title": title})
            if not args.json:
                print(f"  Created: {key} - {title}")
        else:
            results.append({"identifier": id_value, "type": id_type, "status": "failed",
                            "error": "Zotero API error"})

    if args.json:
        print(json.dumps({"results": results}, indent=2, ensure_ascii=False))
    else:
        ok = sum(1 for r in results if r["status"] == "success")
        fail = sum(1 for r in results if r["status"] == "failed")
        print(f"\nDone: {ok} added, {fail} failed", file=sys.stderr)
        if ok:
            print("Run 'zot sync' to update local database.", file=sys.stderr)


if __name__ == "__main__":
    main()
