# Invoke agy

Use `~/.agents/skills/agy/scripts/agy-run.sh`. Do not call `agy` directly.

## What the wrapper runs

```bash
agy -p "$PROMPT" --output-format json --print-timeout 10m
```

stderr → `~/.cache/agy-opencode/<run>.stderr`  
envelope → `~/.cache/agy-opencode/<conversation_id>.json`  
last id → `~/.cache/agy-opencode/last`

Host agents must not read those files on a normal turn.

## Continue the same thread

Headless agy is stateless unless you pass an id. **Always resume with `--conversation UUID`** copied from the previous `CONVERSATION:` line. That is deterministic.

| Flag | When |
|---|---|
| `--conversation UUID` | Default. Required for every follow-up. |
| `--last` | Only if the uuid was dropped from context. Reads `~/.cache/agy-opencode/last`, which is whatever this wrapper ran most recently — not necessarily this task. |

Never use `agy -c` / `--continue`.

agy already has prior turns. Do not paste the previous `RESPONSE` back.

| Situation | Action |
|---|---|
| Refine, filter, "what was item 3?" | `--conversation UUID` |
| New unrelated task | fresh run |
| Need one buried tool result | `--conversation UUID` follow-up first; then `review.md` |

## Optional flags

| Flag | Notes |
|---|---|
| `--model SLUG` | Only if the user pins a model. Otherwise leave unset so agy uses its configured default (`agy models` / `/model` / settings). Do not hardcode a slug. |
| `--effort low\|medium\|high` | Reasoning effort |
| `--agent NAME` | `agy agents` |
| `--print-timeout T` | Default `10m` (agy default is `5m`) |
| `--add-dir PATH` | Extra workspace root; repeatable |
| `--mode accept-edits\|plan` | Execution mode |
| `--sandbox` | Terminal sandbox |
| `--dangerously-skip-permissions` | Only after a soft-deny |

Env overrides: `AGY_BIN`, `AGY_PRINT_TIMEOUT`, `AGY_OPENCODE_CACHE`.

## Auth

agy uses cached credentials. If a run says authentication required, the user must sign in once with interactive `agy` (not from this wrapper).
