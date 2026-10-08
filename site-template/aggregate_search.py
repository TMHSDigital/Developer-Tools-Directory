#!/usr/bin/env python3
"""Build a full-text search index for the directory catalog site.

Reads registry.json and, for each tool with a local checkout, extracts
skill names, rule names, and MCP tool names using the parsers from
build_site.py. Outputs a JSON search index to docs/search-index.json.
"""

import argparse
import contextlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from build_site import load_json, load_mcp_tools, parse_rules, parse_skills

import re

BACKSLASH = chr(92)

# Fallback extraction for repos that ship no mcp-tools.json manifest: read
# tool names straight from the server source. Python FastMCP servers use
# ``@mcp.tool()`` on a function; TypeScript servers call
# ``server.tool("name", ...)`` or ``server.registerTool("name", ...)``.
_PY_TOOL_RE = re.compile(
    r"@\w+\.tool\((?P<args>[^)]*)\)\s*(?:async\s+)?def\s+(?P<fn>\w+)"
)
_PY_NAME_ARG_RE = re.compile(r"name\s*=\s*['\"]([^'\"]+)['\"]")
_TS_TOOL_RE = re.compile(r"\.(?:registerTool|tool)\(\s*['\"]([A-Za-z0-9_.-]+)['\"]")
_SKIP_DIRS = {"node_modules", "dist", "build", ".git", "tests", "test", "__tests__"}


def _iter_sources(root: Path, suffix: str):
    for path in root.rglob(f"*{suffix}"):
        if _SKIP_DIRS.intersection(part.lower() for part in path.relative_to(root).parts):
            continue
        if path.name.endswith((".test.ts", ".spec.ts", ".d.ts")):
            continue
        yield path


def scan_source_tool_names(repo_root: Path) -> list[str]:
    """Best-effort tool names from server source, sorted and de-duplicated."""
    names: set[str] = set()
    py_root = repo_root / "mcp-server"
    if py_root.is_dir():
        for path in _iter_sources(py_root, ".py"):
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in _PY_TOOL_RE.finditer(text):
                explicit = _PY_NAME_ARG_RE.search(m.group("args"))
                names.add(explicit.group(1) if explicit else m.group("fn"))
    for ts_root in (repo_root / "src", repo_root / "mcp-server" / "src"):
        if ts_root.is_dir():
            for path in _iter_sources(ts_root, ".ts"):
                text = path.read_text(encoding="utf-8", errors="replace")
                names.update(_TS_TOOL_RE.findall(text))
    return sorted(names)


def build_index(
    registry_path: Path,
    repo_dirs: dict[str, Path],
    existing: dict[str, dict] | None = None,
) -> list[dict]:
    """Build search index entries from registry + local repo data.

    Basic fields (name, description, type, topics, npm, url, homepage) always
    come from the registry. Skill/rule/MCP-tool names come from a local repo
    checkout when one is available; otherwise they are preserved from
    *existing* (a prior index keyed by slug) so refreshing without a full
    fleet checkout does not discard data that was scanned earlier.
    """
    registry = load_json(registry_path)
    existing = existing or {}
    index = []

    for tool in registry:
        slug = tool.get("slug", "")
        prior = existing.get(slug, {})
        entry = {
            "name": tool["name"],
            "slug": slug,
            "description": tool.get("description", ""),
            "type": tool.get("type", ""),
            "topics": tool.get("topics", []),
            "npm": tool.get("npm", ""),
            "url": f"https://github.com/{tool['repo']}",
            "homepage": tool.get("homepage", ""),
            "skills": list(prior.get("skills", [])),
            "rules": list(prior.get("rules", [])),
            "mcpTools": list(prior.get("mcpTools", [])),
        }

        repo_root = repo_dirs.get(slug)
        if repo_root and repo_root.is_dir():
            skills = parse_skills(repo_root)
            entry["skills"] = [s["name"] for s in skills]

            rules = parse_rules(repo_root)
            entry["rules"] = [r["name"] for r in rules]

            mcp_tools = load_mcp_tools(repo_root)
            if mcp_tools:
                entry["mcpTools"] = [t["name"] for t in mcp_tools]
            else:
                entry["mcpTools"] = scan_source_tool_names(repo_root)

        index.append(entry)

    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path(__file__).parent.parent / "registry.json",
        help="Path to registry.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).parent.parent / "docs" / "search-index.json",
        help="Output path for the search index JSON",
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        action="append",
        default=[],
        help="Path to a local tool repo checkout (can be repeated)",
    )
    parser.add_argument(
        "--scan",
        type=Path,
        help="Parent directory to auto-discover repo checkouts (siblings of the directory repo)",
    )
    parser.add_argument(
        "--clone",
        action="store_true",
        help=(
            "Shallow-clone every registry repo not found via --repo-dir/--scan "
            "into a temp directory (public repos, no token). Gives a complete, "
            "current index without a local fleet checkout."
        ),
    )
    args = parser.parse_args()
    with contextlib.ExitStack() as stack:
        _run(args, stack)


def _shallow_clone(repo: str, dest: Path) -> bool:
    """Clone ``owner/name`` at depth 1. Returns False (with a warning) on
    failure so one unreachable repo does not abort the whole index."""
    result = subprocess.run(
        ["git", "clone", "--quiet", "--depth", "1", f"https://github.com/{repo}.git", str(dest)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(f"warning: clone failed for {repo}: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def _run(args: argparse.Namespace, stack: contextlib.ExitStack) -> None:

    repo_dirs: dict[str, Path] = {}

    for d in args.repo_dir:
        resolved = d.resolve()
        if resolved.is_dir():
            slug = resolved.name.lower()
            repo_dirs[slug] = resolved

    if args.scan and args.scan.is_dir():
        registry = load_json(args.registry)
        repo_names = {}
        for tool in registry:
            repo_name = tool["repo"].split("/")[-1]
            repo_names[repo_name.lower()] = tool["slug"]

        for child in args.scan.iterdir():
            if child.is_dir():
                slug = repo_names.get(child.name.lower())
                if slug and slug not in repo_dirs:
                    repo_dirs[slug] = child

    if args.clone:
        tmp_root = Path(tempfile.mkdtemp(prefix="dtd-search-"))
        stack.callback(shutil.rmtree, tmp_root, True)
        for tool in load_json(args.registry):
            slug = tool["slug"]
            if slug in repo_dirs:
                continue
            dest = tmp_root / slug
            if _shallow_clone(tool["repo"], dest):
                repo_dirs[slug] = dest

    existing: dict[str, dict] = {}
    if args.out.is_file():
        try:
            for e in load_json(args.out):
                if isinstance(e, dict) and e.get("slug"):
                    existing[e["slug"]] = e
        except (ValueError, OSError):
            existing = {}

    index = build_index(args.registry, repo_dirs, existing)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Same serialization as scripts/sync_from_registry.py (script-safe JSON
    # plus a trailing newline) so a refresh does not trip the sync check.
    raw = json.dumps(index, separators=(",", ":"), ensure_ascii=False)
    for ch, esc in (("<", "u003c"), (">", "u003e"), ("&", "u0026")):
        raw = raw.replace(ch, BACKSLASH + esc)
    args.out.write_text(raw + "\n", encoding="utf-8", newline="\n")

    total_skills = sum(len(e["skills"]) for e in index)
    total_rules = sum(len(e["rules"]) for e in index)
    total_mcp = sum(len(e["mcpTools"]) for e in index)
    print(f"Wrote {args.out} ({len(index)} tools, {total_skills} skills, {total_rules} rules, {total_mcp} MCP tools)")


if __name__ == "__main__":
    main()
