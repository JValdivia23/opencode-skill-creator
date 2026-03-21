#!/usr/bin/env python3
"""Install an OpenCode skill directory from a GitHub tree URL.

This script is deterministic by design:
- It downloads the full directory recursively (not only SKILL.md)
- It validates the installed skill before reporting success
- It writes an installation manifest for auditability
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional, Tuple


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def parse_github_tree_url(url: str) -> Tuple[str, str, str, str]:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("URL must start with http:// or https://")
    if parsed.netloc != "github.com":
        raise ValueError("Only github.com URLs are supported")

    parts = [p for p in parsed.path.split("/") if p]
    # Expected: /owner/repo/tree/branch/path/to/skill
    if len(parts) < 5 or parts[2] != "tree":
        raise ValueError(
            "URL must be a GitHub tree URL like "
            "https://github.com/OWNER/REPO/tree/BRANCH/path/to/skill"
        )

    owner = parts[0]
    repo = parts[1]
    branch = parts[3]
    source_path = "/".join(parts[4:])
    if not source_path:
        raise ValueError("Tree URL must include a skill path")

    return owner, repo, branch, source_path


def build_raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    """Build a raw.githubusercontent.com URL for a file."""
    encoded_path = urllib.parse.quote(path, safe="/")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{encoded_path}"


def try_load_manifest(
    owner: str,
    repo: str,
    branch: str,
    source_path: str,
    token: Optional[str],
) -> Optional[Dict]:
    """Try to load manifest.yaml from the skill directory. Returns None if not found."""
    manifest_path = f"{source_path}/manifest.yaml"
    raw_url = build_raw_url(owner, repo, branch, manifest_path)

    try:
        content = _http_get_bytes(raw_url, token)
        import yaml

        manifest = yaml.safe_load(content.decode("utf-8"))
        if isinstance(manifest, dict):
            return manifest
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except Exception:
        return None
    return None


def get_files_from_manifest(
    manifest: Dict,
    owner: str,
    repo: str,
    branch: str,
    source_path: str,
) -> List[Tuple[str, str]]:
    """Extract file list from manifest. Returns list of (relative_path, download_url)."""
    files: List[Tuple[str, str]] = []

    source = manifest.get("source", {})
    base_url = source.get("base_url")
    manifest_files = source.get("files", [])

    # If manifest has explicit base_url and files, use them
    if base_url and manifest_files:
        for file_path in manifest_files:
            rel_path = pathlib.PurePosixPath(file_path)
            download_url = f"{base_url}/{file_path}"
            files.append((rel_path.as_posix(), download_url))
    else:
        # Fallback: construct URLs from source_path
        for file_path in manifest_files:
            full_path = f"{source_path}/{file_path}"
            download_url = build_raw_url(owner, repo, branch, full_path)
            files.append((file_path, download_url))

    return files


def _http_get_json(url: str, token: Optional[str]) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "opencode-skill-creator-installer",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_latest_commit_sha(
    owner: str,
    repo: str,
    branch: str,
    path: str,
    token: Optional[str],
) -> Optional[str]:
    """Get the latest commit SHA that touched the given path."""
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
        eprint(f"[WARN] Could not fetch commit SHA: {exc}")
    return None


def _http_get_bytes(url: str, token: Optional[str]) -> bytes:
    headers = {
        "User-Agent": "opencode-skill-creator-installer",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def list_github_files_recursive(
    owner: str,
    repo: str,
    branch: str,
    source_path: str,
    token: Optional[str],
) -> List[Tuple[str, str]]:
    """Return list of (relative_path, download_url) under source_path."""

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
            else:
                # Symlinks/submodules can be ignored for this use case.
                eprint(
                    f"[WARN] Skipping unsupported item type '{item_type}': {item_path}"
                )

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
    warnings: List[str] = []

    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        errors.append("Missing SKILL.md")
        return errors

    try:
        text = skill_md.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive
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
            "Frontmatter name has invalid format. Expected regex "
            "^[a-z0-9]+(-[a-z0-9]+)*$"
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

    if warnings:
        for warning in warnings:
            eprint(f"[WARN] {warning}")
    return errors


def compute_install_path(
    scope: str,
    skill_name: str,
    dest_root: Optional[str],
) -> pathlib.Path:
    if dest_root:
        root = pathlib.Path(dest_root).expanduser().resolve()
    elif scope == "global":
        root = pathlib.Path.home() / ".config" / "opencode" / "skills"
    else:
        root = pathlib.Path.cwd() / ".opencode" / "skills"
    return root / skill_name


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Install an OpenCode skill from a GitHub tree URL"
    )
    p.add_argument("--url", required=True, help="GitHub tree URL to skill directory")
    p.add_argument(
        "--scope",
        choices=("global", "local"),
        default="local",
        help="Install scope. Default: local",
    )
    p.add_argument(
        "--skill-name",
        default=None,
        help="Override target skill name (default: basename of URL path or from manifest)",
    )
    p.add_argument(
        "--dest-root",
        default=None,
        help="Optional root directory to install under (final path: <dest-root>/<skill-name>)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing installed skill directory",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Only list files that would be installed",
    )
    p.add_argument(
        "--github-token-env",
        default="GITHUB_TOKEN",
        help="Environment variable name containing GitHub token (optional)",
    )
    p.add_argument(
        "--use-manifest",
        action="store_true",
        default=True,
        help="Use manifest.yaml if present for deterministic installation (default: True)",
    )
    p.add_argument(
        "--no-use-manifest",
        dest="use_manifest",
        action="store_false",
        help="Disable manifest-based installation, always use API discovery",
    )
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        owner, repo, branch, source_path = parse_github_tree_url(args.url)
    except ValueError as exc:
        eprint(f"[ERROR] {exc}")
        return 2

    skill_name = args.skill_name or pathlib.PurePosixPath(source_path).name
    if not NAME_RE.match(skill_name):
        eprint(
            "[ERROR] Invalid skill name. Use --skill-name with a valid value matching "
            "^[a-z0-9]+(-[a-z0-9]+)*$"
        )
        return 2

    token = os.environ.get(args.github_token_env)
    install_path = compute_install_path(args.scope, skill_name, args.dest_root)

    print("== OpenCode Skill Installer ==")
    print(f"Source URL:     {args.url}")
    print(f"Repository:     {owner}/{repo}")
    print(f"Branch:         {branch}")
    print(f"Source path:    {source_path}")
    print(f"Scope:          {args.scope}")
    print(f"Install path:   {install_path}")
    print(f"Skill name:     {skill_name}")

    # Try to use manifest for deterministic installation
    files: List[Tuple[str, str]] = []
    manifest: Optional[Dict] = None
    used_manifest = False

    if args.use_manifest:
        try:
            manifest = try_load_manifest(owner, repo, branch, source_path, token)
            if manifest:
                used_manifest = True
                print("[INFO] Found manifest.yaml - using deterministic installation")
                files = get_files_from_manifest(
                    manifest, owner, repo, branch, source_path
                )

                # Override skill name from manifest if not explicitly provided
                if args.skill_name is None and "skill" in manifest:
                    manifest_name = manifest["skill"].get("name")
                    if manifest_name:
                        skill_name = manifest_name
                        install_path = compute_install_path(
                            args.scope, skill_name, args.dest_root
                        )
                        print(f"[INFO] Using skill name from manifest: {skill_name}")
                        print(f"[INFO] Updated install path: {install_path}")
        except Exception as exc:
            eprint(f"[WARN] Failed to load manifest: {exc}")

    # Fallback to API discovery if no manifest or manifest disabled
    if not files:
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
        eprint(
            "[ERROR] No files found at source path. Is this a valid skill directory?"
        )
        return 1

    commit_sha: Optional[str] = None
    try:
        commit_sha = get_latest_commit_sha(owner, repo, branch, source_path, token)
        if commit_sha:
            print(f"Commit SHA:    {commit_sha[:12]}...")
    except Exception:
        pass

    if used_manifest:
        print(f"Files from manifest: {len(files)}")
    else:
        print(f"Files discovered: {len(files)}")
    for rel, _ in files:
        print(f"  - {rel}")

    if args.dry_run:
        print("Dry run complete. No files were written.")
        return 0

    if install_path.exists():
        if args.force:
            import shutil

            print(f"[INFO] Removing existing path (force): {install_path}")
            shutil.rmtree(install_path)
        else:
            eprint(
                f"[ERROR] Install path already exists: {install_path}\n"
                "Use --force to overwrite."
            )
            return 1

    install_path.mkdir(parents=True, exist_ok=True)

    downloaded: List[str] = []
    for rel, dl_url in files:
        dest_file = install_path / rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            content = _http_get_bytes(dl_url, token)
        except urllib.error.HTTPError as exc:
            eprint(f"[ERROR] Failed to download {rel}: HTTP {exc.code} {exc.reason}")
            return 1
        except urllib.error.URLError as exc:
            eprint(f"[ERROR] Failed to download {rel}: {exc.reason}")
            return 1
        dest_file.write_bytes(content)
        downloaded.append(rel)

    install_manifest = {
        "installed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_url": args.url,
        "source": {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "path": source_path,
        },
        "scope": args.scope,
        "skill_name": skill_name,
        "install_path": str(install_path),
        "files": downloaded,
        "used_manifest": used_manifest,
    }
    if commit_sha:
        install_manifest["commit_sha"] = commit_sha
    (install_path / ".install-manifest.json").write_text(
        json.dumps(install_manifest, indent=2) + "\n", encoding="utf-8"
    )

    errors = validate_skill_dir(install_path, expected_name=skill_name)
    if errors:
        eprint("[ERROR] Installation completed but validation failed:")
        for err in errors:
            eprint(f"  - {err}")
        return 1

    print("Installation succeeded and validation passed.")
    print("Installed files:")
    for rel in downloaded:
        print(f"  - {rel}")
    print(f"Manifest: {install_path / '.install-manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
