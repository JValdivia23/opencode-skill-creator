# Getting Started — Zotero Skill

This file is loaded **only on the first invocation of the skill, and only when `~/.zotero-skill/config.toml` does not yet exist.** After setup, the agent reads `SKILL.md` alone.

If you are reading this and you have not yet run setup, run:

```bash
python scripts/setup.py
```

If the config file already exists, this file is irrelevant to you — go read `SKILL.md` instead.

---

## 1. What this skill does

Adds papers to your local Zotero library by identifier (DOI, arXiv, ISBN, PMID), reads existing items, resolves PDF attachment paths, converts PDFs to Markdown in a directory you choose, and audits which papers in your Zotero library don't yet have Markdown counterparts. **No wiki, no Obsidian ingestion, no graph build** — just the add-paper → convert-PDF → MD pipeline.

## 2. Dependencies

### Required

- **`zot` CLI** — the Zotero command-line tool. Install:
  ```bash
  uv tool install zotero-cli-cc
  ```
  Test: `zot --version`

- **`pymupdf4llm`** — the PDF-to-Markdown library. Install:
  ```bash
  pip install pymupdf4llm
  ```
  Test: `python -c "import pymupdf4llm"`

- **Zotero desktop app**, with the local `zotero.sqlite` at `~/Zotero/zotero.sqlite` on macOS and Linux, `%USERPROFILE%\Zotero\zotero.sqlite` on Windows. If yours is elsewhere, pass `--zotero-db` and `--zotero-storage` to `scripts/check_missing_raw.py`.

- **Python 3.11+** (uses `tomllib` from stdlib). For Python 3.10, install `tomli` and change the `import tomllib` line in `scripts/_config.py` to `import tomli as tomllib`.

### Optional — only if you want to add papers by identifier

- **`zot-add-identifier`** + **`zot-translation-server`** (Node.js + Python wrapper). The translation server runs the actual Zotero JavaScript translator engine (the same one the magic wand uses in the GUI). Install:
  ```bash
  git clone --recurse-submodules https://github.com/zotero/translation-server.git /tmp/translation-server
  cd /tmp/translation-server && npm install
  # scripts are at ~/.local/bin/zot-add-identifier and zot-translation-server
  ```
  Test: `zot-add-identifier --dry-run "10.2307/4486062"`

  See `references/add-by-identifier.md` for the full guide, including the auto-sleep watchdog behavior and the resource footprint.

### Optional — only if you have scanned PDFs

- **Tesseract OCR.** Install via your package manager:
  ```bash
  brew install tesseract       # macOS
  apt-get install tesseract-ocr # Debian/Ubuntu
  ```
  Test: `tesseract --version`

  The `scripts/pdf2md.py` script delegates to `pymupdf4llm`, which auto-engages Tesseract for pages with no extractable text. If tesseract is not on PATH, those pages will be empty in the output.

## 3. Where will your Markdown files live?

This is the **only** question the agent asks the new user. Pick one of these patterns, or type a custom path:

| Choice | Path | When to pick this |
|---|---|---|
| `1` | `~/Documents/papers-md/` | Simplest. One flat folder, no Obsidian integration. |
| `2` | `~/Documents/ObsidianVault/papers/` | You're using Obsidian and want the .md files to show up automatically. |
| `3` | `<current-project>/<project-name>-papers-md/` | Project-local. The Markdown files live next to your project. |
| `4` | (you type a path) | Any other location. |

`setup.py` writes `~/.zotero-skill/config.toml` with your choice. You can re-run `setup.py` at any time to change it.

## 4. (No second question in v1.)

The skill defaults to `flat` layout — one folder, `Author_Year_Title.md`. The other two options (`by-year` and `by-collection`) live in `references/configuration.md` for users who want to switch later.

## 5. The smoke test (mandatory)

Setup is **not** done until the user has converted one real PDF from their own Zotero library and seen the .md file in the output directory. The agent walks through this with you. No fixtures, no toy data.

1. `zot --json recent --days 7` — pick the first result you recognize.
2. `zot --json read <KEY>` — confirm it's a real paper.
3. Resolve the PDF's local path (one of the three approaches in `references/pdf-path-resolution.md`).
4. `python scripts/pdf2md.py <pdf_path>` — no `-o`, so it writes to your config's `output_dir`.
5. `ls <output_dir>` — confirm the `.md` file exists and is more than 100 lines.

If step 5 fails, the agent does NOT declare setup complete. The diagnostics:

- **No file at all**:
  - Check the path from step 3 — did `pdf2md.py` print "✓ Wrote" or an error? If "Error: PDF not found", re-check the path. If a different error, see `references/pdf-path-resolution.md` and `references/configuration.md`.
  - Check that the script's resolved `output_dir` matches what you expect: `cat ~/.zotero-skill/config.toml`.
  - If the error was "attachment not found" or similar, the parent key differs from the storage key — see `references/pdf-path-resolution.md` SQLite approach. This is the most common real-world failure.
- **File exists but is empty / < 100 lines**:
  - Likely a scanned PDF. Install Tesseract (see step 2 above).
- **Zotero desktop was just restarted and the SQLite DB is locked**:
  - Symptom: `pdf2md.py` errors with "database is locked" or the SQLite query in `references/pdf-path-resolution.md` fails.
  - Fix: close Zotero desktop temporarily, or use the `zot open <KEY>` path-discovery approach instead of SQLite.
- **`python: command not found` or `No module named pymupdf4llm`**:
  - Re-run `setup.py --check` for a diagnostic report.

When step 5 succeeds, the agent says: *"You're set up. From now on, just say 'convert this paper' or 'audit my Zotero' and I'll handle it."*

## 6. Re-running setup

To change the output path or reset the config:

```bash
# Erases the config. Re-run setup to write a new one.
rm ~/.zotero-skill/config.toml
python scripts/setup.py
```

`setup.py` will prompt to overwrite an existing config if you don't delete it first.

## 7. Verify the toolchain is still healthy

```bash
python scripts/setup.py --check
```

Exit 0 means the config is present, the output_dir is usable, and all required dependencies are installed. Non-zero prints the specific failure and points at the right `references/*.md`.
