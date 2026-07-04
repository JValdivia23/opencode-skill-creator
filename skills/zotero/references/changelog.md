# Changelog

The current version lives in `SKILL.md` frontmatter (`version:` field).
This file holds the full version history — load it on demand, not every turn.

## v1.0.3

- Fix `scripts/stage.py` YAML round-trip validation: `yaml.safe_load` received the full `---`-wrapped frontmatter block and raised `ComposerError: expected a single document in the stream` (the trailing `---` started a second, empty document). Now strips the `---` markers before parsing. The bug only fired on real staging (`--force`), not `--dry-run` (which skips validation). `cmd_check` was already correct (it regex-extracts the inner content).

## v1.0.2

- Add `scripts/stage.py` — one-command staging tool that wraps the v1.0.1 3-step workflow: `zot --json read <KEY>` → resolve PDF via SQLite → build 14-field YAML frontmatter → run `pdf2md.py` for the body → write `Author_Year_Title.md` to `output_dir`. Supports `--dry-run`, `--pdf <path>`, `-o <path>`, `--no-frontmatter`, `--force`, `--schema`, `--check <file>`. Optional PyYAML for frontmatter round-trip validation (skipped with a warning if absent).
- Extract the canonical `Author_Year_Title` slugger into `scripts/_config.py` (`_slugify_canonical`), shared by `stage.py` and `check_missing_raw.py` (now a thin delegate) so the writer and the audit cannot drift apart.
- Fix the v1.0.1 frontmatter schema field names in `SKILL.md` to match the actual `zot --json read` JSON (`abstract` not `abstractNote`, `item_type` not `itemType`, `date_added`/`date_modified` not `dateAdded`/`dateModified`; creators use `first_name`/`last_name`).
- `pdf2md.py` unchanged (pure converter); `check_missing_raw.py` behavior unchanged (strict `Author_Year` prefix match still enforces the standard).

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
