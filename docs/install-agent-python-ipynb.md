# Agent Installation Contract (python-ipynb)

This document defines deterministic behavior for agents installing the `python-ipynb` skill from this repository.

## Core Rule

Never claim this skill is installed unless files were actually downloaded and validation passed.

## Quick Installation (Copy-Paste This)

For agents reading this file, install `python-ipynb` by downloading this file:

```
Create directory ~/.config/opencode/skills/python-ipynb/

Download this file:
1. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/python-ipynb/SKILL.md

Validate by checking that SKILL.md exists and has valid frontmatter with 'name' and 'description' fields.
Report success with the installation path and file count.
```

## Explicit Non-Automation Rule

- Examples in docs are examples only.
- Do not auto-run conversions or kernel execution after install.
- The user decides which notebook/project to operate on.

## Required Success Report Format

After install, report:

- Source: GitHub raw URLs
- Destination path
- Complete installed file list
- Validation status

## Required Failure Report Format

If any step fails, report:

- Failing step
- Command/tool error
- Partial artifacts left on disk (if any)
- Next corrective action
