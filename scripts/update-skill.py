#!/usr/bin/env python3
"""Update an installed OpenCode skill from its GitHub source.

This script:
1. Reads the install manifest from an installed skill
2. Checks GitHub for the latest commit on the source branch
3. If newer, re-downloads all files
4. Updates the manifest with new commit SHA and timestamp
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def compute_install_path(
    scope: str, skill_name: str, dest_root: Optional[str]
) -> pathlib.Path:
    if dest_root:
        root = pathlib.Path(dest_root).expanduser().resolve()
    elif scope == "global":
        root = pathlib.Path.home() / ".config" / "opencode" / "skills"
    else:
        root = pathlib.Path.cwd() / ".opencode" / "skills"
    return root / skill_name


def _http_get_json(url: str, token: Optional[str]) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "opencode-skill-creator-updater",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get_bytes(url: str, token: Optional[str]) -> bytes:
    headers = {
        "User-Agent": "opencode-skill-creator-updater",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def get_latest_commit_sha(
    owner: str,
    repo: str,
    branch: str,
    path: str,
    token: Optional[str],
) -> Optional[str]:
    encoded_path = urllib.parse.quote(path, safe="/")
    api_url = (
        f"https://api.github.com/repos/{owner}/{repo}/commits"
        f"?path={encoded_path}&sha={urllib.parse.quote(branch, safe='')}&per_page=1"
    )
    try:
        data = _http_get_json(api_url, token)
        if isinstance(data, list) and len(data) > 0:
            commit_sha = data[0].get("sha")
            if isinstance(commit_sha, str):
                return commit_sha
    except Exception as exc:
        eprint(f"[WARN] Could not fetch latest commit SHA: {exc}")
    return None


def list_github_files_recursive(
    owner: str,
    repo: str,
    branch: str,
    source_path: str,
    token: Optional[str],
) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    quoted_ref = urllib.parse.quote(branch, safe="")

    def walk(path_in_repo: str) -> None:
        encoded_path = urllib.parse.quote(path_in_repo, safe="/")
        api_url = (
            f"https://api.github.com/repos/{owner}/{repo}/contents/"
            f"{encoded_path}?ref={quoted_ref}"
        )
        data = _http_get_json(api_url, token)

        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            raise RuntimeError(
                f"Unexpected API response at path '{path_in_repo}': {type(data)}"
            )

        for item in data:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            item_path = item.get("path")
            if not isinstance(item_path, str):
                continue

            if item_type == "file":
                download_url = item.get("download_url")
                if not isinstance(download_url, str) or not download_url:
                    eprint(f"[WARN] Skipping file with no download_url: {item_path}")
                    continue
                try:
                    rel = pathlib.PurePosixPath(item_path).relative_to(
                        pathlib.PurePosixPath(source_path)
                    )
                except ValueError:
                    eprint(
                        f"[WARN] Skipping unexpected path outside source: {item_path}"
                    )
                    continue
                out.append((rel.as_posix(), download_url))
            elif item_type == "dir":
                walk(item_path)

    walk(source_path)
    out.sort(key=lambda x: x[0])
    return out


def parse_frontmatter(skill_md_text: str) -> Dict[str, str]:
    lines = skill_md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter delimiter '---'")

    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break
    if end_index is None:
        raise ValueError("SKILL.md frontmatter is missing closing '---'")

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


def validate_skill_dir(path: pathlib.Path, expected_name: str) -> List[str]:
    errors: List[str] = []

    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        errors.append("Missing SKILL.md")
        return errors

    try:
        text = skill_md.read_text(encoding="utf-8")
    except Exception as exc:
        errors.append(f"Failed to read SKILL.md: {exc}")
        return errors

    try:
        fm = parse_frontmatter(text)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    name = fm.get("name", "")
    description = fm.get("description", "")

    if not name:
        errors.append("Frontmatter missing required field: name")
    elif not NAME_RE.match(name):
        errors.append(
            "Frontmatter name has invalid format. Expected regex ^[a-z0-9]+(-[a-z0-9]+)*$"
        )

    if not description:
        errors.append("Frontmatter missing required field: description")
    elif len(description) > 1024:
        errors.append("Frontmatter description exceeds 1024 characters")

    dir_name = path.name
    if name and name != dir_name:
        errors.append(
            f"Frontmatter name '{name}' does not match directory '{dir_name}'"
        )
    if expected_name != dir_name:
        errors.append(
            f"Target directory '{dir_name}' does not match expected '{expected_name}'"
        )

    return errors


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Update an installed OpenCode skill from GitHub"
    )
    p.add_argument(
        "--skill-name",
        required=True,
        help="Name of the skill to update",
    )
    p.add_argument(
        "--scope",
        choices=("global", "local"),
        default="local",
        help="Scope where skill is installed (default: local)",
    )
    p.add_argument(
        "--dest-root",
        default=None,
        help="Optional root directory (overrides scope)",
    )
    p.add_argument(
        "--check-only",
        action="store_true",
        help="Only check for updates, do not apply them",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Update even if commit SHA unchanged",
    )
    p.add_argument(
        "--github-token-env",
        default="GITHUB_TOKEN",
        help="Environment variable name containing GitHub token (optional)",
    )
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not NAME_RE.match(args.skill_name):
        eprint(f"[ERROR] Invalid skill name: {args.skill_name}")
        return 2

    token = os.environ.get(args.github_token_env)
    install_path = compute_install_path(args.scope, args.skill_name, args.dest_root)

    manifest_file = install_path / ".install-manifest.json"

    if not install_path.is_dir():
        eprint(f"[ERROR] Skill not installed at: {install_path}")
        eprint("Install it first using install-skill-from-github.py")
        return 1

    if not manifest_file.is_file():
        eprint(f"[ERROR] No install manifest found at: {manifest_file}")
        eprint(
            "This skill may have been installed manually. Reinstall with --force to enable updates."
        )
        return 1

    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        eprint(f"[ERROR] Invalid manifest JSON: {exc}")
        return 1

    source = manifest.get("source", {})
    owner = source.get("owner")
    repo = source.get("repo")
    branch = source.get("branch")
    source_path = source.get("path")

    if not all([owner, repo, branch, source_path]):
        eprint(
            "[ERROR] Manifest missing required source fields (owner, repo, branch, path)"
        )
        return 1

    current_sha = manifest.get("commit_sha")

    print("== OpenCode Skill Updater ==")
    print(f"Skill:          {args.skill_name}")
    print(f"Install path:   {install_path}")
    print(f"Source:         {owner}/{repo}@{branch}/{source_path}")
    print(f"Installed SHA:  {current_sha[:12] if current_sha else 'unknown'}...")

    latest_sha = get_latest_commit_sha(owner, repo, branch, source_path, token)

    if latest_sha:
        print(f"Latest SHA:   {latest_sha[:12]}...")
    else:
        eprint("[WARN] Could not determine latest commit SHA")

    if args.check_only:
        if not latest_sha:
            eprint("[ERROR] Cannot check without latest SHA")
            return 1
        if current_sha and current_sha == latest_sha:
            print("Status: UP TO DATE")
            return 0
        else:
            print("Status: UPDATE AVAILABLE")
            return 0

    if not args.force and current_sha and latest_sha and current_sha == latest_sha:
        print("Already up to date. Use --force to re-download anyway.")
        return 0

    print("Downloading updated files...")

    try:
        files = list_github_files_recursive(owner, repo, branch, source_path, token)
    except urllib.error.HTTPError as exc:
        eprint(f"[ERROR] GitHub API request failed: HTTP {exc.code} {exc.reason}")
        return 1
    except urllib.error.URLError as exc:
        eprint(f"[ERROR] Network error while contacting GitHub: {exc.reason}")
        return 1
    except Exception as exc:
        eprint(f"[ERROR] Failed to list repository files: {exc}")
        return 1

    if not files:
        eprint("[ERROR] No files found at source path")
        return 1

    backup_dir = install_path.with_suffix(install_path.suffix + ".bak")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.move(str(install_path), str(backup_dir))
    install_path.mkdir(parents=True, exist_ok=True)

    downloaded: List[str] = []
    success = True

    for rel, dl_url in files:
        dest_file = install_path / rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            content = _http_get_bytes(dl_url, token)
            dest_file.write_bytes(content)
            downloaded.append(rel)
        except Exception as exc:
            eprint(f"[ERROR] Failed to download {rel}: {exc}")
            success = False
            break

    if not success:
        eprint("[ERROR] Update failed, restoring backup...")
        shutil.rmtree(install_path)
        shutil.move(str(backup_dir), str(install_path))
        return 1

    shutil.rmtree(backup_dir)

    new_manifest = {
        "installed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_url": f"https://github.com/{owner}/{repo}/tree/{branch}/{source_path}",
        "source": {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "path": source_path,
        },
        "scope": args.scope,
        "skill_name": args.skill_name,
        "install_path": str(install_path),
        "files": downloaded,
    }
    if latest_sha:
        new_manifest["commit_sha"] = latest_sha
        new_manifest["previous_sha"] = current_sha

    manifest_file.write_text(
        json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8"
    )

    errors = validate_skill_dir(install_path, expected_name=args.skill_name)
    if errors:
        eprint("[ERROR] Update completed but validation failed:")
        for err in errors:
            eprint(f"  - {err}")
        return 1

    print("Update succeeded and validation passed.")
    print("Updated files:")
    for rel in downloaded:
        print(f"  - {rel}")
    if current_sha and latest_sha:
        print(f"Updated: {current_sha[:12]}... -> {latest_sha[:12]}...")
    print(f"Manifest: {manifest_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
