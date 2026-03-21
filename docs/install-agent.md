# Agent Installation Contract

This document defines deterministic behavior for agents installing the `skill-creator` skill from this repository.

## Core Rule

Never claim a skill is installed unless files were actually downloaded and validation passed.

## Quick Installation (Copy-Paste This)

For agents reading this file, install the skill-creator using the manifest below:

```
Read https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/manifest.yaml
Then download each file listed under `source.files` to the target installation directory:
  - Local: .opencode/skills/skill-creator/
  - Global: ~/.config/opencode/skills/skill-creator/
Base URL for downloads: https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/
After downloading, validate by checking that SKILL.md exists and has valid frontmatter with 'name' and 'description' fields.
Report success with the installation path and file count.
```

## Explicit Non-Automation Rule

- Examples in docs are examples only.
- Do not auto-install sample skills unless the user explicitly asked for that specific skill URL.
- The user decides which skill to install.

## Manual Installation Flow (If Not Using Manifest)

1. Parse user-provided target scope (`local` or `global`).
2. Download all skill files from the manifest or file list:
   - SKILL.md
   - references/installation-guide.md
   - references/troubleshooting.md
   - references/claude-adaptation.md
   - references/templates/basic-skill.md
   - references/templates/full-skill.md
3. Validate installed skill directory:
   - SKILL.md exists
   - Frontmatter has `name` and `description`
   - `name` matches directory name (skill-creator)
4. Report installed files and location.
5. If validation fails, report failure and do not claim success.

## Using Repository Scripts (Alternative)

If the full repository is available locally:

```bash
python3 ./scripts/install-skill-from-github.py --url "https://github.com/JValdivia23/opencode-skill-creator/tree/main/skills/skill-creator" --scope local
python3 ./scripts/validate-skill.py "./.opencode/skills/skill-creator"
```

For repo skill itself (if repo cloned):

```bash
./scripts/install-skill-creator.sh --scope local --force
```

## Required Success Report Format

After install, report:

- Source: GitHub raw URLs or local scripts
- Destination path
- Complete installed file list (6 files total)
- Validation status
- Warnings (Claude/OpenCode compatibility notes)

## Required Failure Report Format

If any step fails, report:

- Failing step
- Command/tool error
- Partial artifacts left on disk (if any)
- Next corrective action

## File Checksum Verification (Optional)

For additional security, verify files match expected checksums:
- Download manifest.yaml first
- Verify each downloaded file exists
- Future: checksum validation may be added to manifest
