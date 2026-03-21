# Human Installation Guide

This guide is for people using the `opencode-skill-creator` repository directly.

Important: this project does **not** auto-install third-party skills by itself. You decide which skills to install, when to install them, and where to install them.

## 1) Install this repository's `skill-creator`

From the repo root:

```bash
# Project-local install (recommended first)
./scripts/install-skill-creator.sh --scope local --force

# Global install (available in all projects)
./scripts/install-skill-creator.sh --scope global --force
```

## 2) Verify installation

```bash
# Local check
./scripts/doctor-skill.sh skill-creator --scope local

# Global check
./scripts/doctor-skill.sh skill-creator --scope global
```

## 3) Install a third-party skill (optional, user-selected)

Use the installer tool and pass the GitHub tree URL you want.

```bash
# Example URL only. You must choose your own URL.
python3 ./scripts/install-skill-from-github.py \
  --url "https://github.com/OWNER/REPO/tree/BRANCH/path/to/skill" \
  --scope local
```

If installing to global scope, use `--scope global`.

## 4) Uninstall

```bash
# Uninstall this project's skill-creator (local)
./scripts/uninstall-skill.sh --skill-name skill-creator --scope local --yes

# Uninstall this project's skill-creator (global)
./scripts/uninstall-skill.sh --skill-name skill-creator --scope global --yes

# Uninstall any installed third-party skill
./scripts/uninstall-skill.sh --skill-name YOUR_SKILL_NAME --scope local --yes
```

## Notes

- Local path: `./.opencode/skills/<name>/`
- Global path: `~/.config/opencode/skills/<name>/`
- Installer writes `.install-manifest.json` in installed skill directory
