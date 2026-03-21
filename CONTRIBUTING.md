# Contributing

## Development Principles

- Keep `skills/skill-creator/` functional and backwards-compatible.
- Prefer deterministic scripts over ad hoc instructions.
- Do not blur examples with installed state.

## Local Checks

Run from repo root:

```bash
python3 ./scripts/validate-skill.py ./skills/skill-creator
python3 ./scripts/install-skill-from-github.py --url "https://github.com/anthropics/skills/tree/main/skills/pdf" --scope local --dry-run
```

## Pull Request Checklist

- [ ] docs updated when behavior changes
- [ ] installer/uninstaller behavior tested
- [ ] no claims of auto-install without explicit command
