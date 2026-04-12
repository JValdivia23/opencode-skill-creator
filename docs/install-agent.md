# Agent Installation Contract

This document defines deterministic behavior for agents installing the `skill-creator` skill from this repository.

## Core Rule

Never claim a skill is installed unless files were actually downloaded and validation passed.

## Quick Installation (Copy-Paste This)

For agents reading this file, install skill-creator by downloading these files:

```
Create directory ~/.config/opencode/skills/skill-creator/references/templates/

Download these files:
1. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/SKILL.md
2. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/installation-guide.md
3. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/troubleshooting.md
4. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/claude-adaptation.md
5. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/templates/basic-skill.md
6. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/skill-creator/references/templates/full-skill.md

Validate by checking that SKILL.md exists and has valid frontmatter with 'name' and 'description' fields.
If the installed skill is later used to install third-party skills from GitHub, the agent must scan the target skill docs for prerequisites/dependencies and verify what it can. Missing dependencies should be reported as installed with warnings.
Report success with the installation path and file count.
```

## Explicit Non-Automation Rule

- Examples in docs are examples only.
- Do not auto-install sample skills unless the user explicitly asked for that specific skill URL.
- The user decides which skill to install.

## Required Success Report Format

After install, report:

- Source: GitHub raw URLs
- Destination path
- Complete installed file list
- Validation status
- Requirement Check status (for target skill installs): Found / Verified / Missing / Not checked
- Warnings (Claude/OpenCode compatibility notes)

## Required Failure Report Format

If any step fails, report:

- Failing step
- Command/tool error
- Partial artifacts left on disk (if any)
- Next corrective action
