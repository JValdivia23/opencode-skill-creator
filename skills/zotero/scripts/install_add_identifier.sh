#!/bin/bash
# install_add_identifier.sh — opt-in installer for the optional
# "add papers by DOI/arXiv/ISBN/PMID" feature.
#
# This script:
#   1. Verifies prerequisites (node, npm, git, python3, pip).
#   2. Clones zotero/translation-server to /tmp/translation-server
#      (idempotent — skipped if already present).
#   3. Runs `npm install` in the cloned dir.
#   4. Copies the two wrapper scripts from scripts/templates/ to
#      ~/.local/bin/ and chmod +x.
#   5. Runs `pip install --user pyzotero requests httpx` for the
#      Python wrapper.
#   6. Smoke-tests: zot-add-identifier --dry-run <known DOI>.
#
# Run from the skill root:  bash scripts/install_add_identifier.sh
# Or from anywhere:         bash <skill-dir>/scripts/install_add_identifier.sh

set -euo pipefail

# Locate the skill directory (parent of this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$SCRIPT_DIR/templates"

BIN_DIR="${HOME}/.local/bin"
SERVER_DIR="/tmp/translation-server"
SERVER_REPO="https://github.com/zotero/translation-server.git"

# Optional override of the bin dir (e.g. on a system where ~/.local/bin
# isn't on PATH and the user wants /usr/local/bin)
if [ -n "${ZOTERO_BIN_DIR:-}" ]; then
    BIN_DIR="$ZOTERO_BIN_DIR"
fi

say() { printf "  %s\n" "$*"; }
err() { printf "  ERROR: %s\n" "$*" >&2; }
ok()  { printf "  OK: %s\n" "$*"; }
hdr() { printf "\n=== %s ===\n" "$*"; }

hdr "zotero skill — install add-by-identifier feature"
echo "  Skill dir:    $SKILL_DIR"
echo "  Templates:    $TEMPLATES_DIR"
echo "  Bin dir:      $BIN_DIR"
echo "  Server dir:   $SERVER_DIR"

# 1. Prerequisites
hdr "1. Checking prerequisites"
missing=()

if ! command -v node >/dev/null 2>&1; then
    missing+=("node (https://nodejs.org/ — Node.js 18+ recommended)")
else
    ok "node: $(command -v node) ($(node --version 2>/dev/null || echo unknown))"
fi

if ! command -v npm >/dev/null 2>&1; then
    missing+=("npm (ships with node)")
else
    ok "npm: $(command -v npm) ($(npm --version 2>/dev/null || echo unknown))"
fi

if ! command -v git >/dev/null 2>&1; then
    missing+=("git")
else
    ok "git: $(command -v git)"
fi

if ! command -v python3 >/dev/null 2>&1; then
    missing+=("python3 (Python 3.11+ required)")
else
    ok "python3: $(command -v python3) ($(python3 --version 2>&1 || echo unknown))"
fi

if ! command -v pip3 >/dev/null 2>&1 && ! python3 -m pip --version >/dev/null 2>&1; then
    missing+=("pip3 (or `python3 -m pip` must work)")
else
    ok "pip: $(command -v pip3 || echo 'python3 -m pip')"
fi

if [ ${#missing[@]} -gt 0 ]; then
    err "Missing prerequisites:"
    for m in "${missing[@]}"; do
        err "  - $m"
    done
    exit 1
fi

# 2. Clone translation-server (idempotent)
hdr "2. Cloning zotero/translation-server"
if [ -d "$SERVER_DIR/.git" ]; then
    ok "$SERVER_DIR already exists, skipping clone"
elif [ -d "$SERVER_DIR" ] && [ -z "$(ls -A "$SERVER_DIR" 2>/dev/null)" ]; then
    # Empty dir exists (e.g. left over from a previous failed install) — remove it
    # so git clone can succeed.
    rmdir "$SERVER_DIR"
    say "Removed empty $SERVER_DIR, cloning fresh ..."
    if git clone --recurse-submodules "$SERVER_REPO" "$SERVER_DIR"; then
        ok "Cloned"
    else
        err "git clone failed. Check your network and try again."
        exit 1
    fi
elif [ -d "$SERVER_DIR" ]; then
    err "$SERVER_DIR exists but is not a git repo."
    err "Either delete it manually, or move it aside and re-run."
    exit 1
else
    say "Cloning to $SERVER_DIR ..."
    if git clone --recurse-submodules "$SERVER_REPO" "$SERVER_DIR"; then
        ok "Cloned"
    else
        err "git clone failed. Check your network and try again."
        exit 1
    fi
fi

# 3. npm install
hdr "3. Running npm install"
if [ -d "$SERVER_DIR/node_modules" ]; then
    ok "node_modules already present, skipping npm install"
else
    say "Running npm install in $SERVER_DIR ..."
    if (cd "$SERVER_DIR" && npm install); then
        ok "npm install complete"
    else
        err "npm install failed. See output above."
        exit 1
    fi
fi

# 4. Install wrapper scripts
hdr "4. Installing wrapper scripts to $BIN_DIR"
mkdir -p "$BIN_DIR"

if [ ! -f "$TEMPLATES_DIR/zot-translation-server.sh" ]; then
    err "Template missing: $TEMPLATES_DIR/zot-translation-server.sh"
    exit 1
fi
if [ ! -f "$TEMPLATES_DIR/zot-add-identifier.py" ]; then
    err "Template missing: $TEMPLATES_DIR/zot-add-identifier.py"
    exit 1
fi

cp "$TEMPLATES_DIR/zot-translation-server.sh" "$BIN_DIR/zot-translation-server"
chmod +x "$BIN_DIR/zot-translation-server"
ok "Installed: $BIN_DIR/zot-translation-server"

cp "$TEMPLATES_DIR/zot-add-identifier.py" "$BIN_DIR/zot-add-identifier"
chmod +x "$BIN_DIR/zot-add-identifier"
ok "Installed: $BIN_DIR/zot-add-identifier"

# 5. Python deps
hdr "5. Installing Python dependencies (pyzotero, requests, httpx)"
# Prefer `pip3` if available; fall back to `python3 -m pip`.
if command -v pip3 >/dev/null 2>&1; then
    pip_cmd=(pip3)
elif python3 -m pip --version >/dev/null 2>&1; then
    pip_cmd=(python3 -m pip)
else
    err "Neither pip3 nor python3 -m pip is available."
    exit 1
fi

# PEP 668 / externally-managed-environment: many modern system Pythons
# (Homebrew, Debian 12+, Fedora 38+) reject `--user` outright. On those
# systems `pip install` already installs to the user site by default.
# Only add `--user` if (a) we're not in a venv, AND (b) we can confirm pip
# actually accepts it (not just lists it in --help — Homebrew pip lists
# `--user` in help but rejects it as "no such option").
if [ -n "${VIRTUAL_ENV:-}" ]; then
    use_user=""
elif "${pip_cmd[@]}" install --user --dry-run pyzotero >/dev/null 2>&1; then
    use_user="--user"
else
    use_user=""
fi

say "Running: ${pip_cmd[*]} install --upgrade ${use_user} pyzotero requests httpx"
# Note: --user goes AFTER `install` (not as a global flag) because some
# pip versions (e.g. Homebrew pip 25.x) reject "pip3 --user install …"
# with "no such option: --user" but accept "pip3 install --user …".
if "${pip_cmd[@]}" install --upgrade ${use_user} pyzotero requests httpx; then
    ok "Python dependencies installed"
else
    err "pip install failed. See output above."
    err "If your system has an externally-managed Python (PEP 668),"
    err "create a venv first: python3 -m venv ~/.zotero-skill-venv,"
    err "activate it, then re-run this installer."
    exit 1
fi

# 6. Smoke test
hdr "6. Smoke test"
if ! command -v zot-add-identifier >/dev/null 2>&1; then
    err "zot-add-identifier is not on PATH."
    err "Add $BIN_DIR to PATH, or run it directly: $BIN_DIR/zot-add-identifier"
    exit 1
fi

if [ ! -f "$HOME/.config/zot/config.toml" ]; then
    err "~/.config/zot/config.toml not found."
    err "Run: zot config init"
    err "Then re-run this installer."
    exit 1
fi

say "Running: zot-add-identifier --dry-run 10.2307/4486062"
if zot-add-identifier --dry-run "10.2307/4486062"; then
    ok "Smoke test passed"
else
    err "Smoke test failed. Try running zot-translation-server start manually."
    exit 1
fi

hdr "Done"
echo "  zot-translation-server : $BIN_DIR/zot-translation-server"
echo "  zot-add-identifier      : $BIN_DIR/zot-add-identifier"
echo
echo "Usage:"
echo "  zot-translation-server start"
echo "  zot-add-identifier 10.1023/A:1026553619983"
echo "  zot-add-identifier arxiv:2306.03838"
echo "  zot-add-identifier --batch identifiers.txt"
echo
echo "The translation server auto-starts on the first call and stops after"
echo "30 minutes of inactivity. ~80 MB RAM while running."
