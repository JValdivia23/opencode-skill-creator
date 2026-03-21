#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_SKILL_DIR="${REPO_ROOT}/skills/skill-creator"

if [[ ! -d "${SOURCE_SKILL_DIR}" ]]; then
  echo "[ERROR] Cannot find source skill at ${SOURCE_SKILL_DIR}" >&2
  exit 1
fi

SCOPE="local"
DEST_ROOT=""
FORCE="false"

usage() {
  cat <<'EOF'
Install this repository's skill-creator into OpenCode skills.

Usage:
  scripts/install-skill-creator.sh [--scope local|global] [--dest-root PATH] [--force]

Options:
  --scope      Install scope (default: local)
  --dest-root  Optional root folder. Final path is <dest-root>/skill-creator
  --force      Overwrite existing destination
  -h, --help   Show this help

Notes:
  - This script installs only skill-creator itself.
  - It does not auto-install any third-party skills.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)
      SCOPE="$2"
      shift 2
      ;;
    --dest-root)
      DEST_ROOT="$2"
      shift 2
      ;;
    --force)
      FORCE="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ "${SCOPE}" != "local" && "${SCOPE}" != "global" ]]; then
  echo "[ERROR] --scope must be 'local' or 'global'" >&2
  exit 2
fi

if [[ -n "${DEST_ROOT}" ]]; then
  DEST_PATH="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).expanduser().resolve())' "${DEST_ROOT}")/skill-creator"
elif [[ "${SCOPE}" == "global" ]]; then
  DEST_PATH="${HOME}/.config/opencode/skills/skill-creator"
else
  DEST_PATH="$(pwd)/.opencode/skills/skill-creator"
fi

echo "Installing skill-creator"
echo "Source: ${SOURCE_SKILL_DIR}"
echo "Target: ${DEST_PATH}"

if [[ -e "${DEST_PATH}" ]]; then
  if [[ "${FORCE}" == "true" ]]; then
    rm -rf "${DEST_PATH}"
  else
    echo "[ERROR] Destination already exists. Use --force to overwrite." >&2
    exit 1
  fi
fi

mkdir -p "$(dirname "${DEST_PATH}")"
cp -R "${SOURCE_SKILL_DIR}" "${DEST_PATH}"

echo "Running validation..."
python3 "${REPO_ROOT}/scripts/validate-skill.py" "${DEST_PATH}"

echo "Done. skill-creator installed at: ${DEST_PATH}"
