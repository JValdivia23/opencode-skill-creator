#!/usr/bin/env bash
set -euo pipefail

python3 ./scripts/install-skill-from-github.py \
  --url "https://github.com/anthropics/skills/tree/main/skills/pdf" \
  --scope local \
  --dry-run

echo "test_install_dry_run.sh: OK"
