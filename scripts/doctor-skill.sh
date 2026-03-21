#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/doctor-skill.sh <skill-name> [--scope local|global]" >&2
  exit 2
fi

SKILL_NAME="$1"
SCOPE="local"

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)
      SCOPE="$2"
      shift 2
      ;;
    *)
      echo "[ERROR] Unknown arg: $1" >&2
      exit 2
      ;;
  esac
done

if [[ "${SCOPE}" == "global" ]]; then
  PATH_CANDIDATE="${HOME}/.config/opencode/skills/${SKILL_NAME}"
else
  PATH_CANDIDATE="$(pwd)/.opencode/skills/${SKILL_NAME}"
fi

echo "Skill doctor"
echo "Scope: ${SCOPE}"
echo "Path:  ${PATH_CANDIDATE}"

if [[ ! -d "${PATH_CANDIDATE}" ]]; then
  echo "[ERROR] Skill directory not found"
  exit 1
fi

echo "\nFiles:"
ls -la "${PATH_CANDIDATE}"

echo "\nValidation:"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "${SCRIPT_DIR}/validate-skill.py" "${PATH_CANDIDATE}"
