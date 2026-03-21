# opencode-skill-creator

Tools and docs to install, validate, update, and manage OpenCode skills with deterministic behavior.

This repository includes:
- a packaged `skill-creator` skill under `skills/skill-creator/`
- installer/validator/updater/uninstaller scripts
- separate guidance for humans and agents

## Important Clarification

This project is a **toolkit**, not an automatic skill bundle installer.

- It does **not** install arbitrary example skills unless you explicitly provide the URL/skill you want.
- Example commands in docs are examples only.
- User/operator always decides what to install.

## Quick Start

From repository root:

```bash
# Install this repo's skill-creator locally
./scripts/install-skill-creator.sh --scope local --force

# Validate
./scripts/doctor-skill.sh skill-creator --scope local
```

Install a user-selected third-party skill from GitHub tree URL:

```bash
python3 ./scripts/install-skill-from-github.py \
  --url "https://github.com/OWNER/REPO/tree/BRANCH/path/to/skill" \
  --scope local
```

## Installation for Your Agent

Copy and paste this prompt into your AI agent (OpenCode, Claude, etc.) to have it install everything automatically:

> Clone the repository https://github.com/JValdivia23/opencode-skill-creator.git into a temporary directory, then install the skill-creator skill globally using the install-skill-creator.sh script with --force flag. After installation, validate it works by running the doctor-skill.sh script, then clean up by removing the temporary clone directory. Report the installation path and confirmation that skill-creator is ready to use.

**What the agent will do:**
1. Clone the repo to a temp directory
2. Run `./scripts/install-skill-creator.sh --scope global --force`
3. Run `./scripts/doctor-skill.sh skill-creator --scope global` to verify
4. Remove the temp directory
5. Report success with the installation path

## List Installed Skills

```bash
# List all skills with version info
python3 ./scripts/list-skills.py

# List only global skills
python3 ./scripts/list-skills.py --scope global

# List only local skills
python3 ./scripts/list-skills.py --scope local

# Output as JSON for scripting
python3 ./scripts/list-skills.py --json
```

## Update Skills

Skills installed with `install-skill-from-github.py` include a `.install-manifest.json` that tracks the commit SHA. This enables version-aware updates.

```bash
# Check for updates (dry run)
python3 ./scripts/update-skill.py --skill-name pdf --check-only

# Update a skill to latest version
python3 ./scripts/update-skill.py --skill-name pdf

# Force re-download even if unchanged
python3 ./scripts/update-skill.py --skill-name pdf --force
```

## Uninstall

```bash
# Remove local install
./scripts/uninstall-skill.sh --skill-name skill-creator --scope local --yes

# Remove global install
./scripts/uninstall-skill.sh --skill-name skill-creator --scope global --yes
```

## Documentation

- Human setup: `docs/install-human.md`
- Agent contract: `docs/install-agent.md`
- Claude compatibility: `docs/claude-compatibility.md`
- Troubleshooting: `docs/troubleshooting.md`

## Repository Layout

```text
skills/skill-creator/    # your current working skill files (copied as-is)
scripts/                 # install/validate/uninstall tooling
docs/                    # human and agent instructions
tests/                   # lightweight checks
```

## License

MIT for this repository. Third-party skills retain their own licenses.
