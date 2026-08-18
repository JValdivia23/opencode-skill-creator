---
name: agy
description: >-
  Delegate a task to the Antigravity CLI (agy) in headless print mode.
  Use when the user mentions agy, Antigravity CLI, antigravity, or asks to
  run or continue a task through agy. Always invoke scripts/agy-run.sh so
  only the final answer enters context. Use ONLY when the current agent is
  not already agy. Do not use for local Zotero library work.
---

# agy

Run Antigravity CLI (`agy`) headless from a host agent. Ingest **only** the wrapper's compact output. agy's thoughts, tool calls, and stderr stay on disk.

## Hard rules

1. Call `scripts/agy-run.sh`. Never bare `agy`, never `-i` / `--prompt-interactive`, never `--output-format stream-json`, never `agy -c` / `--continue`.
2. After a run, keep `STATUS`, `CONVERSATION`, and `RESPONSE`. Discard everything else.
3. Follow up on the same thread with `--conversation <uuid>` from that run's `CONVERSATION` line. Do not paste the previous answer back. Use `--last` only if the uuid was lost.
4. New unrelated task → new run (no `--conversation`).
5. Do not `cat` cache JSON, stderr logs, or brain transcripts unless `references/review.md` applies.

Wrapper path: `~/.agents/skills/agy/scripts/agy-run.sh`

## Quick start

```bash
~/.agents/skills/agy/scripts/agy-run.sh "PROMPT"
```

```bash
~/.agents/skills/agy/scripts/agy-run.sh --conversation UUID "follow-up"
```

Stdout shape:

```
STATUS: SUCCESS
CONVERSATION: <uuid>
RESPONSE:
<final answer only>
```

On failure: `STATUS: ERROR`, optional `CONVERSATION`, and `ERROR:`.

## When to use

- User asks to run something via agy / Antigravity CLI.
- A task should be delegated to agy instead of done in the current agent.

## When not to use

- Local Zotero add/read/stage/audit → `zotero` skill.
- You are already inside agy.
- The user wants the agy TUI.

## Flags you may pass through

`--model`, `--effort`, `--agent`, `--print-timeout`, `--add-dir`, `--mode`, `--sandbox`, `--dangerously-skip-permissions`. Defaults: json print mode, 10m timeout. Omit `--model` unless the user pins one — agy uses its own configured default. Skip `--dangerously-skip-permissions` unless a run soft-denies a tool.

## Review

If `RESPONSE` is missing one specific fact, read `references/review.md`. Do not load the full transcript.

## More

- Flags and continue semantics: `references/invoke.md`
- Failures: `references/troubleshooting.md`
