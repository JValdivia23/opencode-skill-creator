#!/usr/bin/env python3
"""
python-ipynb helper: streamlined notebook and kernel operations for agents.

Dependencies: jupyter_client, nbformat
Install: pip install jupyter_client nbformat

Usage:
    python python_ipynb_tool.py <command> [args]

Commands:
    discover-servers                List running Jupyter servers.
    discover-kernels                List active kernel connection files.
    execute --connection <file> --code "<py>" [--timeout 30]
    variables --connection <file> [--timeout 10]
    cells list --notebook <file>
    cells insert --notebook <file> --at-index <n> --cell-type code|markdown --source "<text>"
    cells replace --notebook <file> --cell-id <id> --source "<text>"
    cells delete --notebook <file> --cell-id <id>
    validate --notebook <file> --connection <file> --positions 1,3,5 [--timeout 60]
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import time
import uuid


def _error(msg: str):
    print(json.dumps({"ok": False, "error": msg}, indent=2))
    sys.exit(1)


def _ok(data: dict):
    print(json.dumps({"ok": True, **data}, indent=2))


def discover_servers():
    """Parse `jupyter server list` output."""
    try:
        result = subprocess.run(
            ["jupyter", "server", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        _ok({"servers": [], "note": "jupyter command not found"})
        return
    except Exception as e:
        _error(str(e))
        return

    lines = result.stdout.strip().splitlines()
    servers = []
    # Typical lines:
    # Currently running servers:
    # http://localhost:8888/?token=... :: /path
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("Currently"):
            continue
        parts = line.split(" :: ", 1)
        url = parts[0].strip()
        root = parts[1].strip() if len(parts) > 1 else ""
        servers.append({"url": url, "root": root})
    _ok({"servers": servers})


def discover_kernels():
    """Find kernel connection JSON files in common runtime dirs."""
    candidates = []
    for base in [
        os.environ.get("JUPYTER_RUNTIME_DIR", ""),
        os.path.expanduser("~/Library/Jupyter/runtime"),
        os.path.expanduser("~/.local/share/jupyter/runtime"),
        os.path.expanduser("~/.jupyter/runtime"),
    ]:
        if base and os.path.isdir(base):
            candidates.extend(glob.glob(os.path.join(base, "kernel-*.json")))
    # Deduplicate preserving order
    seen = set()
    kernels = []
    for path in candidates:
        if path in seen:
            continue
        seen.add(path)
        try:
            with open(path, "r") as f:
                info = json.load(f)
            kernels.append({
                "connection_file": path,
                "kernel_name": info.get("kernel_name", "unknown"),
                "key": info.get("key", ""),
            })
        except Exception:
            kernels.append({"connection_file": path, "kernel_name": "unknown", "key": ""})
    _ok({"kernels": kernels})


def _kernel_client(connection_file: str, timeout: int = 10):
    try:
        from jupyter_client import BlockingKernelClient
    except ImportError:
        raise RuntimeError("jupyter_client is required. Install: pip install jupyter_client")

    kc = BlockingKernelClient(connection_file=connection_file)
    kc.load_connection_file()
    kc.start_channels()
    kc.wait_for_ready(timeout=timeout)
    return kc


def execute_code(connection_file: str, code: str, timeout: int = 30):
    try:
        kc = _kernel_client(connection_file, timeout=10)
    except Exception as e:
        _error(str(e))
        return

    msg_id = kc.execute(code, stop_on_error=True)
    outputs = []
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            msg = kc.get_iopub_msg(timeout=1)
            if msg.get("parent_header", {}).get("msg_id") != msg_id:
                continue
            msg_type = msg.get("msg_type")
            content = msg.get("content", {})
            if msg_type == "stream":
                outputs.append({"type": "stream", "name": content.get("name"), "text": content.get("text", "")})
            elif msg_type == "execute_result":
                outputs.append({"type": "execute_result", "data": content.get("data", {})})
            elif msg_type == "error":
                outputs.append({
                    "type": "error",
                    "ename": content.get("ename"),
                    "evalue": content.get("evalue"),
                    "traceback": content.get("traceback", []),
                })
            elif msg_type == "status" and content.get("execution_state") == "idle":
                break
    except Exception as e:
        kc.stop_channels()
        _error(str(e))
        return
    finally:
        kc.stop_channels()

    _ok({"outputs": outputs})


def list_variables(connection_file: str, timeout: int = 10):
    code = (
        "import json, sys\n"
        "try:\n"
        "    from IPython import get_ipython\n"
        "    shell = get_ipython()\n"
        "    user_ns = shell.user_ns if shell else {}\n"
        "except Exception:\n"
        "    user_ns = {}\n"
        "items = []\n"
        "for k, v in list(user_ns.items()):\n"
        "    if k.startswith('_'):\n"
        "        continue\n"
        "    t = type(v).__name__\n"
        "    r = repr(v)\n"
        "    if len(r) > 200:\n"
        "        r = r[:200] + '...'\n"
        "    items.append({'name': k, 'type': t, 'repr': r})\n"
        "print(json.dumps(items))\n"
    )
    try:
        kc = _kernel_client(connection_file, timeout=10)
    except Exception as e:
        _error(str(e))
        return

    msg_id = kc.execute(code, stop_on_error=True)
    variables = []
    deadline = time.time() + timeout
    try:
        while time.time() < deadline:
            msg = kc.get_iopub_msg(timeout=1)
            if msg.get("parent_header", {}).get("msg_id") != msg_id:
                continue
            msg_type = msg.get("msg_type")
            content = msg.get("content", {})
            if msg_type == "stream" and content.get("name") == "stdout":
                try:
                    variables = json.loads(content.get("text", "[]"))
                except json.JSONDecodeError:
                    pass
            elif msg_type == "status" and content.get("execution_state") == "idle":
                break
    except Exception as e:
        kc.stop_channels()
        _error(str(e))
        return
    finally:
        kc.stop_channels()

    _ok({"variables": variables})


def _read_notebook(path: str):
    try:
        import nbformat
    except ImportError:
        raise RuntimeError("nbformat is required. Install: pip install nbformat")
    return nbformat.read(path, as_version=4)


def _write_notebook(path: str, nb):
    import nbformat
    nbformat.write(nb, path)


def cells_list(notebook_path: str):
    try:
        nb = _read_notebook(notebook_path)
    except Exception as e:
        _error(str(e))
        return
    cells = []
    for idx, cell in enumerate(nb.cells):
        cid = cell.get("id", f"cell-{idx}")
        cells.append({
            "index": idx,
            "id": cid,
            "cell_type": cell.cell_type,
            "source_preview": cell.source[:200] + "..." if len(cell.source) > 200 else cell.source,
        })
    _ok({"cells": cells})


def cells_insert(notebook_path: str, at_index: int, cell_type: str, source: str):
    try:
        import nbformat
        nb = _read_notebook(notebook_path)
        new_cell = nbformat.v4.new_code_cell(source) if cell_type == "code" else nbformat.v4.new_markdown_cell(source)
        new_cell.id = str(uuid.uuid4())[:8]
        if at_index < 0 or at_index > len(nb.cells):
            at_index = len(nb.cells)
        nb.cells.insert(at_index, new_cell)
        _write_notebook(notebook_path, nb)
    except Exception as e:
        _error(str(e))
        return
    _ok({"inserted_at": at_index, "cell_id": new_cell.id})


def cells_replace(notebook_path: str, cell_id: str, source: str):
    try:
        nb = _read_notebook(notebook_path)
        found = False
        for cell in nb.cells:
            if cell.get("id") == cell_id:
                cell.source = source
                found = True
                break
        if not found:
            _error(f"Cell id '{cell_id}' not found.")
            return
        _write_notebook(notebook_path, nb)
    except Exception as e:
        _error(str(e))
        return
    _ok({"replaced": cell_id})


def cells_delete(notebook_path: str, cell_id: str):
    try:
        nb = _read_notebook(notebook_path)
        original = len(nb.cells)
        nb.cells = [c for c in nb.cells if c.get("id") != cell_id]
        if len(nb.cells) == original:
            _error(f"Cell id '{cell_id}' not found.")
            return
        _write_notebook(notebook_path, nb)
    except Exception as e:
        _error(str(e))
        return
    _ok({"deleted": cell_id})


def validate_cells(notebook_path: str, connection_file: str, positions: list[int], timeout: int = 60):
    try:
        nb = _read_notebook(notebook_path)
        kc = _kernel_client(connection_file, timeout=10)
    except Exception as e:
        _error(str(e))
        return

    code_cells = [c for c in nb.cells if c.get("cell_type") == "code"]
    results = []
    try:
        for pos in positions:
            if pos < 1 or pos > len(code_cells):
                _error(f"Invalid code-cell position: {pos}. Notebook has {len(code_cells)} code cells.")
                return
            source = code_cells[pos - 1].get("source", "")
            msg_id = kc.execute(source, stop_on_error=True, store_history=False)
            cell_deadline = time.time() + timeout
            while time.time() < cell_deadline:
                msg = kc.get_iopub_msg(timeout=1)
                if msg.get("parent_header", {}).get("msg_id") != msg_id:
                    continue
                msg_type = msg.get("msg_type")
                content = msg.get("content", {})
                if msg_type == "error":
                    traceback = "\n".join(content.get("traceback", []))
                    _error(f"Code-cell {pos} failed:\n{traceback}")
                    return
                if msg_type == "status" and content.get("execution_state") == "idle":
                    break
            results.append({"position": pos, "status": "ok"})
    except Exception as e:
        kc.stop_channels()
        _error(str(e))
        return
    finally:
        kc.stop_channels()

    _ok({"validated": results})


def main():
    parser = argparse.ArgumentParser(description="python-ipynb agent helper")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("discover-servers", help="List running Jupyter servers")
    sub.add_parser("discover-kernels", help="List active kernel connection files")

    p_exec = sub.add_parser("execute", help="Execute code in a kernel")
    p_exec.add_argument("--connection", required=True)
    p_exec.add_argument("--code", required=True)
    p_exec.add_argument("--timeout", type=int, default=30)

    p_vars = sub.add_parser("variables", help="List variables in a kernel")
    p_vars.add_argument("--connection", required=True)
    p_vars.add_argument("--timeout", type=int, default=10)

    p_cells = sub.add_parser("cells", help="Notebook cell operations")
    cells_sub = p_cells.add_subparsers(dest="cells_cmd")
    p_list = cells_sub.add_parser("list", help="List cells")
    p_list.add_argument("--notebook", required=True)
    p_ins = cells_sub.add_parser("insert", help="Insert a cell")
    p_ins.add_argument("--notebook", required=True)
    p_ins.add_argument("--at-index", type=int, required=True)
    p_ins.add_argument("--cell-type", choices=["code", "markdown"], required=True)
    p_ins.add_argument("--source", required=True)
    p_rep = cells_sub.add_parser("replace", help="Replace cell source")
    p_rep.add_argument("--notebook", required=True)
    p_rep.add_argument("--cell-id", required=True)
    p_rep.add_argument("--source", required=True)
    p_del = cells_sub.add_parser("delete", help="Delete a cell")
    p_del.add_argument("--notebook", required=True)
    p_del.add_argument("--cell-id", required=True)

    p_val = sub.add_parser("validate", help="Validate specific cells in a kernel")
    p_val.add_argument("--notebook", required=True)
    p_val.add_argument("--connection", required=True)
    p_val.add_argument("--positions", required=True, help="Comma-separated 1-based positions")
    p_val.add_argument("--timeout", type=int, default=60)

    args = parser.parse_args()

    if args.command == "discover-servers":
        discover_servers()
    elif args.command == "discover-kernels":
        discover_kernels()
    elif args.command == "execute":
        execute_code(args.connection, args.code, args.timeout)
    elif args.command == "variables":
        list_variables(args.connection, args.timeout)
    elif args.command == "cells":
        if args.cells_cmd == "list":
            cells_list(args.notebook)
        elif args.cells_cmd == "insert":
            cells_insert(args.notebook, args.at_index, args.cell_type, args.source)
        elif args.cells_cmd == "replace":
            cells_replace(args.notebook, args.cell_id, args.source)
        elif args.cells_cmd == "delete":
            cells_delete(args.notebook, args.cell_id)
        else:
            parser.print_help()
            sys.exit(1)
    elif args.command == "validate":
        positions = [int(x.strip()) for x in args.positions.split(",")]
        validate_cells(args.notebook, args.connection, positions, args.timeout)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
