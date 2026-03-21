# Troubleshooting

## Skill installed but not visible

- Confirm path exists (`.opencode/skills/<name>` or `~/.config/opencode/skills/<name>`)
- Run validation:

```bash
python3 ./scripts/validate-skill.py ".opencode/skills/<name>"
```

- Restart session so available skills are refreshed

## Validation errors

Common causes:
- Missing `SKILL.md`
- Missing frontmatter `name` or `description`
- Name mismatch between directory and frontmatter

Fix and rerun validation.

## GitHub download errors

- Check URL format: `https://github.com/OWNER/REPO/tree/BRANCH/path/to/skill`
- Try with auth token to avoid rate limits:

```bash
export GITHUB_TOKEN="<token>"
python3 ./scripts/install-skill-from-github.py --url "..."
```

## Uninstall mistakes

Use dry review first by reading the command target path before running `--yes`.
