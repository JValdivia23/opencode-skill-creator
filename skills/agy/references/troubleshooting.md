# Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `missing dependency: agy` | Not on PATH | `command -v agy`; binary is often `~/.local/bin/agy` |
| `missing dependency: jq` | jq not installed | `brew install jq` |
| `authentication required` | No cached login | User runs interactive `agy` once and signs in |
| `STATUS: ERROR` with empty CONVERSATION | Failed before a thread was created | Read `ERROR:`; start a new run |
| Soft-deny / tool blocked | Headless cannot prompt | User allow-list, or one-shot `--dangerously-skip-permissions` |
| Timeout | Default wait too short | `--print-timeout 15m` (or higher) |
| `--last` fails | No prior wrapper run, or last id is a different task | Use `--conversation UUID` from the run you care about |
| Wrong prior context | Used `agy -c` or `--last` | Resume with `--conversation UUID` |
| Non-JSON stdout | agy printed diagnostics on stdout | Check `~/.cache/agy-opencode/*.stderr` |

Cache dir: `~/.cache/agy-opencode/` (`AGY_OPENCODE_CACHE` overrides).

Live docs: https://antigravity.google/docs/cli/headless/
