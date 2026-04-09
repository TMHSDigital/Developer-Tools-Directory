#!/usr/bin/env python3
"""Build a full-text search index for the directory catalog site.

Reads registry.json and, for each tool with a local checkout, extracts
skill names, rule names, and MCP tool names using the parsers from
build_site.py. Outputs a JSON search index to docs/search-index.json.
"""

import argparse
import json
import sys
from pathlib import Path

from build_site import load_json, load_mcp_tools, parse_rules, parse_skills


def build_index(registry_path: Path, repo_dirs: dict[str, Path]) -> list[dict]:
    """Build search index entries from registry + local repo data."""
    registry = load_json(registry_path)
    index = []

    for tool in registry:
        slug = tool.get("slug", "")
        entry = {
            "name": tool["name"],
            "slug": slug,
            "description": tool.get("description", ""),
            "type": tool.get("type", ""),
            "topics": tool.get("topics", []),
            "npm": tool.get("npm", ""),
            "url": f"https://github.com/{tool['repo']}",
            "homepage": tool.get("homepage", ""),
            "skills": [],
            "rules": [],
            "mcpTools": [],
        }

        repo_root = repo_dirs.get(slug)
        if repo_root and repo_root.is_dir():
            skills = parse_skills(repo_root)
            entry["skills"] = [s["name"] for s in skills]

            rules = parse_rules(repo_root)
            entry["rules"] = [r["name"] for r in rules]

            mcp_tools = load_mcp_tools(repo_root)
            entry["mcpTools"] = [t["name"] for t in mcp_tools]

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
    args = parser.parse_args()

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

    index = build_index(args.registry, repo_dirs)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(index, f, separators=(",", ":"))

    total_skills = sum(len(e["skills"]) for e in index)
    total_rules = sum(len(e["rules"]) for e in index)
    total_mcp = sum(len(e["mcpTools"]) for e in index)
    print(f"Wrote {args.out} ({len(index)} tools, {total_skills} skills, {total_rules} rules, {total_mcp} MCP tools)")


if __name__ == "__main__":
    main()
