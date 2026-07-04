# Changelog

The current version lives in `SKILL.md` frontmatter (`version:` field).
This file holds the full version history — load it on demand, not every turn.

## v1.0.1

- Standardize md creation on the `Author_Year_Title` + YAML-frontmatter staging convention, matching the project-local zotero staging workflow. `SKILL.md` conversion section now mirrors staging: `zot --json read <KEY>` → `pdf2md.py -o <Author_Year_Title>.md` → prepend frontmatter (title, authors, year, doi, abstract, tags, collections, item_key, item_type, source_url, date, date_added, date_modified, pdf_path).
- `scripts/pdf2md.py` and `scripts/check_missing_raw.py` unchanged. The audit's strict `Author_Year` prefix match now enforces the standard: a non-standard filename (e.g. kebab-case from a bare `pdf2md.py <pdf>` call) is flagged as missing, prompting re-staging.

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
