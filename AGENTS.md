# AGENTS.md

Operational rules for agents working in this repository.

## Intent

This repository provides installation tooling and guidance. It is not a directive to auto-install all sample skills.

## Mandatory Rules

1. Never claim installation succeeded without file-level verification.
2. Never treat README/doc examples as already installed skills.
3. Only install skills explicitly requested by user.
4. Always validate installed skill directory before success message.
5. Report exact install path and installed file list.

## Use These Scripts

- Install this repo's skill:
  - `./scripts/install-skill-creator.sh --scope local --force`
- Install third-party skill by URL:
  - `python3 ./scripts/install-skill-from-github.py --url "..." --scope local`
- List installed skills:
  - `python3 ./scripts/list-skills.py`
- Check for updates:
  - `python3 ./scripts/update-skill.py --skill-name <name> --check-only`
- Update a skill:
  - `python3 ./scripts/update-skill.py --skill-name <name>`
- Validate:
  - `python3 ./scripts/validate-skill.py "<path>"`
- Uninstall:
  - `./scripts/uninstall-skill.sh --skill-name <name> --scope local --yes`

## Failure Handling

If installation fails, do not continue with partial assumptions. Report failure, reason, and next fix.
