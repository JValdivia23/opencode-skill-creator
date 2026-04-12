---
name: python-ipynb
description: Convert and sync Python scripts and Jupyter notebooks with jupytext (default) and ipynb-py-convert (fallback), preserve notebook outputs, and attach to the user's active kernel for targeted execution. Use when users mention .ipynb, jupytext, ipynb-py-convert, or %connect_info.
version: 1.0.0
---

# Python IPYNB

Use this skill to keep `.py` and `.ipynb` aligned while preserving notebook outputs and executing tests in the user's kernel.

## What I Do

- Convert between `.py` and `.ipynb`
- Prefer paired notebook workflows with `jupytext`
- Preserve notebook outputs whenever possible
- Attach to an existing user kernel for targeted execution
- Handle separate tooling and runtime environments

## When to Use Me

Use this skill when:
- The user mentions `.ipynb`, Jupyter notebooks, or notebook/script syncing
- The user asks for `jupytext`, `ipynb-py-convert`, or `pupytext` workflows
- The user wants to run or test specific notebook code through an existing kernel
- The user provides `%connect_info` output or asks to connect to a running kernel

Do not use this skill when:
- The task is unrelated to notebook or script conversion/sync
- The user is asking for generic Python coding without notebook context

## Kernel Selection Policy (Required)

1. If the task targets an existing `.ipynb`, use its kernelspec metadata when present.
2. If the user provides `%connect_info` output or a connection file, use that active kernel.
3. If creating a notebook for the first time and the kernel/environment is not stated, ask exactly one targeted question for the kernel/environment and do not assume.
4. Execute and test code in the user-selected kernel, not in the conversion tooling environment.
5. Never restart, replace, or shut down the user's running kernel unless explicitly requested.

## Two-Environment Policy (Required)

- Runtime kernel: the user's notebook kernel for execution and testing.
- Tooling environment: terminal/python environment used for conversion commands.
- `jupytext` may exist only in the tooling environment; this is acceptable.
- Keep conversion in the tooling environment and keep execution/testing in the user kernel.

## Default Workflow (jupytext)

Install in tooling environment:

```bash
pip install jupytext
```

Create or enforce paired files (default):

```bash
jupytext --set-formats ipynb,py script.py --sync
```

Sync after edits:

```bash
jupytext --sync script.py
```

One-shot conversions:

```bash
# .py -> .ipynb
jupytext --to notebook script.py

# .ipynb -> .py
jupytext --to py notebook.ipynb
```

## Output Preservation Policy (Required)

- Prefer `jupytext --sync <file>` for paired files.
- To update inputs while preserving outputs/metadata, use `jupytext --update --to notebook <script.py>`.
- Avoid `jupytext --to notebook <script.py>` on already paired notebooks because it recreates notebooks without outputs.
- If code in a cell changes, updating or clearing that cell's output is correct.
- Do not use `ipynb-py-convert` when output preservation is required.

## Fallback Workflow (ipynb-py-convert)

Use only when requested or when output retention is not required.

```bash
pip install ipynb-py-convert
ipynb-py-convert script.py script.ipynb
ipynb-py-convert notebook.ipynb notebook.py
```

## Connect to User Kernel

### Human console pattern

```bash
pip install jupyter-console
jupyter console --existing
```

Inside notebook:

```python
%connect_info
```

### Agent-first non-interactive pattern

1. Get the kernel connection file path from `%connect_info` output.
2. Attach with `jupyter_client` and execute a bounded snippet.
3. Capture `stream`, `execute_result`, and `error` outputs.
4. Apply final code edits to `.py`, then sync notebook files.

```bash
pip install jupyter-client
python - <<'PY'
from jupyter_client import BlockingKernelClient
import time

connection_file = "KERNEL_CONNECTION_FILE.json"
code = "print('kernel ok')"

kc = BlockingKernelClient(connection_file=connection_file)
kc.load_connection_file()
kc.start_channels()
kc.wait_for_ready(timeout=10)

msg_id = kc.execute(code, stop_on_error=True)
deadline = time.time() + 30
while time.time() < deadline:
    msg = kc.get_iopub_msg(timeout=1)
    if msg.get("parent_header", {}).get("msg_id") != msg_id:
        continue
    msg_type = msg.get("msg_type")
    content = msg.get("content", {})
    if msg_type == "stream":
        print(content.get("text", ""), end="")
    elif msg_type == "execute_result":
        print(content.get("data", {}).get("text/plain", ""))
    elif msg_type == "error":
        print("\n".join(content.get("traceback", [])))
        break
    elif msg_type == "status" and content.get("execution_state") == "idle":
        break

kc.stop_channels()
PY
```

## Common Tasks

| Task | Command |
|------|---------|
| Pair script and notebook | `jupytext --set-formats ipynb,py script.py --sync` |
| Sync paired files | `jupytext --sync script.py` |
| Update inputs and keep outputs | `jupytext --update --to notebook script.py` |
| One-shot `.py` to `.ipynb` | `jupytext --to notebook script.py` |
| One-shot `.ipynb` to `.py` | `jupytext --to py notebook.ipynb` |
| Fallback convert | `ipynb-py-convert script.py script.ipynb` |

## Important Notes

- Use `.py` as the editable source for agent-driven changes.
- Run tests in the user-selected runtime kernel.
- Keep conversion and execution concerns separated when environments differ.
- If kernel is unknown for a first-time notebook, ask once, then proceed with that kernel.
