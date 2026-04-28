---
name: python-ipynb
description: Convert and sync Python scripts and Jupyter notebooks with jupytext, preserve outputs, discover active kernels/servers, inspect live variables, edit notebook cells, and attach to the user's active kernel for targeted execution.
version: 1.1.0
---

# Python IPYNB

Use this skill to keep `.py` and `.ipynb` aligned while preserving notebook outputs, discover running Jupyter infrastructure, introspect kernel state, edit notebook structure, and execute code in the user's active kernel.

## What I Do

- Convert between `.py` and `.ipynb`
- Prefer paired notebook workflows with `jupytext`
- Preserve notebook outputs whenever possible
- Discover running Jupyter servers and active kernel connections
- Attach to an existing user kernel for targeted execution
- Inspect live variables in a connected kernel
- Insert, replace, and delete notebook cells programmatically
- Handle separate tooling and runtime environments

## When to Use Me

Use this skill when:
- The user mentions `.ipynb`, Jupyter notebooks, or notebook/script syncing
- The user asks for `jupytext`, `ipynb-py-convert`, or `pupytext` workflows
- The user wants to run or test specific notebook code through an existing kernel
- The user provides `%connect_info` output or asks to connect to a running kernel
- The user wants to know what variables exist in their kernel
- The user wants to edit notebook cells without opening the GUI
- The user wants to discover what notebooks or kernels are currently running

Do not use this skill when:
- The task is unrelated to notebook or script conversion/sync
- The user is asking for generic Python coding without notebook context

## Prerequisites

- `jupytext` for conversion workflows: `pip install jupytext`
- `jupyter_client` and `nbformat` for kernel operations and cell editing: `pip install jupyter_client nbformat`
- The helper script in this skill directory (relative to SKILL.md): `scripts/python_ipynb_tool.py`

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

## Agent Helper Script

This skill includes `scripts/python_ipynb_tool.py` to replace heavy inline boilerplate with single commands that return structured JSON. Use it for all kernel and notebook editing tasks.

Set the script path once:

```bash
TOOL="$(dirname "$0")/scripts/python_ipynb_tool.py"
# Or if running from the skill root:
TOOL="./scripts/python_ipynb_tool.py"
```

All commands below output structured JSON. On success, the top-level `ok` field is `true`. On failure, `ok` is `false` and `error` contains details.

## Discovery

### Running Jupyter servers

```bash
python "$TOOL" discover-servers
```

Returns a list of URLs and notebook directories for currently running servers.

### Active kernel connections

```bash
python "$TOOL" discover-kernels
```

Returns active kernel connection JSON files found in standard Jupyter runtime directories, including the kernel name. This eliminates the need for the user to manually locate `%connect_info` files.

## Quick Kernel Execution

### Execute code in a connected kernel

```bash
python "$TOOL" execute \
  --connection /path/to/kernel-xxx.json \
  --code "print('hello from kernel')" \
  --timeout 30
```

Returns an `outputs` array with `stream`, `execute_result`, and `error` entries. This replaces the 20+ line inline `BlockingKernelClient` boilerplate.

### Inspect live variables

```bash
python "$TOOL" variables \
  --connection /path/to/kernel-xxx.json \
  --timeout 10
```

Returns a `variables` array with `name`, `type`, and a truncated `repr` for each user-defined variable in the kernel namespace. This enables state-aware exploration without executing new code.

## Structured Notebook Cell Editing

All cell editing commands operate directly on the `.ipynb` file. If you are using a paired jupytext workflow, run `jupytext --sync` after editing to update the `.py` counterpart.

### List cells

```bash
python "$TOOL" cells list --notebook notebook.ipynb
```

Returns cell `index`, `id`, `cell_type`, and a `source_preview`.

### Insert a cell

```bash
python "$TOOL" cells insert \
  --notebook notebook.ipynb \
  --at-index 2 \
  --cell-type code \
  --source "import pandas as pd"
```

### Replace a cell's source

```bash
python "$TOOL" cells replace \
  --notebook notebook.ipynb \
  --cell-id <id-from-list> \
  --source "df = pd.read_csv('data.csv')"
```

### Delete a cell

```bash
python "$TOOL" cells delete \
  --notebook notebook.ipynb \
  --cell-id <id-from-list>
```

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

## Connect to User Kernel (Manual Pattern)

For cases where the helper script is unavailable, the manual `BlockingKernelClient` pattern is preserved below.

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

## Validate Specific Notebook Cells in User Kernel

### Using the helper script (recommended)

```bash
python "$TOOL" validate \
  --notebook notebook.ipynb \
  --connection /path/to/kernel-xxx.json \
  --positions 2,5,7 \
  --timeout 60
```

Returns per-cell status. Fails fast on the first error and reports the cell position plus traceback. Does not modify the notebook file.

### Using inline Python (legacy)

Use this mode when you need to confirm that specific cells run without errors in the user's current kernel session, but you do not want to write outputs into the notebook file.

Required behavior:
- Use the user's active kernel connection from `%connect_info`.
- Select cells by 1-based code-cell position (count only code cells, skip markdown).
- Execute selected cells in order in the same running kernel.
- Fail fast on the first error and report cell position plus traceback.
- Do not modify or save `.ipynb` in this validation mode.
- Do not run `jupytext --sync` or `jupytext --update` unless the user asks for file updates.

Example (set notebook path, connection file, and selected cell positions):

```bash
pip install nbformat jupyter-client
python - <<'PY'
import time
import nbformat
from jupyter_client import BlockingKernelClient

notebook_path = "notebook.ipynb"
connection_file = "KERNEL_CONNECTION_FILE.json"
cells_to_run = [2, 5, 7]  # 1-based code-cell positions

nb = nbformat.read(notebook_path, as_version=4)
code_cells = [cell for cell in nb.cells if cell.get("cell_type") == "code"]

selected = []
for pos in cells_to_run:
    if pos < 1 or pos > len(code_cells):
        raise SystemExit(f"Invalid code-cell position: {pos}. Notebook has {len(code_cells)} code cells.")
    selected.append((pos, code_cells[pos - 1].get("source", "")))

kc = BlockingKernelClient(connection_file=connection_file)
kc.load_connection_file()
kc.start_channels()
kc.wait_for_ready(timeout=10)

def run_cell(position: int, source: str) -> None:
    msg_id = kc.execute(source, stop_on_error=True, store_history=False)
    deadline = time.time() + 60
    while time.time() < deadline:
        msg = kc.get_iopub_msg(timeout=1)
        if msg.get("parent_header", {}).get("msg_id") != msg_id:
            continue
        msg_type = msg.get("msg_type")
        content = msg.get("content", {})
        if msg_type == "error":
            traceback = "\n".join(content.get("traceback", []))
            raise RuntimeError(f"Code-cell {position} failed:\n{traceback}")
        if msg_type == "status" and content.get("execution_state") == "idle":
            return
    raise TimeoutError(f"Timed out waiting for code-cell {position} completion.")

try:
    for position, source in selected:
        run_cell(position, source)
        print(f"Code-cell {position}: OK")
finally:
    kc.stop_channels()

print("Selected cells executed without kernel errors.")
PY
```

## Common Tasks

| Task | Command |
|------|---------|
| Pair script and notebook | `jupytext --set-formats ipynb,py script.py --sync` |
| Sync paired files | `jupytext --sync script.py` |
| Update inputs and keep outputs | `jupytext --update --to notebook script.py` |
| Discover running servers | `python "$TOOL" discover-servers` |
| Discover active kernels | `python "$TOOL" discover-kernels` |
| Execute code in kernel | `python "$TOOL" execute --connection <file> --code "<py>"` |
| List kernel variables | `python "$TOOL" variables --connection <file>` |
| List notebook cells | `python "$TOOL" cells list --notebook <file>` |
| Insert a cell | `python "$TOOL" cells insert --notebook <file> --at-index <n> --cell-type code --source "<py>"` |
| Replace cell source | `python "$TOOL" cells replace --notebook <file> --cell-id <id> --source "<py>"` |
| Delete a cell | `python "$TOOL" cells delete --notebook <file> --cell-id <id>` |
| Validate cells in kernel | `python "$TOOL" validate --notebook <file> --connection <file> --positions 1,3` |
| One-shot `.py` to `.ipynb` | `jupytext --to notebook script.py` |
| One-shot `.ipynb` to `.py` | `jupytext --to py notebook.ipynb` |
| Fallback convert | `ipynb-py-convert script.py script.ipynb` |

## Important Notes

- Use `.py` as the editable source for agent-driven changes when using jupytext pairs.
- Run tests in the user-selected runtime kernel.
- Keep conversion and execution concerns separated when environments differ.
- If kernel is unknown for a first-time notebook, ask once, then proceed with that kernel.
- Prefer the helper script for all kernel and cell-editing operations; it returns structured JSON and eliminates inline boilerplate.
