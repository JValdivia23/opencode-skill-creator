# Configuration

This skill reads its config from `~/.zotero-skill/config.toml` (TOML). The file is created by `python scripts/setup.py` and edited manually thereafter.

## Why `~/.zotero-skill/` and not `~/.config/zotero-skill/`?

XDG-style paths (`~/.config/<skill>/`) are the convention for OpenCode, Hermes, and Codex, but **not** for Claude Code or Cursor. Plain `~/` works in every agent without special handling. The plan is to keep this skill agent-agnostic, so the config lives in a path that every agent can read.

## File format

```toml
# Zotero skill config — written by scripts/setup.py
# Edit freely. Re-run `python scripts/setup.py` to reset.

# Where converted Markdown files are written.
# ~ expands to your home directory.
output_dir = "~/Documents/papers-md/"

# File layout. One of:
#   flat          -> output_dir/Author_Year_Title.md        (default)
#   by-year       -> output_dir/2024/Author_Year_Title.md
#   by-collection -> output_dir/<Zotero collection>/Author_Year_Title.md
layout = "flat"

# Optional: Zotero local database. Uncomment to override.
# zotero_db = "~/Zotero/zotero.sqlite"
# zotero_storage = "~/Zotero/storage"
```

## Fields

### `output_dir` (required)

The directory where `scripts/pdf2md.py` writes converted Markdown files. `~` is expanded. The directory is auto-created if it doesn't exist (the first time `pdf2md.py` runs).

To change it, edit the file directly and re-run `python scripts/setup.py --check` to verify the path is usable.

### `layout` (optional, default `flat`)

How files are organized inside `output_dir`:

- **`flat`** — `output_dir/Author_Year_Title.md`. The default. Every paper is one file at the top level.
- **`by-year`** — `output_dir/2024/Author_Year_Title.md`. Subfolders by publication year. Useful if you have a large library and want to browse by date.
- **`by-collection`** — `output_dir/<Zotero collection>/Author_Year_Title.md`. Subfolders by Zotero collection. Useful if you organize your library into topic collections.

**v1 limitation:** only `flat` is implemented in `scripts/pdf2md.py`. `by-year` and `by-collection` are documented here as future options; the script currently ignores the `layout` field and writes everything flat. The field is set by `scripts/setup.py` for forward compatibility — no current script reads it.

### `zotero_db` and `zotero_storage` (optional)

Override the auto-detected Zotero local database path. Defaults are:

- **macOS / Linux**: `~/Zotero/zotero.sqlite`, `~/Zotero/storage`
- **Windows**: `%USERPROFILE%\Zotero\zotero.sqlite`, `%USERPROFILE%\Zotero\storage`

If your Zotero data directory is elsewhere (e.g. on a different drive, or under `~/Documents/Zotero`), uncomment and set these.

## CLI overrides

Every command-line tool accepts a flag to override the config:

```bash
# pdf2md.py: explicit output path
python scripts/pdf2md.py paper.pdf -o ~/Desktop/paper.md

# check_missing_raw.py: override any of the paths
python scripts/check_missing_raw.py --zotero-db /Volumes/external/Zotero/zotero.sqlite
python scripts/check_missing_raw.py --zotero-storage /Volumes/external/Zotero/storage
python scripts/check_missing_raw.py --raw-dir /some/other/dir
```

CLI flags always win over the config. The config is a default, not a constraint.

## Re-running setup

To change the output path interactively:

```bash
python scripts/setup.py
```

`setup.py` will prompt to overwrite if the config already exists. If you want a clean slate, delete the config first:

```bash
rm ~/.zotero-skill/config.toml
python scripts/setup.py
```

## Validating the config

```bash
python scripts/setup.py --check
```

Exit 0 means the config is present, parses as valid TOML, and the `output_dir` is usable. Non-zero prints the specific failure.

## Scanned PDFs and OCR

If `scripts/pdf2md.py` produces suspiciously small output (< 50 lines), the source PDF is likely a scanned image without native text. The script delegates to `pymupdf4llm`, which auto-engages Tesseract OCR for pages with no extractable text — but the `tesseract` binary must be on PATH:

```bash
brew install tesseract       # macOS
apt-get install tesseract-ocr # Debian/Ubuntu
# Windows: download from https://github.com/UB-Mannheim/tesseract/wiki
```

If output is still poor (< 50 chars per page), the source PDF is likely a low-quality 1980s-era scan. The script can't help; you'll need specialized tools (Nougat, manual typing) or a better source PDF.

## Out of scope for v1: per-project overrides

A future version may add `.zotero-skill.toml` files in individual project directories that override the global config. For v1, the global config + per-command CLI flags are enough. To override for a specific conversion, pass `-o`. To override for a batch run, edit the global config or pass `--raw-dir` / `--zotero-db` flags.
