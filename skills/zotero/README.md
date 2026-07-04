# Zotero (skill for OpenCode-skill-creator)

Add papers to a local Zotero library by DOI/arXiv/ISBN/PMID, read existing items, resolve PDF attachment paths, convert PDFs to Markdown, and audit which papers still need conversion.

This is a strict subset of the user's full Zotero workflow — no wiki ingestion, no Obsidian Dataview, no knowledge graph. Just **add paper → convert PDF → MD**, plus an audit of what's still missing. The script converts the PDF body; YAML frontmatter is not generated (the user adds it manually from `zot --json read <KEY>` if needed).

## Install

Copy-paste this to your AI agent:

```
Install the zotero skill from https://github.com/JValdivia23/opencode-skill-creator by reading https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/docs/install-agent-zotero.md
```

The install doc lists all 18 files to download (SKILL.md, README.md, LICENSE.txt, .gitignore, 5 scripts, 1 install script, 2 wrapper templates, 6 references).

Or manually, in `~/.config/opencode/skills/zotero/`:

```bash
mkdir -p ~/.config/opencode/skills/zotero/{scripts/templates,references}
# Then download each file from:
# https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/<filename>
# where <filename> is each of the 18 files listed in docs/install-agent-zotero.md.
```

## What you get

- **`scripts/setup.py`** — first-run setup. Writes `~/.zotero-skill/config.toml` with your output directory. Re-runnable; `--check` flag for diagnostic re-entry.
- **`scripts/pdf2md.py`** — convert a local PDF to Markdown with `pymupdf4llm`. The script delegates OCR to pymupdf4llm, which auto-engages Tesseract when a page has no extractable text.
- **`scripts/stage.py`** — one-command staging: reads Zotero metadata (`zot --json read`), resolves the PDF, builds the YAML frontmatter, runs `pdf2md.py` for the body, and writes `Author_Year_Title.md` to the config's `output_dir`. Supports `--dry-run`, `--pdf`, `-o`, `--no-frontmatter`, `--force`, `--schema`, `--check`.
- **`scripts/check_missing_raw.py`** — audit which PDFs in your Zotero library don't have a Markdown counterpart. Four-section report.
- **`scripts/install_add_identifier.sh`** — opt-in installer for the "add by DOI/arXiv/ISBN/PMID" feature. Clones the translation-server, installs Python deps, copies wrapper scripts to `~/.local/bin/`. Only needed if you want to add papers by identifier from the terminal.
- **`scripts/templates/zot-translation-server.sh`**, **`scripts/templates/zot-add-identifier.py`** — source templates for the two wrapper scripts. The install script copies them to `~/.local/bin/` with chmod +x.
- **`references/getting-started.md`** — one-time setup narrative (load only on the first run, when the config file doesn't exist).
- **`references/zot-cheatsheet.md`** — the `zot` CLI command reference, focused on what this skill needs.
- **`references/add-by-identifier.md`** — the magic-wand equivalent for the terminal. DOI/arXiv/ISBN/PMID, batch mode, troubleshooting. (Requires `install_add_identifier.sh` first.)
- **`references/configuration.md`** — the config file format and how to re-run setup.
- **`references/pdf-path-resolution.md`** — three approaches to find a PDF's local path on disk.

## Dependencies

Required:
- `zot` CLI — `uv tool install zotero-cli-cc`
- `pymupdf4llm` — `pip install pymupdf4llm`
- Zotero desktop (with the local `zotero.sqlite` at the default path)
- Python 3.11+

Optional (only if you want to add papers by identifier):
- Run `scripts/install_add_identifier.sh` — handles Node.js, `git clone`, `npm install`, Python deps, and wrapper script installation in one command.

Optional (only if you have scanned PDFs):
- Tesseract OCR (already bundled via `pymupdf4llm`'s OCR backend, but the tesseract binary must be on PATH: `brew install tesseract` / `apt-get install tesseract-ocr`).

## Compatibility

Tested against the conventions used by:
- OpenCode 1.x
- Codex 0.x
- Claude Code 1.x
- Hermes (default Hermes Agent profile)
- Cursor 0.x

The skill is agent-agnostic: it does not depend on any agent-specific feature beyond reading `SKILL.md` and executing shell commands. The config file lives at `~/.zotero-skill/config.toml` (plain `~/`, not XDG `~/.config/`) for cross-agent compatibility.

## License

MIT. See `LICENSE.txt`. Copyright 2026 Jairo M. Valdivia-Prado (JValdivia23).

## Origin

This skill was extracted from a personal Zotero-wiki workflow that combines `zotero-cli` (the upstream CLI) and a private wiki with subagent-driven ingestion. The public version is the strict subset of that workflow: add paper, convert PDF, audit gaps. The wiki ingestion half is intentionally out of scope and lives in a separate project-local skill.

## Related

- Upstream `zot` CLI: https://github.com/Agents365-ai/zotero-cli-cc
- Zotero translation-server: https://github.com/zotero/translation-server
