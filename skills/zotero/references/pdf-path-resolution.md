# Resolving a PDF's Local Path

A Zotero item has a *parent key* (the paper's metadata) and an *attachment key* (the PDF in storage). **They are different.** The actual PDF path is:

```
~/Zotero/storage/<attachment_key>/<filename>
```

The three approaches below, in order of preference.

## Approach A — SQLite query (fastest)

Requires the SQLite database to be unlocked. If Zotero desktop is running, the DB is locked — use Approach B in that case.

```bash
sqlite3 "file:/Users/$USER/Zotero/zotero.sqlite?mode=ro&immutable=1" \
  "SELECT parent.key, child.key, ia.path
   FROM items parent
   JOIN itemAttachments ia ON parent.itemID = ia.parentItemID
   JOIN items child ON child.itemID = ia.itemID
   WHERE parent.key = '<PARENT_KEY>';"
```

Returns rows like:

```
73KR57YH|WFVI5V3R|storage:Zhang et al. - 2016 - ... .pdf
```

The columns are: `parent_key | attachment_key | storage_path`. The actual PDF path is:

```
~/Zotero/storage/WFVI5V3R/Zhang et al. - 2016 - ... .pdf
```

### For multiple items at once

```bash
KEYS="('KEY1', 'KEY2', 'KEY3')"
sqlite3 "file:/Users/$USER/Zotero/zotero.sqlite?mode=ro&immutable=1" \
  "SELECT parent.key, child.key, ia.path
   FROM items parent
   JOIN itemAttachments ia ON parent.itemID = ia.parentItemID
   JOIN items child ON child.itemID = ia.itemID
   WHERE parent.key IN $KEYS;"
```

### `database is locked` — what to do

If `sqlite3` reports `database is locked`, Zotero desktop has the file open exclusively. Three workarounds:

1. **Close Zotero desktop temporarily** and re-run the query. The DB is unlocked when the app is closed.
2. **Use Approach B (`zot open`)** — it works while Zotero is running.
3. **Make a temporary copy** of the database (read-only snapshot, won't conflict with the running app):
   ```bash
   cp ~/Zotero/zotero.sqlite /tmp/zotero-snapshot.sqlite
   sqlite3 "file:/tmp/zotero-snapshot.sqlite?mode=ro" "SELECT ..."
   ```

The first two are the cleanest. The snapshot is a last resort.

## Approach B — `zot open <KEY>` (Zotero-desktop-friendly)

```bash
zot open XRVJ9QGR
```

Output goes to stderr (and the file opens in the system viewer):

```
Opening /Users/.../Zotero/storage/XXRJSPRK/Paper title.pdf
```

`zot open` reads the DB through the CLI's own read path, which **does not** require direct SQLite access. It works while Zotero desktop is running.

**Trade-off:** the system-viewer window opens. For a single paper, fine. For a batch of 10+ items, you'll have 10+ viewer windows stacking up. Switch to Approach A for batches.

## Approach C — `find` (nuclear fallback)

When you don't have a key, only the author/year/title:

```bash
find ~/Zotero/storage -name "*.pdf" | grep -i "author.*year"
```

The storage folder names are attachment keys. PDF filenames contain the paper metadata (author, year, title slug). Grep for what you know.

This works reliably when:
- You know the author or year but don't have a Zotero key.
- The SQLite database is unavailable (corrupted, missing, on an unmounted drive).
- You're working from a manual list of references.

## Quick decision tree

```
Do you have the Zotero item key?
├── Yes, and Zotero desktop is closed   → Approach A (SQLite)
├── Yes, and Zotero desktop is running   → Approach B (zot open)
├── No, only author/year/title          → Approach C (find)
└── No, and SQLite is unavailable       → Approach C (find)
```

## Verifying the file exists

The attachment record in the database does **not** guarantee the file is on disk. Always verify before passing the path to `scripts/pdf2md.py`:

```bash
test -f "/path/to/paper.pdf" && echo "OK" || echo "MISSING"
```

If `MISSING`, the paper is metadata-only — the PDF was never downloaded, or was deleted, or lives on an unmounted drive. To get the PDF, open Zotero desktop → right-click the item → "Find Available PDF", or download manually and `zot attach <KEY> --file paper.pdf`.

## Common failures and fixes

| Failure | Cause | Fix |
|---|---|---|
| `sqlite3: database is locked` | Zotero desktop has the file open | Use Approach B (zot open) |
| `Error: no such table: items` | Wrong SQLite path | Check `ls ~/Zotero/zotero.sqlite`; override with `--zotero-db` if needed |
| `Error: no rows returned` | Parent key has no PDF attachment, or key is wrong | `zot --json read <KEY>` to verify the item; check for `data.children` with `item_type == "attachment"` |
| `file not found: <path>` | Parent key ≠ storage key (most common) | Re-run Approach A; the third column (`ia.path`) is the filename, the second column (`child.key`) is the storage folder name |
| Path works but `pdf2md.py` produces 0 lines | PDF is image-only (scanned) | `pymupdf4llm` auto-engages Tesseract OCR; install tesseract on PATH |
