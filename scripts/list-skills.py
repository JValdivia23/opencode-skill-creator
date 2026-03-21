#!/usr/bin/env python3
"""List installed OpenCode skills with version information.

This script scans skill directories and displays:
- Skill name
- Installation scope (global/local)
- Installation date
- Source repository
- Commit SHA (if available)
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime
from typing import Dict, List, Optional


def parse_frontmatter(skill_md_text: str) -> Dict[str, str]:
    lines = skill_md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break
    if end_index is None:
        return {}

    fields: Dict[str, str] = {}
    for line in lines[1:end_index]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        value = v.strip().strip('"').strip("'")
        if key:
            fields[key] = value
    return fields


def format_datetime(iso_str: Optional[str]) -> str:
    if not iso_str:
        return "unknown"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str[:16] if len(iso_str) >= 16 else iso_str


def gather_skills(base_path: pathlib.Path, scope: str) -> List[Dict]:
    skills = []

    if not base_path.is_dir():
        return skills

    for skill_dir in sorted(base_path.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_name = skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        manifest_file = skill_dir / ".install-manifest.json"

        info = {
            "name": skill_name,
            "scope": scope,
            "description": "",
            "installed_at": None,
            "source_repo": None,
            "commit_sha": None,
            "has_manifest": False,
        }

        if skill_md.is_file():
            try:
                fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
                info["description"] = fm.get("description", "")[:60]
                if len(fm.get("description", "")) > 60:
                    info["description"] += "..."
            except Exception:
                pass

        if manifest_file.is_file():
            try:
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
                info["has_manifest"] = True
                info["installed_at"] = manifest.get("installed_at")

                source = manifest.get("source", {})
                owner = source.get("owner", "")
                repo = source.get("repo", "")
                if owner and repo:
                    info["source_repo"] = f"{owner}/{repo}"

                info["commit_sha"] = manifest.get("commit_sha")
            except Exception:
                pass

        skills.append(info)

    return skills


def main() -> int:
    parser = argparse.ArgumentParser(description="List installed OpenCode skills")
    parser.add_argument(
        "--scope",
        choices=("global", "local", "all"),
        default="all",
        help="Which skills to list (default: all)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--short",
        action="store_true",
        help="Show only skill names",
    )
    args = parser.parse_args()

    global_path = pathlib.Path.home() / ".config" / "opencode" / "skills"
    local_path = pathlib.Path.cwd() / ".opencode" / "skills"

    all_skills: List[Dict] = []

    if args.scope in ("global", "all"):
        all_skills.extend(gather_skills(global_path, "global"))

    if args.scope in ("local", "all"):
        all_skills.extend(gather_skills(local_path, "local"))

    if not all_skills:
        print("No skills installed.")
        return 0

    if args.json:
        print(json.dumps(all_skills, indent=2))
        return 0

    if args.short:
        for skill in all_skills:
            print(skill["name"])
        return 0

    max_name = max(len(s["name"]) for s in all_skills)
    max_scope = 6
    max_repo = max(len(s["source_repo"] or "manual") for s in all_skills)

    header = f"{'NAME':<{max_name}} {'SCOPE':<{max_scope}} {'INSTALLED':<17} {'COMMIT':<12} {'SOURCE':<{max_repo}} DESCRIPTION"
    print(header)
    print("-" * len(header))

    for skill in all_skills:
        name = skill["name"]
        scope = skill["scope"]
        installed = format_datetime(skill["installed_at"])
        commit = (skill["commit_sha"] or "unknown")[:12] + "..."
        if skill["commit_sha"]:
            commit = skill["commit_sha"][:12] + "..."
        source = skill["source_repo"] or "manual"
        desc = skill["description"]

        print(
            f"{name:<{max_name}} {scope:<{max_scope}} {installed:<17} {commit:<12} {source:<{max_repo}} {desc}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
