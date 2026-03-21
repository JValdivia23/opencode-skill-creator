#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME=""
SCOPE="local"
DEST_ROOT=""
YES="false"

usage() {
  cat <<'EOF'
Uninstall an OpenCode skill by deleting its directory.

Usage:
  scripts/uninstall-skill.sh --skill-name NAME [--scope local|global] [--dest-root PATH] [--yes]

Options:
  --skill-name  Required. Skill directory name to remove.
  --scope       Scope for default path resolution (default: local)
  --dest-root   Optional root folder override. Final path is <dest-root>/<skill-name>
  --yes         Do not prompt for confirmation
  -h, --help    Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill-name)
      SKILL_NAME="$2"
      shift 2
      ;;
    --scope)
      SCOPE="$2"
      shift 2
      ;;
    --dest-root)
      DEST_ROOT="$2"
      shift 2
      ;;
    --yes)
      YES="true"
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

if [[ -z "${SKILL_NAME}" ]]; then
  echo "[ERROR] --skill-name is required" >&2
  usage
  exit 2
fi

if [[ "${SCOPE}" != "local" && "${SCOPE}" != "global" ]]; then
  echo "[ERROR] --scope must be 'local' or 'global'" >&2
  exit 2
fi

if [[ -n "${DEST_ROOT}" ]]; then
  DEST_PATH="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).expanduser().resolve())' "${DEST_ROOT}")/${SKILL_NAME}"
elif [[ "${SCOPE}" == "global" ]]; then
  DEST_PATH="${HOME}/.config/opencode/skills/${SKILL_NAME}"
else
  DEST_PATH="$(pwd)/.opencode/skills/${SKILL_NAME}"
fi

if [[ ! -e "${DEST_PATH}" ]]; then
  echo "Nothing to uninstall. Path does not exist: ${DEST_PATH}"
  exit 0
fi

echo "Skill uninstall target: ${DEST_PATH}"
if [[ "${YES}" != "true" ]]; then
  read -r -p "Delete this directory recursively? [y/N] " answer
  case "${answer}" in
    y|Y|yes|YES)
      ;;
    *)
      echo "Aborted."
      exit 1
      ;;
  esac
fi

rm -rf "${DEST_PATH}"
echo "Uninstalled: ${DEST_PATH}"
