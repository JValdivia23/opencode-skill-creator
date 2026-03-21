# Agent Installation Contract

This document defines deterministic behavior for agents using this repository.

## Core Rule

Never claim a skill is installed unless files were actually downloaded/copied and validation passed.

## Required Installation Flow

1. Parse user-provided source URL and target scope (`local` or `global`).
2. Download the full skill directory recursively.
   - Do not install only `SKILL.md` when additional files/directories exist.
3. Validate installed skill directory:
   - `SKILL.md` exists
   - Frontmatter has `name` and `description`
   - `name` matches directory name
4. Report installed files and location.
5. If validation fails, report failure and do not claim success.

## Explicit Non-Automation Rule

- Examples in docs are examples only.
- Do not auto-install sample skills unless the user explicitly asked for that specific skill URL.
- The user decides which skill to install.

## Preferred Tooling

Use repository scripts:

```bash
python3 ./scripts/install-skill-from-github.py --url "<github-tree-url>" --scope local
python3 ./scripts/validate-skill.py "./.opencode/skills/<skill-name>"
```

For repo skill itself:

```bash
./scripts/install-skill-creator.sh --scope local --force
```

## Required Success Report Format

After install, report:

- source URL
- destination path
- complete installed file list
- validation status
- warnings (Claude/OpenCode compatibility notes)

## Required Failure Report Format

If any step fails, report:

- failing step
- command/tool error
- partial artifacts left on disk (if any)
- next corrective action
