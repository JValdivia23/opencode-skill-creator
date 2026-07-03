# `zot` Cheatsheet

The `zot` CLI is the single source of truth for reading Zotero data. This is a subset of its full command set — the commands you'll reach for in this skill. For the upstream reference, see https://github.com/Agents365-ai/zotero-cli-cc.

**Always use `--json` when processing results programmatically.** Output is a structured envelope: `{data: [...], meta: {...}, ok: true}`. Target `.data` when piping to `jq`.

## Search & Browse

```bash
zot --json search "transformer attention"
zot --json search "BERT" --collection "NLP"
zot --json list --collection "Machine Learning" --limit 10
zot --json read ITEMKEY
zot --json relate ITEMKEY
```

## Notes & Tags

```bash
zot --json note ITEMKEY
zot note ITEMKEY --add "Key finding: ..."
zot --json tag ITEMKEY
zot tag ITEMKEY --add "important"
zot tag ITEMKEY --remove "to-read"
```

## Citation Export

```bash
zot export ITEMKEY                    # BibTeX
zot export ITEMKEY --format csl-json  # CSL-JSON
zot export ITEMKEY --format ris       # RIS
zot export ITEMKEY --format json      # Raw JSON

# Formatted citation (copies to clipboard)
zot cite ITEMKEY                      # APA (default)
zot cite ITEMKEY --style nature       # Nature
zot cite ITEMKEY --style vancouver    # Vancouver
```

## Item Management (Write Ops)

```bash
# PREFER zot-add-identifier for these — see references/add-by-identifier.md
# zot add --doi "..."  creates a bare stub. Avoid.
zot add --pdf paper.pdf                   # Add from local PDF (auto-extract DOI)
zot --no-interaction delete ITEMKEY
zot update ITEMKEY --title "New Title"
zot update ITEMKEY --field volume=42 --field pages=1-10
zot attach ITEMKEY --file supplement.pdf
```

## Collections

```bash
zot --json collection list
zot --json collection items COLLECTIONKEY
zot collection create "New Project"
zot collection move ITEMKEY COLLECTIONKEY
zot collection rename COLLECTIONKEY "New Name"
zot collection delete COLLECTIONKEY
```

## Duplicates, Recent & Trash

```bash
zot --json duplicates                # Find duplicates (DOI + title matching)
zot --json duplicates --by title     # Title-only matching
zot --json recent --days 7           # Recently added items
zot --json recent --sort dateModified
zot --json trash list                # View trashed items
zot trash restore ITEMKEY            # Restore from trash
```

## PDF & Summarization

```bash
zot --json pdf ITEMKEY
zot pdf ITEMKEY --pages 1-5
zot pdf ITEMKEY --annotations        # Extract PDF annotations
zot --json summarize ITEMKEY
zot summarize-all
```

## Utilities

```bash
zot --json stats                     # Library statistics
zot open ITEMKEY                     # Open PDF in system viewer (also prints path)
```

## Group Library

```bash
zot --library group:12345 search "query"    # Search in group library
zot --library group:12345 list              # List group library items
```

## Global Flags

| Flag | Purpose |
|------|---------|
| `--json` | JSON output (ALWAYS use for programmatic processing) |
| `--limit N` | Limit results (default: 50) |
| `--detail minimal` | Only key/title/authors/year — saves tokens |
| `--detail full` | Include extra fields |
| `--no-interaction` | Suppress prompts (for automation) |
| `--profile NAME` | Use a specific config profile |
| `--verbose` | Verbose/debug output |

## Search quirks — read these

1. **Multi-word keyword search is unreliable.** `zot search "Ryzhkov beam broadening"` may return zero results even when the paper is in the library. Use shorter queries — author-only or single significant keyword.

2. **DOI search is the most reliable membership test.** When verifying whether a specific paper is in the library, search by the exact raw DOI:
   ```bash
   # Reliable
   zot search "10.1175/JTECH2003.1"
   # Unreliable
   zot search "Ryzhkov beam broadening"
   ```

3. **Do NOT prefix with `doi:`.** `zot search "doi:10.1175/..."` returns no results.

4. **A `zot search` miss is NOT proof of absence.** Always confirm a negative result with a raw DOI search.

5. **`zot search` does not do full-text search.** It matches metadata only. For PDF content, use `zot --json pdf <KEY>` to extract the full text, or build a workspace index (out of scope for v1 of this skill).
