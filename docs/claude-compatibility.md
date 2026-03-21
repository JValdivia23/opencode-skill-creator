# Claude Skills Compatibility Notes

This repository helps install skills originating from Claude's public skills repo.

## What is compatible

- `SKILL.md` structure is compatible with OpenCode discovery rules.
- Many skills work directly after installation.

## What often needs review

- references to `claude -p`
- references to `~/.claude/skills`
- references to tools not present in OpenCode (`present_files`, etc.)

## Validation

To validate a skill manually:

```bash
# Check if SKILL.md exists
ls ~/.config/opencode/skills/<skill-name>/SKILL.md

# Check frontmatter
head -5 ~/.config/opencode/skills/<skill-name>/SKILL.md

# Verify name matches directory
SKILL_NAME=$(grep "^name:" ~/.config/opencode/skills/<skill-name>/SKILL.md | sed 's/name: //')
echo "Skill name in file: $SKILL_NAME"
```

For detailed adaptation guidance, see `skills/skill-creator/references/claude-adaptation.md`.
