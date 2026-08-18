# Review an agy conversation

Use this only when `RESPONSE` is missing a **specific** fact (a URL, DOI, command, or tool error). Prefer another wrapper follow-up first.

```bash
~/.agents/skills/agy/scripts/agy-run.sh --conversation UUID \
  "Return only the missing fact: …"
```

## Index, do not dump

Transcript (JSONL, one step per line):

```
~/.gemini/antigravity-cli/brain/<UUID>/.system_generated/logs/transcript.jsonl
```

List steps:

```bash
jq -r '[.step_index, .type, (.tool_calls[0].name // "-")] | @tsv' \
  ~/.gemini/antigravity-cli/brain/<UUID>/.system_generated/logs/transcript.jsonl
```

Then read **one** matching `step_index`:

```bash
jq -s --argjson i 12 '.[] | select(.step_index == $i)' \
  ~/.gemini/antigravity-cli/brain/<UUID>/.system_generated/logs/transcript.jsonl
```

`type` values: `USER_INPUT`, `PLANNER_RESPONSE`, `GENERIC` (tool results), `CHECKPOINT`.

Do not read `GENERIC` steps unless that exact tool output is required. They are large (web dumps).

## Last resort

If you must inspect the live stream, write it to a file and `jq` **one** event. Never paste `stream-json` into the host session.

```bash
agy -p "unused" --conversation UUID --output-format stream-json \
  --print-timeout 1m > /tmp/agy-stream.jsonl
```

Prefer the on-disk transcript over re-running with `stream-json`.

## Do not

- `cat` the transcript or `*.json` cache
- `--output-format stream-json` in the live host tool result
- Load `transcript_full.jsonl` unless the short transcript is insufficient
