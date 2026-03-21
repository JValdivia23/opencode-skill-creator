# Claude Skills Compatibility Notes

This repository helps install skills originating from Claude's public skills repo.

## What is compatible

- `SKILL.md` structure is compatible with OpenCode discovery rules.
- Many skills work directly after installation.

## What often needs review

- references to `claude -p`
- references to `~/.claude/skills`
- references to tools not present in OpenCode (`present_files`, etc.)

Use:

```bash
python3 ./scripts/validate-skill.py "<installed-skill-path>"
```

And inspect `skills/skill-creator/references/claude-adaptation.md` for adaptation guidance.
