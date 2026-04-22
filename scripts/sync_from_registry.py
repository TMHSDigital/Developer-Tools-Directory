#!/usr/bin/env python3
"""Sync derived artifacts from registry.json.

Source of truth: registry.json at the repo root.

Regenerated artifacts:
  - README.md tools table         (between registry:tools:start / :end markers)
  - README.md tool descriptions   (between registry:descriptions:start / :end markers)
  - README.md aggregate stats     (between registry:stats:start / :end markers)
  - docs/index.html embedded JSON (inside <script id="registry-data">)
  - CLAUDE.md cataloged tools     (between registry:tools:start / :end markers)
  - CLAUDE.md totals              (between registry:stats:start / :end markers)

Usage:
  python scripts/sync_from_registry.py           # rewrite artifacts in place
  python scripts/sync_from_registry.py --check   # exit 1 if anything would change
  python scripts/sync_from_registry.py --about   # print the gh repo edit command only

No third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "registry.json"
README_PATH = REPO_ROOT / "README.md"
CLAUDE_PATH = REPO_ROOT / "CLAUDE.md"
INDEX_PATH = REPO_ROOT / "docs" / "index.html"

TYPE_DISPLAY = {
    "cursor-plugin": "Plugin",
    "mcp-server": "MCP Server",
}


def load_registry() -> list[dict[str, Any]]:
    with REGISTRY_PATH.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise SystemExit("registry.json must be a JSON array")
    return data


def fmt_cell(value: Any) -> str:
    if value is None or value == "":
        return "-"
    return str(value)


def render_readme_tools_table(entries: list[dict[str, Any]]) -> str:
    lines = [
        "| Tool | Type | Skills | Rules | MCP&nbsp;Tools | Links |",
        "|:-----|:-----|-------:|------:|------:|:------|",
    ]
    for e in entries:
        type_display = TYPE_DISPLAY.get(e["type"], e["type"])
        repo_url = f"https://github.com/{e['repo']}"
        homepage = e.get("homepage") or ""
        npm = e.get("npm") or ""
        skills = fmt_cell(e.get("skills")) if e["type"] != "mcp-server" else "-"
        rules = fmt_cell(e.get("rules")) if e["type"] != "mcp-server" else "-"
        mcp = fmt_cell(e.get("mcpTools"))
        links = [
            f"[![Repo](https://img.shields.io/badge/repo-blue?logo=github)]({repo_url})"
        ]
        pages_type = e.get("pagesType", "static")
        if homepage and pages_type != "none":
            links.append(
                f"[![Docs](https://img.shields.io/badge/docs-7c3aed)]({homepage})"
            )
        if npm:
            links.append(
                f"[![npm](https://img.shields.io/badge/npm-cb3837?logo=npm&logoColor=white)](https://www.npmjs.com/package/{npm})"
            )
        lines.append(
            f"| **{e['name']}** | {type_display} | {skills} | {rules} | {mcp} | {' '.join(links)} |"
        )
    return "\n".join(lines) + "\n"


def render_readme_descriptions(entries: list[dict[str, Any]]) -> str:
    lines = [
        "| Tool | Description |",
        "|:-----|:------------|",
    ]
    for e in entries:
        desc = e["description"].replace("|", "\\|")
        lines.append(f"| **{e['name']}** | {desc} |")
    return "\n".join(lines) + "\n"


def aggregate_stats(entries: list[dict[str, Any]]) -> dict[str, int]:
    counted_statuses = {"active", "maintenance"}
    visible = [e for e in entries if e.get("status", "active") in counted_statuses]
    return {
        "repos": len(visible),
        "skills": sum(int(e.get("skills") or 0) for e in visible),
        "rules": sum(int(e.get("rules") or 0) for e in visible),
        "mcpTools": sum(int(e.get("mcpTools") or 0) for e in visible),
    }


def render_readme_stats(entries: list[dict[str, Any]]) -> str:
    s = aggregate_stats(entries)
    return (
        "<p align=\"center\">\n"
        f" {s['repos']} repos &nbsp;&bull;&nbsp; {s['skills']} skills "
        f"&nbsp;&bull;&nbsp; {s['rules']} rules "
        f"&nbsp;&bull;&nbsp; {s['mcpTools']} MCP tools\n"
        "</p>\n"
    )


def render_claude_tools_table(entries: list[dict[str, Any]]) -> str:
    lines = [
        "| Tool | Type | Skills | Rules | MCP Tools |",
        "|------|------|-------:|------:|----------:|",
    ]
    for e in entries:
        type_display = TYPE_DISPLAY.get(e["type"], e["type"])
        skills = e.get("skills") if e["type"] != "mcp-server" else 0
        rules = e.get("rules") if e["type"] != "mcp-server" else 0
        lines.append(
            f"| {e['name']} | {type_display} | {skills or 0} | {rules or 0} | {e.get('mcpTools', 0)} |"
        )
    return "\n".join(lines) + "\n"


def render_claude_stats(entries: list[dict[str, Any]]) -> str:
    s = aggregate_stats(entries)
    return (
        f"**Totals:** {s['skills']} skills, {s['rules']} rules, "
        f"{s['mcpTools']} MCP tools across {s['repos']} repos\n"
    )


def render_embedded_registry(entries: list[dict[str, Any]]) -> str:
    return json.dumps(entries, separators=(",", ":"), ensure_ascii=False)


def replace_between(
    text: str, start_marker: str, end_marker: str, new_body: str, path: Path
) -> str:
    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(
            f"Markers not found in {path}: '{start_marker}' / '{end_marker}'"
        )
    replacement = f"{start_marker}\n{new_body.rstrip()}\n{end_marker}"
    return pattern.sub(replacement, text, count=1)


def replace_script_block(text: str, new_body: str) -> str:
    pattern = re.compile(
        r'(<script id="registry-data" type="application/json">)(.*?)(</script>)',
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(
            "Could not find <script id=\"registry-data\" ...> in docs/index.html"
        )
    replacement = r"\g<1>\n" + new_body + r"\n\g<3>"
    return pattern.sub(replacement, text, count=1)


def sync_readme(entries: list[dict[str, Any]], check: bool) -> bool:
    current = README_PATH.read_text(encoding="utf-8")
    new = current
    new = replace_between(
        new,
        "<!-- registry:tools:start -->",
        "<!-- registry:tools:end -->",
        render_readme_tools_table(entries),
        README_PATH,
    )
    new = replace_between(
        new,
        "<!-- registry:descriptions:start -->",
        "<!-- registry:descriptions:end -->",
        render_readme_descriptions(entries),
        README_PATH,
    )
    new = replace_between(
        new,
        "<!-- registry:stats:start -->",
        "<!-- registry:stats:end -->",
        render_readme_stats(entries),
        README_PATH,
    )
    return write_if_changed(README_PATH, current, new, check)


def sync_claude(entries: list[dict[str, Any]], check: bool) -> bool:
    current = CLAUDE_PATH.read_text(encoding="utf-8")
    new = current
    new = replace_between(
        new,
        "<!-- registry:tools:start -->",
        "<!-- registry:tools:end -->",
        render_claude_tools_table(entries),
        CLAUDE_PATH,
    )
    new = replace_between(
        new,
        "<!-- registry:stats:start -->",
        "<!-- registry:stats:end -->",
        render_claude_stats(entries),
        CLAUDE_PATH,
    )
    return write_if_changed(CLAUDE_PATH, current, new, check)


def sync_index(entries: list[dict[str, Any]], check: bool) -> bool:
    current = INDEX_PATH.read_text(encoding="utf-8")
    new = replace_script_block(current, render_embedded_registry(entries))
    return write_if_changed(INDEX_PATH, current, new, check)


def write_if_changed(path: Path, current: str, new: str, check: bool) -> bool:
    if current == new:
        return False
    rel = path.relative_to(REPO_ROOT)
    if check:
        print(f"DRIFT: {rel} is out of sync with registry.json", file=sys.stderr)
        return True
    path.write_text(new, encoding="utf-8")
    print(f"updated: {rel}")
    return True


def about_command(entries: list[dict[str, Any]]) -> str:
    s = aggregate_stats(entries)
    description = (
        f"Centralized catalog, standards, and scaffolding for {s['repos']} TMHSDigital "
        f"developer tools - {s['skills']} skills, {s['rules']} rules, "
        f"{s['mcpTools']} MCP tools"
    )
    topics = sorted(
        {"cursor-plugin", "mcp-server", "developer-tools", "scaffold", "standards"}
    )
    topic_args = " ".join(f'--add-topic {t}' for t in topics)
    return (
        "gh repo edit TMHSDigital/Developer-Tools-Directory "
        f'--description "{description}" '
        '--homepage "https://tmhsdigital.github.io/Developer-Tools-Directory/" '
        f"{topic_args}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any artifact is out of sync; do not write files.",
    )
    parser.add_argument(
        "--about",
        action="store_true",
        help="Print the gh repo edit command to update the GitHub About section and exit.",
    )
    args = parser.parse_args()

    entries = load_registry()

    if args.about:
        print(about_command(entries))
        return 0

    drift = False
    drift |= sync_readme(entries, args.check)
    drift |= sync_claude(entries, args.check)
    drift |= sync_index(entries, args.check)

    if args.check:
        if drift:
            print(
                "Run: python scripts/sync_from_registry.py",
                file=sys.stderr,
            )
            return 1
        print("registry sync: ok")
        return 0

    if not drift:
        print("registry sync: no changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
