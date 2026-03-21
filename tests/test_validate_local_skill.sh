#!/usr/bin/env bash
set -euo pipefail

python3 ./scripts/validate-skill.py ./skills/skill-creator

echo "test_validate_local_skill.sh: OK"
