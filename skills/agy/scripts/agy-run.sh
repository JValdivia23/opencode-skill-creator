#!/usr/bin/env bash
# Context-safe agy headless runner for host agents (OpenCode and others).
# Prints only STATUS, CONVERSATION, and RESPONSE. Never stream-json.
set -euo pipefail

CACHE_DIR="${AGY_OPENCODE_CACHE:-${HOME}/.cache/agy-opencode}"
AGY_BIN="${AGY_BIN:-}"
if [[ -z "$AGY_BIN" ]]; then
  if command -v agy >/dev/null 2>&1; then
    AGY_BIN="$(command -v agy)"
  elif [[ -x "$HOME/.local/bin/agy" ]]; then
    AGY_BIN="$HOME/.local/bin/agy"
  elif [[ -x "/opt/homebrew/bin/agy" ]]; then
    AGY_BIN="/opt/homebrew/bin/agy"
  else
    AGY_BIN="agy"
  fi
fi
TIMEOUT="${AGY_PRINT_TIMEOUT:-10m}"
CONVERSATION=""
USE_LAST=0
MODEL=""
EFFORT=""
AGENT=""
MODE=""
SANDBOX=0
SKIP_PERMS=0
ADD_DIRS=()
PROMPT=""

usage() {
  cat <<'EOF'
Usage: agy-run.sh [options] PROMPT

Run agy headless and print only STATUS, CONVERSATION, and RESPONSE.

Options:
  --conversation ID   Resume a specific agy conversation
  --last              Resume the last conversation started by this wrapper
  --model SLUG        Pin a model (see: agy models)
  --effort LEVEL      low | medium | high
  --agent NAME        agy agent name (see: agy agents)
  --print-timeout T   Wait ceiling (default 10m)
  --add-dir PATH      Extra workspace directory (repeatable)
  --mode MODE         accept-edits | plan
  --sandbox           Enable terminal sandbox
  --dangerously-skip-permissions
  -h, --help
EOF
}

fail() {
  local msg="$1"
  printf 'STATUS: ERROR\nCONVERSATION: \nERROR: %s\n' "$msg"
  exit 1
}

emit() {
  local status="$1"
  local conv="$2"
  local response="$3"
  local error="${4:-}"
  printf 'STATUS: %s\n' "$status"
  printf 'CONVERSATION: %s\n' "$conv"
  if [[ -n "$error" && "$status" != "SUCCESS" ]]; then
    printf 'ERROR: %s\n' "$error"
  fi
  printf 'RESPONSE:\n%s\n' "$response"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "missing dependency: $1"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --conversation)
      [[ $# -ge 2 ]] || fail "--conversation requires an id"
      CONVERSATION="$2"
      shift 2
      ;;
    --last)
      USE_LAST=1
      shift
      ;;
    --model)
      [[ $# -ge 2 ]] || fail "--model requires a slug"
      MODEL="$2"
      shift 2
      ;;
    --effort)
      [[ $# -ge 2 ]] || fail "--effort requires low|medium|high"
      EFFORT="$2"
      shift 2
      ;;
    --agent)
      [[ $# -ge 2 ]] || fail "--agent requires a name"
      AGENT="$2"
      shift 2
      ;;
    --print-timeout)
      [[ $# -ge 2 ]] || fail "--print-timeout requires a duration"
      TIMEOUT="$2"
      shift 2
      ;;
    --add-dir)
      [[ $# -ge 2 ]] || fail "--add-dir requires a path"
      ADD_DIRS+=("$2")
      shift 2
      ;;
    --mode)
      [[ $# -ge 2 ]] || fail "--mode requires accept-edits|plan"
      MODE="$2"
      shift 2
      ;;
    --sandbox)
      SANDBOX=1
      shift
      ;;
    --dangerously-skip-permissions)
      SKIP_PERMS=1
      shift
      ;;
    --continue|-c)
      fail "do not use agy -c/--continue; pass --conversation <id> or --last"
      ;;
    --)
      shift
      PROMPT="$*"
      break
      ;;
    -*)
      fail "unknown option: $1"
      ;;
    *)
      PROMPT="$*"
      break
      ;;
  esac
done

[[ -n "${PROMPT//[[:space:]]/}" ]] || fail "prompt is required"
[[ "$USE_LAST" -eq 0 || -z "$CONVERSATION" ]] || fail "use either --conversation or --last, not both"

require_cmd "$AGY_BIN"
require_cmd jq
mkdir -p "$CACHE_DIR"

if [[ "$USE_LAST" -eq 1 ]]; then
  [[ -s "${CACHE_DIR}/last" ]] || fail "no last conversation; run without --last first"
  CONVERSATION="$(tr -d '[:space:]' < "${CACHE_DIR}/last")"
  [[ -n "$CONVERSATION" ]] || fail "last conversation file is empty"
fi

run_id="$(date +%Y%m%dT%H%M%S)_$$"
stdout_file="${CACHE_DIR}/${run_id}.stdout"
stderr_file="${CACHE_DIR}/${run_id}.stderr"

cmd=("$AGY_BIN" -p "$PROMPT" --output-format json --print-timeout "$TIMEOUT")
[[ -n "$CONVERSATION" ]] && cmd+=(--conversation "$CONVERSATION")
[[ -n "$MODEL" ]] && cmd+=(--model "$MODEL")
[[ -n "$EFFORT" ]] && cmd+=(--effort "$EFFORT")
[[ -n "$AGENT" ]] && cmd+=(--agent "$AGENT")
[[ -n "$MODE" ]] && cmd+=(--mode "$MODE")
[[ "$SANDBOX" -eq 1 ]] && cmd+=(--sandbox)
[[ "$SKIP_PERMS" -eq 1 ]] && cmd+=(--dangerously-skip-permissions)
for dir in "${ADD_DIRS[@]+"${ADD_DIRS[@]}"}"; do
  cmd+=(--add-dir "$dir")
done

set +e
"${cmd[@]}" >"$stdout_file" 2>"$stderr_file"
agy_exit=$?
set -e

if ! jq -e . "$stdout_file" >/dev/null 2>&1; then
  tail_err="$(tail -c 500 "$stderr_file" 2>/dev/null || true)"
  fail "agy returned non-JSON (exit ${agy_exit})${tail_err:+; ${tail_err}}"
fi

status="$(jq -r '.status // "ERROR"' "$stdout_file")"
conv="$(jq -r '.conversation_id // empty' "$stdout_file")"
response="$(jq -r '.response // empty' "$stdout_file")"
error="$(jq -r '.error // empty' "$stdout_file")"

if [[ -n "$conv" ]]; then
  cp "$stdout_file" "${CACHE_DIR}/${conv}.json"
  printf '%s\n' "$conv" > "${CACHE_DIR}/last"
  printf '%s\n' "$stderr_file" > "${CACHE_DIR}/${conv}.stderr.path"
fi

if [[ -z "$error" && "$status" != "SUCCESS" ]]; then
  error="agy status ${status} (exit ${agy_exit})"
fi

emit "$status" "$conv" "$response" "$error"
[[ "$status" == "SUCCESS" && "$agy_exit" -eq 0 ]]
