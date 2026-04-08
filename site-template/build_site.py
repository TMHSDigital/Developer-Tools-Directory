#!/usr/bin/env python3
"""Build a GitHub Pages site from plugin metadata and a Jinja2 template.

Reads .cursor-plugin/plugin.json, site.json, skills/, rules/, and
mcp-tools.json from a tool repository and renders a single-page site.
"""

import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def load_json(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter and return (metadata_dict, body_after_frontmatter)."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return {}, text

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, text

    meta: dict[str, str] = {}
    for line in lines[1:end_idx]:
        if ":" in line and not line.strip().startswith("-"):
            key, _, val = line.partition(":")
            meta[key.strip().lower()] = val.strip()

    body = "".join(lines[end_idx + 1:])
    return meta, body


def parse_skills(repo_root: Path) -> list[dict]:
    skills_dir = repo_root / "skills"
    if not skills_dir.is_dir():
        return []

    results = []
    for skill_dir in sorted(skills_dir.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            continue

        text = skill_file.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(text)

        name = meta.get("name", "").replace("-", " ").replace("_", " ").title()
        if not name:
            name = skill_dir.name.replace("-", " ").replace("_", " ").title()
        description = meta.get("description", "")[:200]

        if not description:
            for line in body.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                description = stripped[:200]
                break

        if not name or name == skill_dir.name.replace("-", " ").replace("_", " ").title():
            for line in body.splitlines():
                stripped = line.strip()
                if re.match(r"^#\s+\S", stripped):
                    name = re.sub(r"^#+\s*", "", stripped)
                    break

        results.append({
            "name": name,
            "description": description,
            "category": skill_dir.name,
        })

    return results


def parse_rules(repo_root: Path) -> list[dict]:
    rules_dir = repo_root / "rules"
    if not rules_dir.is_dir():
        return []

    results = []
    for rule_file in sorted(rules_dir.iterdir()):
        if rule_file.suffix not in (".mdc", ".md"):
            continue

        text = rule_file.read_text(encoding="utf-8", errors="replace")
        lines = text.strip().splitlines()

        name = rule_file.stem.replace("-", " ").replace("_", " ").title()
        description = ""
        scope = ""

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("---"):
                continue
            if ":" in stripped and not description:
                key, _, val = stripped.partition(":")
                key_lower = key.strip().lower()
                if key_lower == "description":
                    description = val.strip()[:200]
                elif key_lower in ("globs", "scope"):
                    scope = val.strip()
                continue
            if stripped and not description:
                description = stripped[:200]

        results.append({
            "name": name,
            "description": description,
            "scope": scope,
        })

    return results


def load_mcp_tools(repo_root: Path) -> list[dict]:
    mcp_file = repo_root / "mcp-tools.json"
    if not mcp_file.is_file():
        return []
    data = load_json(mcp_file)
    if isinstance(data, list):
        return data
    return []


def group_by_category(items: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for item in items:
        cat = item.get("category", "General") or "General"
        groups.setdefault(cat, []).append(item)
    return dict(sorted(groups.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        required=True,
        help="Path to the checked-out tool repository",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs"),
        help="Output directory (default: docs)",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    out_dir = args.out.resolve()
    template_dir = Path(__file__).parent.resolve()

    plugin_path = repo_root / ".cursor-plugin" / "plugin.json"
    if not plugin_path.is_file():
        print(f"ERROR: {plugin_path} not found", file=sys.stderr)
        sys.exit(1)

    site_path = repo_root / "site.json"
    if not site_path.is_file():
        print(f"ERROR: {site_path} not found", file=sys.stderr)
        sys.exit(1)

    plugin = load_json(plugin_path)
    site = load_json(site_path)

    skills = parse_skills(repo_root)
    rules = parse_rules(repo_root)
    mcp_tools = load_mcp_tools(repo_root)
    mcp_grouped = group_by_category(mcp_tools)

    context = {
        "plugin": plugin,
        "site": site,
        "skills": skills,
        "skill_count": len(skills),
        "rules": rules,
        "rule_count": len(rules),
        "mcp_tools": mcp_tools,
        "mcp_tool_count": len(mcp_tools),
        "mcp_grouped": mcp_grouped,
        "build_date": datetime.date.today().isoformat(),
    }

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
        keep_trailing_newline=True,
    )
    template = env.get_template("template.html.j2")
    html = template.render(**context)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Wrote {out_dir / 'index.html'}")

    fonts_src = template_dir / "fonts"
    fonts_dst = out_dir / "fonts"
    if fonts_src.is_dir():
        if fonts_dst.exists():
            shutil.rmtree(fonts_dst)
        shutil.copytree(fonts_src, fonts_dst)
        print(f"Copied fonts to {fonts_dst}")

    assets_src = repo_root / "assets"
    assets_dst = out_dir / "assets"
    if assets_src.is_dir():
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)
        print(f"Copied assets to {assets_dst}")

    print("Done.")


if __name__ == "__main__":
    main()
