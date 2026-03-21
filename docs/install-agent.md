# Agent Installation Contract

This document defines deterministic behavior for agents installing the `skill-creator` skill from this repository.

## Core Rule

Never claim a skill is installed unless files were actually downloaded and validation passed.

## Quick Installation (Copy-Paste This)

For agents reading this file, install the skill-creator by reading its SKILL.md:

```
Read https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/SKILL.md
Follow the installation instructions in the SKILL.md to download all required files to the target directory:
  - Local: .opencode/skills/skill-creator/
  - Global: ~/.config/opencode/skills/skill-creator/
After downloading, validate by checking that SKILL.md exists and has valid frontmatter with 'name' and 'description' fields.
Report success with the installation path and file count.
```

## Explicit Non-Automation Rule

- Examples in docs are examples only.
- Do not auto-install sample skills unless the user explicitly asked for that specific skill URL.
- The user decides which skill to install.

## Files to Download

When installing skill-creator, download these files:

1. SKILL.md
2. references/installation-guide.md
3. references/troubleshooting.md
4. references/claude-adaptation.md
5. references/templates/basic-skill.md
6. references/templates/full-skill.md

Base URL: `https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/`

## Required Success Report Format

After install, report:

- Source: GitHub raw URLs
- Destination path
- Complete installed file list
- Validation status
- Warnings (Claude/OpenCode compatibility notes)

## Required Failure Report Format

If any step fails, report:

- Failing step
- Command/tool error
- Partial artifacts left on disk (if any)
- Next corrective action
