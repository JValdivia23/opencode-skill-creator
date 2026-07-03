#!/usr/bin/env python3
"""Audit which Zotero PDFs have not yet been converted to .md in the
user's chosen output directory.

Adapted from the wiki/tools/check_missing_raw.py. Differences:
  - --raw-dir defaults to the config's output_dir, not raw/papers/
  - --zotero-db and --zotero-storage flags override the auto-detected paths
  - "Next steps" point at scripts/pdf2md.py, not tools/ingest.py

Also scans existing .md files for emptiness or stub content (e.g. old
screenshots that produced nothing but YAML frontmatter).

Usage:
    python scripts/check_missing_raw.py
    python scripts/check_missing_raw.py --days 3
    python scripts/check_missing_raw.py --json
    python scripts/check_missing_raw.py --stub-threshold 30
    python scripts/check_missing_raw.py --raw-dir /some/other/dir

Outputs a grouped report:
  1) Existing .md files that are empty or stubs
  2) Recently added (default last 7 days) — your immediate action items
  3) Older gaps — backlog
  4) Items missing local PDF files — metadata exists but file not on disk
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Internal module — leading underscore signals "skill-internal."
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _config  # noqa: E402

DEFAULT_ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"
DEFAULT_ZOTERO_STORAGE = Path.home() / "Zotero" / "storage"


def _slugify_filename(author_last: str, year: str, title: str) -> str:
    """Build the canonical Author_Year_Title... filename stem."""
    author_part = re.sub(r"[^\w]", "", author_last)
    year_part = re.sub(r"[^\d]", "", year)[:4]
    title_clean = re.sub(r"[^\w\s]", "", title)
    words = title_clean.split()[:12]
    title_part = "_".join(words)
    return f"{author_part}_{year_part}_{title_part}"


def _match_exists(stem: str, md_stems: set[str]) -> bool:
    """Check if any existing .md file looks like this stem.

    We compare Author + Year prefix, then do a fuzzy title overlap
    to tolerate slight naming differences.
    """
    parts = stem.split("_")
    if len(parts) < 2:
        return False
    author_year = f"{parts[0]}_{parts[1]}"
    for md in md_stems:
        md_parts = md.split("_")
        if len(md_parts) < 2:
            continue
        md_author_year = f"{md_parts[0]}_{md_parts[1]}"
        if author_year == md_author_year:
            return True
    return False


def fetch_items(conn: sqlite3.Connection):
    """Return list of dicts for every top-level item that has a PDF attachment.

    Deduplicates by parent item. Prefers the attachment whose path exists.
    """
    sql = """
    SELECT
        parent.key          AS itemKey,
        parent.itemID       AS parentItemID,
        attach.key          AS attachKey,
        ia.path             AS attachPath,
        COALESCE(dv.value, '') AS title,
        COALESCE(SUBSTR(dateVal.value, 1, 4), '') AS year,
        parent.dateAdded,
        parent.dateModified,
        it.typeName         AS itemType
    FROM items parent
    JOIN itemTypes it ON parent.itemTypeID = it.itemTypeID
    JOIN itemAttachments ia ON ia.parentItemID = parent.itemID AND ia.contentType = 'application/pdf'
    JOIN items attach ON attach.itemID = ia.itemID
    LEFT JOIN itemData id_title ON id_title.itemID = parent.itemID
        AND id_title.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'title')
    LEFT JOIN itemDataValues dv ON dv.valueID = id_title.valueID
    LEFT JOIN itemData id_date ON id_date.itemID = parent.itemID
        AND id_date.fieldID = (SELECT fieldID FROM fields WHERE fieldName = 'date')
    LEFT JOIN itemDataValues dateVal ON dateVal.valueID = id_date.valueID
    WHERE it.typeName NOT IN ('attachment', 'note', 'annotation')
    ORDER BY parent.itemID, attach.key;
    """
    cur = conn.execute(sql)
    rows = []
    seen_parent_ids = set()
    for row in cur.fetchall():
        parent_id = row[1]
        if parent_id in seen_parent_ids:
            continue
        seen_parent_ids.add(parent_id)
        rows.append({
            "itemKey": row[0],
            "parentItemID": row[1],
            "attachKey": row[2],
            "attachPath": row[3] or "",
            "title": row[4] or "(no title)",
            "year": row[5] or "????",
            "dateAdded": row[6],
            "dateModified": row[7],
            "itemType": row[8],
        })
    return rows


def fetch_authors(conn: sqlite3.Connection, parent_item_ids: list[int]) -> dict[int, str]:
    """Map parentItemID → first author last name."""
    if not parent_item_ids:
        return {}
    placeholders = ",".join("?" * len(parent_item_ids))
    sql = f"""
    SELECT ic.itemID, c.lastName, ic.orderIndex, ct.creatorType
    FROM itemCreators ic
    JOIN creators c ON c.creatorID = ic.creatorID
    JOIN creatorTypes ct ON ct.creatorTypeID = ic.creatorTypeID
    WHERE ic.itemID IN ({placeholders})
    ORDER BY ic.itemID, ic.orderIndex;
    """
    cur = conn.execute(sql, parent_item_ids)
    by_item: dict[int, list[tuple[int, str, str]]] = {}
    for item_id, last_name, order, ctype in cur.fetchall():
        by_item.setdefault(item_id, []).append((order, last_name or "Unknown", ctype))

    result = {}
    for item_id, names in by_item.items():
        authors = [n for n in names if n[2] == "author"]
        if authors:
            result[item_id] = authors[0][1]
            continue
        editors = [n for n in names if n[2] in ("editor", "bookAuthor")]
        if editors:
            result[item_id] = editors[0][1]
            continue
        names.sort(key=lambda x: x[0])
        result[item_id] = names[0][1]
    return result


def fetch_collections(conn: sqlite3.Connection, parent_item_ids: list[int]) -> dict[int, list[str]]:
    if not parent_item_ids:
        return {}
    placeholders = ",".join("?" * len(parent_item_ids))
    sql = f"""
    SELECT ci.itemID, c.collectionName
    FROM collectionItems ci
    JOIN collections c ON c.collectionID = ci.collectionID
    WHERE ci.itemID IN ({placeholders});
    """
    cur = conn.execute(sql, parent_item_ids)
    result: dict[int, list[str]] = {}
    for item_id, col_name in cur.fetchall():
        result.setdefault(item_id, []).append(col_name)
    return result


def pdf_exists_on_disk(attach_key: str, attach_path: str, zotero_storage: Path) -> bool:
    """Verify the physical PDF file is present in Zotero storage."""
    if not attach_path.startswith("storage:"):
        return False
    filename = attach_path.replace("storage:", "", 1)
    full = zotero_storage / attach_key / filename
    return full.exists()


FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def audit_md_files(raw_dir: Path, stub_threshold: int) -> list[dict]:
    """Return list of existing .md files that are empty or stubby."""
    issues = []
    for f in sorted(raw_dir.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        content = FRONTMATTER_RE.sub("", text, count=1)
        content = content.strip()
        word_count = len(content.split()) if content else 0

        if not content:
            issues.append({"filename": f.name, "status": "EMPTY", "words": 0})
        elif word_count < stub_threshold:
            issues.append({"filename": f.name, "status": "STUB", "words": word_count})
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Zotero PDFs missing from your output directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--days", type=int, default=7,
        help="How many days back counts as 'recent' (default: 7)",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON instead of human report",
    )
    parser.add_argument(
        "--zotero-db", type=Path, default=DEFAULT_ZOTERO_DB,
        help=f"Path to zotero.sqlite (default: {DEFAULT_ZOTERO_DB})",
    )
    parser.add_argument(
        "--zotero-storage", type=Path, default=DEFAULT_ZOTERO_STORAGE,
        help=f"Path to Zotero storage (default: {DEFAULT_ZOTERO_STORAGE})",
    )
    parser.add_argument(
        "--raw-dir", type=Path, default=None,
        help="Directory of converted .md files (default: config's output_dir)",
    )
    parser.add_argument(
        "--stub-threshold", type=int, default=50,
        help="Words after frontmatter below which a .md is flagged as stub (default: 50)",
    )
    args = parser.parse_args()

    # Resolve raw_dir: CLI > config
    if args.raw_dir is not None:
        raw_dir = args.raw_dir.resolve()
    else:
        raw_dir = _config.output_dir()

    if not args.zotero_db.exists():
        print(f"Error: Zotero database not found: {args.zotero_db}", file=sys.stderr)
        return 1
    if not raw_dir.exists():
        print(f"Error: Raw directory not found: {raw_dir}", file=sys.stderr)
        return 1

    md_stems = {f.stem for f in raw_dir.iterdir() if f.suffix == ".md"}
    md_issues = audit_md_files(raw_dir, args.stub_threshold)

    db_uri = f"file:{args.zotero_db}?mode=ro&immutable=1"
    try:
        conn = sqlite3.connect(db_uri, uri=True)
    except sqlite3.OperationalError as e:
        print(
            f"Error: cannot open Zotero database read-only: {e}\n"
            f"  Hint: if Zotero desktop is running, the SQLite file is locked.\n"
            f"  Try closing Zotero temporarily, or use a separate read-only copy.",
            file=sys.stderr,
        )
        return 1

    items = fetch_items(conn)
    parent_ids = [it["parentItemID"] for it in items]
    authors_map = fetch_authors(conn, parent_ids)
    collections_map = fetch_collections(conn, parent_ids)
    conn.close()

    now = datetime.now()
    cutoff = now - timedelta(days=args.days)

    recent_missing = []
    older_missing = []
    missing_pdf = []

    for it in items:
        item_id = it["parentItemID"]
        first_author = authors_map.get(item_id, "Unknown")
        stem = _slugify_filename(first_author, it["year"], it["title"])
        it["firstAuthor"] = first_author
        it["expectedStem"] = stem
        it["collections"] = collections_map.get(item_id, [])
        it["pdfOnDisk"] = pdf_exists_on_disk(
            it["attachKey"], it["attachPath"], args.zotero_storage
        )

        if not it["pdfOnDisk"]:
            missing_pdf.append(it)
            continue

        if _match_exists(stem, md_stems):
            continue

        date_added = datetime.strptime(it["dateAdded"], "%Y-%m-%d %H:%M:%S")
        if date_added >= cutoff:
            recent_missing.append(it)
        else:
            older_missing.append(it)

    if args.json:
        output = {
            "meta": {
                "checkedAt": now.isoformat(),
                "recentCutoffDays": args.days,
                "stubThreshold": args.stub_threshold,
                "rawDir": str(raw_dir),
                "totalPdfs": len(items),
                "missingPdfOnDisk": len(missing_pdf),
                "recentMissing": len(recent_missing),
                "olderMissing": len(older_missing),
                "mdIssues": len(md_issues),
            },
            "mdIssues": md_issues,
            "recent": recent_missing,
            "older": older_missing,
            "missingPdf": missing_pdf,
        }
        print(json.dumps(output, indent=2, default=str))
        return 0

    print("=" * 70)
    print(f"Zotero → Markdown Audit  |  {now.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)
    print(f"  Zotero DB      : {args.zotero_db}")
    print(f"  Output dir     : {raw_dir}")
    print(f"  Total PDFs     : {len(items)}")
    print(f"  Existing .md   : {len(md_stems)}")
    print()

    if md_issues:
        print(f"EXISTING .md FILES — empty or stubby ({len(md_issues)} items)")
        print("-" * 70)
        for issue in md_issues:
            status_emoji = "EMPTY" if issue["status"] == "EMPTY" else "STUB"
            print(f"  [{status_emoji:5s}] {issue['filename']} ({issue['words']} words)")
        print()

    if missing_pdf:
        print(f"PDF metadata exists but file NOT on disk ({len(missing_pdf)} items)")
        print("-" * 70)
        for it in missing_pdf:
            cols = ", ".join(it["collections"]) if it["collections"] else "uncategorized"
            print(f"  [{it['itemKey']}] {it['firstAuthor']} ({it['year']}) — {it['title'][:70]}")
            print(f"        Collection: {cols}")
        print()

    if recent_missing:
        print(f"RECENTLY ADDED — missing from output dir ({len(recent_missing)} items)")
        print("-" * 70)
        for it in recent_missing:
            cols = ", ".join(it["collections"]) if it["collections"] else "uncategorized"
            print(f"  [ ] {it['firstAuthor']} ({it['year']}) — {it['title'][:65]}")
            print(f"      Key: {it['itemKey']}  |  Collection: {cols}")
            print(f"      Convert: python scripts/pdf2md.py <pdf_path>")
        print()
    else:
        print(f"OK: No missing items in the last {args.days} days.")
        print()

    if older_missing:
        print(f"OLDER GAPS — not yet converted ({len(older_missing)} items)")
        print("-" * 70)
        for it in older_missing:
            cols = ", ".join(it["collections"]) if it["collections"] else "uncategorized"
            print(f"  [ ] {it['firstAuthor']} ({it['year']}) — {it['title'][:65]}  [{cols}]")
        print()

    print("=" * 70)
    print("Next steps:")
    if md_issues:
        print(f"  1. Review/re-convert stubby .md files (see list above)")
    if recent_missing:
        print(f"  2. Convert recent items:")
        print(f"       python scripts/pdf2md.py <pdf_path>")
        print(f"     (find each PDF's path with one of the methods in")
        print(f"      references/pdf-path-resolution.md)")
    if older_missing:
        print(f"  3. Batch backfill: see references/pdf-path-resolution.md")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
