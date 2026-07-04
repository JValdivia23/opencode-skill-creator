# Agent Installation Contract (zotero)

This document defines deterministic behavior for agents installing the `zotero` skill from this repository.

## Core Rule

Never claim this skill is installed unless files were actually downloaded and validation passed.

## Quick Installation (Copy-Paste This)

For agents reading this file, install `zotero` by downloading these files into `~/.config/opencode/skills/zotero/`:

```
1. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/SKILL.md
2. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/README.md
3. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/LICENSE.txt
4. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/.gitignore
5. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/scripts/_config.py
6. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/scripts/setup.py
7. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/scripts/pdf2md.py
8. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/scripts/check_missing_raw.py
9. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/scripts/install_add_identifier.sh
10. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/scripts/stage.py
11. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/scripts/templates/zot-translation-server.sh
12. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/scripts/templates/zot-add-identifier.py
13. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/references/getting-started.md
14. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/references/zot-cheatsheet.md
15. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/references/add-by-identifier.md
16. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/references/configuration.md
17. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/references/pdf-path-resolution.md
18. https://raw.githubusercontent.com/JValdivia23/opencode-skill-creator/main/skills/zotero/references/changelog.md
```

Validate by checking that `SKILL.md` exists and has valid frontmatter with `name` and `description` fields.

Report success with the installation path and file count (expected: 18 files).

## Explicit Non-Automation Rule

- Examples in docs are examples only.
- Do not auto-run `setup.py` after install. The user runs setup when they're ready to pick an output directory.
- The user decides which Zotero items to convert and when.

## Required Success Report Format

After install, report:

- Source: GitHub raw URLs (18 files)
- Destination path
- Complete installed file list
- Validation status

## Required Failure Report Format

If any step fails, report:

- Failing step
- Command/tool error
- Partial artifacts left on disk (if any)
- Next corrective action
