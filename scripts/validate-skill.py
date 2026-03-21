#!/usr/bin/env python3
"""Validate an installed or local OpenCode skill directory."""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Dict, List, Tuple


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(skill_md: pathlib.Path) -> Dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter (---)")

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise ValueError("Frontmatter missing closing delimiter (---)")

    out: Dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def validate(path: pathlib.Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not path.exists():
        errors.append(f"Path does not exist: {path}")
        return errors, warnings
    if not path.is_dir():
        errors.append(f"Path is not a directory: {path}")
        return errors, warnings

    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        errors.append("Missing required file: SKILL.md")
        return errors, warnings

    try:
        fm = parse_frontmatter(skill_md)
    except Exception as exc:
        errors.append(str(exc))
        return errors, warnings

    name = fm.get("name", "")
    desc = fm.get("description", "")
    dir_name = path.name

    if not name:
        errors.append("Missing required frontmatter field: name")
    elif not NAME_RE.match(name):
        errors.append("Invalid name format. Must match ^[a-z0-9]+(-[a-z0-9]+)*$")

    if not desc:
        errors.append("Missing required frontmatter field: description")
    elif len(desc) > 1024:
        errors.append("Description exceeds 1024 characters")

    if name and name != dir_name:
        errors.append(f"Name mismatch: frontmatter '{name}' vs directory '{dir_name}'")

    # Medium strictness warnings
    lower = skill_md.read_text(encoding="utf-8").lower()
    if "claude -p" in lower:
        warnings.append("Contains 'claude -p' command; may need OpenCode adaptation")
    if "~/.claude/skills" in lower:
        warnings.append("Contains Claude skills path; may need path adaptation")
    if "present_files" in lower:
        warnings.append(
            "References present_files; verify tool availability in OpenCode"
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate OpenCode skill directory")
    parser.add_argument("path", help="Path to skill directory (contains SKILL.md)")
    args = parser.parse_args()

    skill_path = pathlib.Path(args.path).expanduser().resolve()
    errors, warnings = validate(skill_path)

    print(f"Skill path: {skill_path}")
    if errors:
        print("Errors:")
        for e in errors:
            print(f"  - {e}")
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("Validation: FAILED")
        return 1

    if warnings:
        print("Validation: PASSED (with warnings)")
    else:
        print("Validation: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
