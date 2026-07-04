# Changelog

The current version lives in `SKILL.md` frontmatter (`version:` field).
This file holds the full version history — load it on demand, not every turn.

## v1.0.0

Initial release.

- `scripts/setup.py` — first-run config writer, `--check` re-entry mode.
- `scripts/_config.py` — shared config loader.
- `scripts/pdf2md.py` — pymupdf4llm-only PDF-to-Markdown converter, config-driven output_dir.
- `scripts/check_missing_raw.py` — four-section audit (stubs, recent gaps, older gaps, missing-PDF).
- `references/getting-started.md` — one-time setup narrative.
- `references/zot-cheatsheet.md` — `zot` command reference subset.
- `references/add-by-identifier.md` — DOI/arXiv/ISBN/PMID resolver docs.
- `references/configuration.md` — config file format and layout options.
- `references/pdf-path-resolution.md` — three approaches to find a PDF's local path.
