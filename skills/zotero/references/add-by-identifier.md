# Adding Papers by Identifier (DOI / arXiv / ISBN / PMID)

The Zotero GUI's "Add Item by Identifier" (magic wand) is **not** exposed via the CLI, the local HTTP API, or AppleScript. The translation engine that backs the magic wand lives inside Zotero's JavaScript runtime.

`zot add --doi` and `zot add --url` are stub creators — they create empty items with only the DOI/URL field filled in. Title, authors, abstract, year are all blank. **Do not use them.**

The terminal-equivalent of the magic wand is `zot-add-identifier`, which calls Zotero's actual JavaScript translator engine (via `zotero/translation-server` running locally on port 1969) to resolve the identifier, then creates the item via the web API with full metadata.

## Install (one-time)

The translation server requires Node.js. If you don't have it, install Node first (`brew install node` on macOS, or download from https://nodejs.org/).

The skill ships with a one-shot installer that does the full setup — clone the translation-server, run `npm install`, install the Python wrapper dependencies, copy both wrapper scripts to `~/.local/bin/`, and run a smoke test:

```bash
bash scripts/install_add_identifier.sh
```

The installer:
- verifies `node`, `npm`, `git`, `python3`, `pip` are present
- clones `zotero/translation-server` to `/tmp/translation-server` (idempotent)
- runs `npm install` in that dir
- copies `scripts/templates/zot-translation-server.sh` to `~/.local/bin/zot-translation-server`
- copies `scripts/templates/zot-add-identifier.py` to `~/.local/bin/zot-add-identifier` with a generic shebang (no `uv` venv dependency)
- runs `pip install --user pyzotero requests httpx`
- smoke-tests with `zot-add-identifier --dry-run 10.2307/4486062`

After the installer runs, `zot-translation-server` and `zot-add-identifier` are on PATH (assuming `~/.local/bin` is on PATH; if not, add it).

You'll also need a Zotero API key in `~/.config/zot/config.toml`:

```toml
library_id = "5263686"   # or your personal library ID
api_key = "your-api-key"
library_type = "user"     # or "group"
```

To get an API key: https://www.zotero.org/settings/keys.

## Commands

```bash
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

# Multiple identifiers at once
zot-add-identifier "10.2307/4486062" "arxiv:2202.11214"

# Dry run (preview without creating)
zot-add-identifier --dry-run "10.2307/4486062"

# JSON output
zot-add-identifier --json "10.2307/4486062"
```

## Supported identifier types

| Type | Example | Endpoint used |
|------|---------|---------------|
| DOI | `10.1023/A:1026553619983` | `/search` (Crossref / DataCite / CSL) |
| arXiv ID | `2306.03838` | `/web` (arXiv page scrape) |
| arXiv URL | `https://arxiv.org/abs/2306.03838` | `/web` |
| ISBN | `9780262035613` | `/search` |
| PMID | `12345678` | `/search` |

The translation server runs the **exact same JavaScript translator files** that Zotero desktop uses (`DOI Content Negotiation.js`, `arXiv.org.js`, `PubMed.js`, etc.). You get identical metadata to what the magic wand produces.

## Auto-sleep behavior

The translation server auto-starts on the first call and stays running (~80 MB). A watchdog stops it after 30 minutes of inactivity. The next call restarts it in ~2 seconds.

| State | RAM | CPU | Startup |
|-------|-----|-----|---------|
| Running | ~80 MB | 0% idle | — |
| Stopped | 0 MB | 0% | ~2.2 s |

Manual control:

```bash
zot-translation-server start
zot-translation-server status
zot-translation-server stop
```

## API-created items have no PDF

`zot-add-identifier` creates metadata-only items. It does not fetch or attach PDFs. The items exist with full bibliographic data, but no file attachments.

To get PDFs:

1. **Zotero desktop → right-click → "Find Available PDF"** (the magic wand for the item).
2. **Download manually and attach**:
   ```bash
   zot attach <KEY> --file /path/to/paper.pdf
   ```
3. **Zotero's built-in PDF retrieval** after syncing.

## Critical pitfall: always verify what was created

A "successful" `zot-add-identifier` call can resolve to the wrong paper if the DOI exists in Crossref but points to a different article. After every batch, verify:

```bash
zot --json read <KEY> | jq '{title, doi, date, creators: [.data.creators[] | "\(.first_name) \(last_name)"]}'
```

If the title and first author don't match what the user expects:

```bash
# Delete the wrong item
zot delete --yes <WRONG_KEY>

# Re-add with the corrected DOI
zot-add-identifier --json "CORRECT_DOI"
```

**Real example from practice:** the user provided DOI `10.1175/JAS-D-12-0128.1` (Heymsfield et al. 2013). `zot-add-identifier` succeeded, but `zot --json read` showed Cooper et al. "The Influence of Entrainment and Mixing..." — wrong paper. Deleted, searched Crossref for Heymsfield + JAS + 2013, found correct DOI `10.1175/jas-d-12-0124.1`, re-added.

## Troubleshooting

### "No items returned from any translator"

The identifier may be invalid, deactivated, or not indexed by the Zotero translator engine. The translation server queries the same resolvers as Zotero desktop (Crossref, DataCite, arXiv API, PubMed, etc.). If the upstream source does not have metadata for the identifier, resolution fails.

Fix:
1. Verify the DOI exists at `https://doi.org/<doi>` directly.
2. Check Crossref: `curl https://api.crossref.org/works/<doi>`
3. If the DOI is invalid, search for the paper by title/author and find the correct DOI before retrying.
4. For very old or obscure papers, the DOI may not be in Crossref/DataCite. Add the item manually via Zotero desktop or import a BibTeX/CSL file instead.

### Server failed to start

The Node.js translation server lives in `/tmp/translation-server`, which can be partially cleaned by macOS or system reboots. `npm install` artifacts or even `src/server.js` may be missing.

Fix:
```bash
rm -rf /tmp/translation-server
git clone --recurse-submodules https://github.com/zotero/translation-server.git /tmp/translation-server
cd /tmp/translation-server && npm install
```

### Quick health check

```bash
# 1. Check scripts exist
ls -la ~/.local/bin/zot-add-identifier ~/.local/bin/zot-translation-server

# 2. Check translation server source is intact
ls /tmp/translation-server/src/server.js /tmp/translation-server/package.json

# 3. Check Zotero API config exists
cat ~/.config/zot/config.toml | grep -E "library_id|api_key"

# 4. Test end-to-end with a known DOI
zot-add-identifier --dry-run "10.2307/4486062"

# 5. If dry-run passes, test a real creation
zot-add-identifier --json "10.2307/4486062"
```

## Upstream references

- Translation server: https://github.com/zotero/translation-server
- The `zotero-cli-cc` skill that this skill references: https://github.com/Agents365-ai/zotero-cli-cc
- DOI Content Negotiation spec: https://citation.crosscite.org/docs.html
