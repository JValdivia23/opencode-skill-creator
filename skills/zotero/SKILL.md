---
name: zotero
description: "Add papers to a local Zotero library by DOI/arXiv/ISBN/PMID, read existing items, resolve PDF attachment paths, convert PDFs to Markdown, and audit which PDFs still need conversion. Use when the user mentions Zotero, papers, references, citations, DOIs, arXiv, or wants to stage a research library into Markdown."
version: 1.0.1
---

# Zotero

Add papers to a local Zotero library, read existing items, resolve PDF attachment paths, convert PDFs to Markdown, and audit which PDFs still need conversion.

If `~/.zotero-skill/config.toml` does not exist, read `references/getting-started.md` first.

**First-time flow vs. every-turn flow:**

| Turn | Config file present? | What the agent reads |
|---|---|---|
| 1st ever | No | `SKILL.md` (for the one-line pointer) → `references/getting-started.md` |
| 1st ever, after setup | (just created) | `SKILL.md` body (Quick Start onwards) |
| 2nd+ | Yes | `SKILL.md` body only — `getting-started.md` is never loaded again |

The first turn is the only turn that loads two files. After that, one file per turn.

## What I Do

- **Add papers to Zotero by identifier** — DOI, arXiv ID/URL, ISBN, or PMID, with full metadata. Uses the native Zotero translator engine via `zot-add-identifier`, not bare `zot add --doi` (which creates empty stubs).
- **Read Zotero metadata** — search, read item details, list recent items, find duplicates, dump library stats. The `zot` CLI is the single source of truth.
- **Resolve a PDF's local path** — three approaches (SQLite, `zot open`, `find`) for the common case where the parent key differs from the storage key.
- **Convert PDFs to Markdown (staging)** — `pymupdf4llm` only, no GPU, no extra services. Follows the staging workflow: `zot --json read <KEY>` for metadata → `python scripts/pdf2md.py <pdf> -o <Author_Year_Title>.md` → prepend YAML frontmatter. Produces one `Author_Year_Title.md` per paper, matching the audit's expected naming.
- **Audit which Zotero PDFs are missing from your output dir** — four-section report (existing stubs, recent gaps, older gaps, missing-PDF-on-disk).

## When to Use Me

Use this skill when:

1. **The user mentions Zotero, papers, references, citations, DOIs, or arXiv** — any literature-management intent.
2. **The user wants to add a paper to their library by identifier** — DOI, arXiv, ISBN, PMID.
3. **The user wants to convert a paper they already have in Zotero to Markdown** — for Obsidian, a wiki, a notes folder, a project.
4. **The user wants to know which papers in their Zotero library don't have Markdown counterparts** — gap audit.
5. **The user mentions a `.bib` or `.ris` file** — usually means "I have citations somewhere and need them in Zotero / Markdown."

Do not use this skill when:

- The user wants to interact with Zotero *inside* a specific app's UI (browser connector, Zotero iOS app, etc.) — this is a CLI/agent skill, not a UI skill.
- The user wants to do wiki ingestion, Obsidian Dataview queries, knowledge-graph build, or any kind of structured-notes workflow — that's a different skill (`llm-wiki-agent` or similar) and is out of scope for v1 of this skill.
- The user wants to write a citation in a specific format (APA, Nature, Vancouver) — `zot cite KEY --style <name>` is the direct command; no skill needed.
- The user's library is empty or they don't have Zotero installed yet — point them to https://www.zotero.org/ and the deps in `references/getting-started.md` step 2.

## Quick Start

The first three commands a new user will run, in order. Assumes setup has already been completed.

```bash
# 1. Add a paper by DOI (full metadata, not a stub)
zot-add-identifier "10.1023/A:1026553619983"

# 2. Stage it to Markdown: metadata -> convert -> prepend frontmatter
zot --json read <KEY>                                                # metadata + PDF path
python scripts/pdf2md.py <pdf_path> -o "<AuthorLastName>_<Year>_<TitleSlug>.md"
# then prepend YAML frontmatter (see "Converting a PDF to Markdown")

# 3. Audit what's still missing
python scripts/check_missing_raw.py
```

The output directory is read from `~/.zotero-skill/config.toml` (set up via `references/getting-started.md` or `python scripts/setup.py`). The path is configurable — see `references/configuration.md`.

## Adding Papers to Zotero

The magic wand (`Add Item by Identifier` in Zotero's GUI) is **not** exposed via the CLI, the local HTTP API, or AppleScript. The translation engine that backs the magic wand lives inside Zotero's JavaScript runtime and is reachable only through that runtime.

`zot add --doi` and `zot add --url` are stub creators — they do not resolve metadata. They create empty items with only the DOI/URL field filled in. The title, authors, abstract, year, etc. are all blank. **Do not use them for production work.**

The terminal-equivalent of the magic wand is `zot-add-identifier`, which calls Zotero's actual JavaScript translator engine (via `zotero/translation-server` running locally on port 1969) to resolve the identifier, then creates the item via the web API with full metadata.

```bash
# Install once (one-time, in addition to the `zot` CLI)
git clone --recurse-submodules https://github.com/zotero/translation-server.git /tmp/translation-server
cd /tmp/translation-server && npm install
# Scripts are already at ~/.local/bin/zot-add-identifier and zot-translation-server

# Add by DOI
zot-add-identifier "10.1023/A:1026553619983"

# Add by arXiv ID or URL
zot-add-identifier "arxiv:2306.03838"
zot-add-identifier "https://arxiv.org/abs/2306.03838"

# Add by ISBN or PMID
zot-add-identifier --isbn "9780262035613"
zot-add-identifier --pmid "12345678"

# Batch (one identifier per line in a file)
zot-add-identifier --batch identifiers.txt

# Dry run (preview without creating)
zot-add-identifier --dry-run "10.2307/4486062"

# JSON output
zot-add-identifier --json "10.2307/4486062"
```

`zot-add-identifier` and `zot-translation-server` are not bundled with the skill — they are user-installed via `scripts/install_add_identifier.sh` (see `references/add-by-identifier.md`). The skill ships the templates and the installer; running it places the wrappers in `~/.local/bin/`.

Once installed, the translation server auto-starts on the first call and stays running (~80 MB). A watchdog stops it after 30 minutes of inactivity. The next call restarts it in ~2 seconds.

**Always verify what `zot-add-identifier` actually created.** A "successful" call can resolve to the wrong paper if the DOI exists in Crossref but points to a different article. After every batch, run:

```bash
zot --json read <KEY> | jq '{title, doi, date, creators: [.data.creators[] | "\(.first_name) \(last_name)"]}'
```

If the title and first author don't match what the user expects, delete the wrong item (`zot delete --yes <KEY>`) and re-add with the corrected DOI. See `references/add-by-identifier.md` for the full guide, including the `arxiv2md` backend, troubleshooting, and the resource footprint table.

## Reading Zotero Metadata

`zot` is the single CLI for everything. **Always use `--json` when processing results programmatically** — the output is a structured envelope `{data: [...], meta: {...}, ok: true}` and `jq` can target `.data` directly.

### Quick routing

| User intent | Command |
|---|---|
| Search by title/author/tag | `zot --json search "transformer"` |
| Read/view a paper | `zot --json read <KEY>` |
| Export citation (BibTeX) | `zot export <KEY>` |
| Formatted citation to clipboard | `zot cite <KEY> --style apa` |
| Find duplicates | `zot --json duplicates` |
| Recently added items | `zot --json recent --days 7` |
| Find unfiled items | `zot --json recent --days 7 \| jq '.data \| map(select((.collections \| length) == 0))'` |
| PDF full text | `zot --json pdf <KEY>` |
| Library stats | `zot --json stats` |
| Open PDF in system viewer | `zot open <KEY>` |
| Group library (group:12345) | `zot --library group:12345 search "query"` |

### Search quirks — read these

1. **Multi-word keyword search is unreliable.** `zot search "Ryzhkov beam broadening"` may return zero results even when the paper is in the library, because all keywords must match simultaneously across fields. Use shorter queries — author-only or single significant keyword.

2. **DOI search is the most reliable membership test.** When verifying whether a specific paper is in the library, search by the exact raw DOI:
   ```bash
   # Reliable — finds the paper even when keyword search fails
   zot search "10.1175/JTECH2003.1"
   # Unreliable — may miss the paper
   zot search "Ryzhkov beam broadening"
   ```

3. **Do NOT prefix with `doi:`.** `zot search "doi:10.1175/..."` returns no results even when the paper is in the library. Use the raw DOI string.

4. **A `zot search` miss is NOT proof of absence.** Because keyword search can miss items, always confirm a negative result with a raw DOI search before concluding a paper isn't in Zotero.

5. **`zot search` does not do full-text search.** It matches against metadata fields. For PDF content search, use the workspace RAG feature (out of scope for v1 of this skill).

For the full `zot` reference (all commands, all flags, group libraries, workspaces, configuration), see the upstream `zotero-cli` skill — `references/zot-cheatsheet.md` has the most-commonly-used subset.

## Resolving a PDF's Local Path

A Zotero item has a *parent key* (the paper's metadata) and an *attachment key* (the PDF in storage). **They are different.** The actual PDF path is:

```
~/Zotero/storage/<attachment_key>/<filename>
```

Three approaches to find the attachment key, in order of preference:

### Approach A — SQLite query (fastest, requires the DB to be unlocked)

```bash
sqlite3 "file:/Users/$USER/Zotero/zotero.sqlite?mode=ro&immutable=1" \
  "SELECT parent.key, child.key, ia.path
   FROM items parent
   JOIN itemAttachments ia ON parent.itemID = ia.parentItemID
   JOIN items child ON child.itemID = ia.itemID
   WHERE parent.key = '<PARENT_KEY>';"
```

Returns rows like `PARENT_KEY|ATTACH_KEY|storage:Filename.pdf`. The PDF path is `~/Zotero/storage/ATTACH_KEY/Filename.pdf`.

### Approach B — `zot open <KEY>` (Zotero-desktop-friendly)

```bash
zot open XRVJ9QGR
# Output: Opening /Users/.../Zotero/storage/XXRJSPRK/Paper title.pdf
```

`zot open` prints the filesystem path to stderr **and** opens the file in the system PDF viewer. It works while Zotero desktop is running and has the SQLite database locked. Use it for one-off path discovery. For batch jobs (3+ papers), the system-viewer windows stack up — prefer the SQLite approach for batches.

### Approach C — `find` (nuclear fallback)

```bash
find ~/Zotero/storage -name "*.pdf" | grep -i "author.*year"
```

Reliable when you know the author/year/title keywords but don't have a key. The storage folder names are attachment keys, and PDF filenames contain the paper metadata.

For the full guide — including the Zotero-desktop-locking workaround, what to do when `sqlite3` reports `database is locked`, and the parent-vs-attachment key explanation in source — see `references/pdf-path-resolution.md`.

## Converting a PDF to Markdown

Conversion follows the **staging workflow**: resolve metadata from Zotero, convert the PDF body, then prepend structured YAML frontmatter. The result is one `Author_Year_Title.md` file in your output_dir, ready for Obsidian or a wiki ingest.

### Staging steps (one paper)

```bash
# 1. Metadata + resolve the PDF path for a Zotero item
zot --json read <KEY>

# 2. Convert the PDF body, writing to the canonical Author_Year_Title name
python scripts/pdf2md.py <pdf_path> -o "<AuthorLastName>_<Year>_<TitleSlug>.md"

# 3. Prepend YAML frontmatter (built from the zot --json read output) to the .md
```

`pdf2md.py` is a pure converter (pymupdf4llm); it does not query Zotero and does not emit frontmatter. The agent constructs the canonical filename and the frontmatter from `zot --json read <KEY>`, exactly as the project-local zotero staging workflow does. The `-o` path may be a bare stem — `pdf2md.py` writes it into the config's `output_dir`.

### Canonical filename

`<AuthorLastName>_<Year>_<TitleSlug>.md`, where:

- `AuthorLastName` — first author's last name with non-word chars stripped (`Valdivia-Prado` → `ValdiviaPrado`).
- `Year` — 4-digit publication year.
- `TitleSlug` — first 12 title words joined by `_`, punctuation stripped, original case preserved.

This is the same algorithm `scripts/check_missing_raw.py` uses to compute `expectedStem`, so a correctly-staged file is always recognized as converted. The audit matches on the `Author_Year` prefix, so minor title-slug variation is tolerated (existing legacy files use slightly different title slugs and still match). A non-standard filename (e.g. kebab-case from a bare `pdf2md.py <pdf>` call) is flagged as missing — that's the standardization enforcer working as intended; re-stage the paper with the canonical name.

### Frontmatter schema

Prepend this YAML block, sourcing each field from `zot --json read <KEY>`:

```yaml
---
title: "<data.title>"
authors:                            # one entry per creator
  - "<firstName lastName>"
year: "<data.date, first 4 chars>"
doi: "<data.doi>"
abstract: "<data.abstractNote>"
tags: []                            # from data.tags
collections:                        # from data.collections
  - "<collection key>"
item_key: "<data.key>"
item_type: "<data.itemType>"
source_url: "<data.url>"
date: "<data.date>"
date_added: "<data.dateAdded>"
date_modified: "<data.dateModified>"
pdf_path: "<resolved local PDF path>"
---
```

Omit any field the Zotero item doesn't have. Resolve `pdf_path` via `references/pdf-path-resolution.md`.

For scanned PDFs without native text, `pymupdf4llm` (the library `pdf2md.py` wraps) auto-engages Tesseract OCR. The tesseract binary must be on PATH (`brew install tesseract` / `apt-get install tesseract-ocr`). If output is suspiciously small (< 50 lines), it's likely a low-quality scan — see `references/configuration.md` for OCR troubleshooting.

## Auditing a Raw Directory

```bash
# Default: audits the config's output_dir against your Zotero library
python scripts/check_missing_raw.py

# Limit to recent items
python scripts/check_missing_raw.py --days 3

# Machine-readable
python scripts/check_missing_raw.py --json

# Stricter stub detection
python scripts/check_missing_raw.py --stub-threshold 100

# Audit a different directory
python scripts/check_missing_raw.py --raw-dir /some/other/dir
```

Four-section report:

1. **Existing .md files that are empty or stubby** — content below the word threshold after stripping frontmatter. Old screenshots and rate-limit-damaged files end up here.
2. **Recently added (default last 7 days) — your immediate action items.** Zotero items in the date window whose PDF isn't yet a .md in the output_dir.
3. **Older gaps — backlog.** Same as #2 but outside the recent window.
4. **Items missing local PDF files — metadata exists but file not on disk.** The attachment is referenced in the SQLite but the file isn't at `~/Zotero/storage/<key>/...`. Usually a sync issue or a manual deletion.

`--json` output includes the full structured report. Useful for scripting: pipe into `jq` to filter, e.g. `... | jq '.recent | map({key, title, firstAuthor, expectedStem})'`.

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| `zot add --doi` creates stubs | Item has DOI but no title, authors, abstract | Use `zot-add-identifier` instead |
| Wrong Python interpreter | `No module named pymupdf4llm` | Use `python` (where pymupdf4llm is installed), not `python3` |
| Attachment key ≠ parent key | `file not found` at `storage/<parent_key>/` | Use the SQLite query in `references/pdf-path-resolution.md` |
| `database is locked` from sqlite3 | Zotero desktop is running | Close Zotero, or use `zot open <KEY>` instead |
| Scanned PDF | Output is < 50 lines | `pymupdf4llm` auto-engages Tesseract OCR; install tesseract on PATH |
| `search` returns 0 results | Multi-word query too strict | Search by DOI (raw string, no `doi:` prefix) or single keyword |
| API-created items have no PDF | Item exists but no attachment | Open Zotero desktop → right-click → "Find Available PDF", or download manually and `zot attach <KEY> --file paper.pdf` |
| Output dir is wrong | `.md` file lands somewhere unexpected | `cat ~/.zotero-skill/config.toml` to verify; re-run `python scripts/setup.py` to fix |
| `~/.zotero-skill/config.toml` not found | `Error: config not found. Run setup.py first.` | `python scripts/setup.py` |

## References

- **`references/getting-started.md`** — one-time setup: dependencies, install, first-run flow, mandatory smoke test. Load this only when the config file doesn't exist.
- **`references/zot-cheatsheet.md`** — the full `zot` command reference, including group libraries, workspaces, and the deduplication workflow.
- **`references/add-by-identifier.md`** — the magic-wand equivalent for the terminal. DOI/arXiv/ISBN/PMID, batch mode, the translation-server lifecycle, troubleshooting.
- **`references/configuration.md`** — the `~/.zotero-skill/config.toml` format, layout options (`flat` / `by-year` / `by-collection`), how to re-run setup, why `~/.zotero-skill/` not `~/.config/zotero-skill/`.
- **`references/pdf-path-resolution.md`** — the three approaches in full: SQLite (with the `database is locked` workaround), `zot open`, and `find`.
- **`references/changelog.md`** — version history (loaded on demand, not every turn).

For the upstream `zot` CLI source: https://github.com/Agents365-ai/zotero-cli-cc (the `zot` binary lives there; this skill is the workflow, not the CLI).

For the translation-server that powers `zot-add-identifier`: https://github.com/zotero/translation-server.
