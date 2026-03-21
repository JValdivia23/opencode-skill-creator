# Troubleshooting

## Skill installed but not visible

- Confirm path exists (`.opencode/skills/<name>` or `~/.config/opencode/skills/<name>`)
- Check that SKILL.md is readable:
  ```bash
  cat ~/.config/opencode/skills/<name>/SKILL.md
  ```
- Verify frontmatter is present:
  ```bash
  head -5 ~/.config/opencode/skills/<name>/SKILL.md
  ```
- Restart session so available skills are refreshed

## Validation errors

Common causes:
- Missing `SKILL.md`
- Missing frontmatter `name` or `description`
- Name mismatch between directory and frontmatter

Quick validation:
```bash
SKILL_PATH="~/.config/opencode/skills/<name>"

# Check SKILL.md exists
[ -f "$SKILL_PATH/SKILL.md" ] && echo "✓ SKILL.md exists" || echo "✗ Missing!"

# Check frontmatter
head -1 "$SKILL_PATH/SKILL.md" | grep -q "^---" && echo "✓ Frontmatter present" || echo "✗ No frontmatter!"

# Check name field
grep "^name:" "$SKILL_PATH/SKILL.md" | head -1

# Check description field
grep "^description:" "$SKILL_PATH/SKILL.md" | head -1
```

## GitHub download errors

- Check URL format: `https://github.com/OWNER/REPO/tree/BRANCH/path/to/skill`
- Verify the URL is accessible in a browser
- Check file permissions after download
- Ensure curl is available: `which curl`

## Uninstall mistakes

Always review what will be removed before deleting:
```bash
ls -la ~/.config/opencode/skills/<skill-name>/
```

Then remove:
```bash
rm -rf ~/.config/opencode/skills/<skill-name>/
```
