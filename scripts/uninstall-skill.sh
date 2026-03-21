#!/bin/bash
#
# Uninstall an OpenCode skill
# Usage: ./uninstall-skill.sh --skill-name NAME [--scope local|global] [--yes]
#

set -e

# Default values
SCOPE="local"
YES=false

# Show usage
usage() {
  cat << 'EOF'
Uninstall an OpenCode skill by deleting its directory.

Usage:
  ./uninstall-skill.sh --skill-name NAME [--scope local|global] [--yes]

Options:
  --skill-name  Required. Skill directory name to remove.
  --scope       Scope: local (project) or global (user) (default: local)
  --yes         Do not prompt for confirmation
  -h, --help    Show this help
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --skill-name)
      SKILL_NAME="$2"
      shift 2
      ;;
    --scope)
      SCOPE="$2"
      shift 2
      ;;
    --yes)
      YES=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

# Validate
if [[ -z "$SKILL_NAME" ]]; then
  echo "Error: --skill-name is required" >&2
  usage
  exit 1
fi

if [[ "$SCOPE" != "local" && "$SCOPE" != "global" ]]; then
  echo "Error: --scope must be 'local' or 'global'" >&2
  exit 1
fi

# Determine install path
if [[ "$SCOPE" == "global" ]]; then
  INSTALL_DIR="$HOME/.config/opencode/skills/$SKILL_NAME"
else
  INSTALL_DIR="./.opencode/skills/$SKILL_NAME"
fi

echo "== OpenCode Skill Uninstaller =="
echo "Skill: $SKILL_NAME"
echo "Scope: $SCOPE"
echo "Path: $INSTALL_DIR"

# Check if installed
if [[ ! -d "$INSTALL_DIR" ]]; then
  echo "Nothing to uninstall. Skill not found at $INSTALL_DIR"
  exit 0
fi

# Show files that will be removed
echo ""
echo "Files to be removed:"
find "$INSTALL_DIR" -type f 2>/dev/null | sed "s|$INSTALL_DIR/|  - |" || echo "  (empty directory)"

# Confirm
if [[ "$YES" != "true" ]]; then
  echo ""
  read -r -p "Delete this directory? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
  fi
fi

# Remove
rm -rf "$INSTALL_DIR"

echo ""
echo "== Uninstall Complete =="
echo "Removed: $INSTALL_DIR"
