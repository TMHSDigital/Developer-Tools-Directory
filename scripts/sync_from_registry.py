#!/usr/bin/env python3
"""Sync derived artifacts from registry.json.

Source of truth: registry.json at the repo root.

Regenerated artifacts:
  - README.md tools table         (between registry:tools:start / :end markers)
  - README.md tool descriptions   (between registry:descriptions:start / :end markers)
  - README.md aggregate stats     (between registry:stats:start / :end markers)
  - docs/index.html embedded JSON (inside <script id="registry-data">)
  - docs/index.html search index  (inside <script id="search-index">)
  - docs/index.html footer version (element id="footerVersion", from VERSION)
  - docs/index.html standards grid (<div class="standards-grid">, from standards/*.md)
  - docs/index.html standards count (element id="standardsCount")
  - docs/search-index.json         (registry-driven; skill/rule/MCP names are
                                    preserved and refreshed out-of-band by
                                    site-template/aggregate_search.py)
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
SEARCH_INDEX_PATH = REPO_ROOT / "docs" / "search-index.json"
VERSION_PATH = REPO_ROOT / "VERSION"
STANDARDS_DIR = REPO_ROOT / "standards"

TYPE_DISPLAY = {
    "cursor-plugin": "Plugin",
    "mcp-server": "MCP Server",
}

STANDARDS_REPO_BLOB = (
    "https://github.com/TMHSDigital/Developer-Tools-Directory/blob/main/standards"
)

# Curated display order and short descriptions for the standards grid. The grid
# is generated from the actual standards/*.md listing (README excluded), so a
# new standard file always gets a card and the count badge tracks the directory.
# A file missing from this map still renders, using its filename and a fallback.
STANDARDS_ORDER = [
    "folder-structure",
    "plugin-manifest",
    "ci-cd",
    "github-pages",
    "commit-conventions",
    "readme-template",
    "agents-template",
    "versioning",
    "release-doc-sync",
    "testing",
    "skills",
    "rules",
    "mcp-server",
    "security",
    "licensing",
    "scope",
    "born-green-contract",
    "lifecycle",
    "writing-style",
]
STANDARDS_META = {
    "folder-structure": ("Folder Structure", "Canonical repository layout for plugins and MCP servers"),
    "plugin-manifest": ("Plugin Manifest", "plugin.json specification and required fields"),
    "ci-cd": ("CI/CD", "GitHub Actions workflows every repo must have"),
    "github-pages": ("GitHub Pages", "Documentation site setup and deployment"),
    "commit-conventions": ("Commit Conventions", "Conventional commits and version bumping rules"),
    "readme-template": ("README Template", "Standard README structure and required sections"),
    "agents-template": ("AGENTS.md Template", "AI agent guidance file structure"),
    "versioning": ("Versioning", "Semver management and automated release flow"),
    "release-doc-sync": ("Release Doc Sync", "Composite action contract for keeping CHANGELOG, CLAUDE, and ROADMAP in sync after a release"),
    "testing": ("Testing", "Test frameworks, minimum coverage bar, and CI wiring"),
    "skills": ("Skills", "SKILL.md structure and frontmatter conventions"),
    "rules": ("Rules", ".mdc structure, globs, and the secrets rule pattern"),
    "mcp-server": ("MCP Server", "Tool naming, runtime, transport, and destructive operation handling"),
    "security": ("Security", "Vulnerability disclosure, secrets handling, and workflow supply chain"),
    "licensing": ("Licensing", "DCO + inbound license grant model"),
    "scope": ("Scope", "What belongs in the directory and what does not"),
    "born-green-contract": ("Born-Green Contract", "Acceptance criterion that any generator must produce a release-ready repo"),
    "lifecycle": ("Lifecycle", "Tool status transitions from experimental to archived"),
    "writing-style": ("Writing Style", "Prose conventions across all repos"),
}

# Search-index entry fields that come from the registry. Skill/rule/MCP-tool
# name arrays are preserved from the existing index (refreshed out-of-band by
# site-template/aggregate_search.py against local repo checkouts).
SEARCH_ARRAY_FIELDS = ("skills", "rules", "mcpTools")


def load_registry(registry_path: Path = REGISTRY_PATH) -> list[dict[str, Any]]:
    with registry_path.open("r", encoding="utf-8") as fh:
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


def list_standards(standards_dir: Path = STANDARDS_DIR) -> list[str]:
    """Return standard slugs present on disk (``*.md`` minus ``README``)."""
    return sorted(
        p.stem for p in standards_dir.glob("*.md") if p.stem.lower() != "readme"
    )


def ordered_standards(present: list[str]) -> list[str]:
    """Curated order first, then any unmapped files alphabetically."""
    known = [s for s in STANDARDS_ORDER if s in present]
    extra = sorted(s for s in present if s not in STANDARDS_ORDER)
    return known + extra


def standard_title_desc(slug: str) -> tuple[str, str]:
    if slug in STANDARDS_META:
        return STANDARDS_META[slug]
    # Fallback for an unmapped standard: parse H1 + first paragraph.
    title = slug.replace("-", " ").title()
    desc = ""
    md = STANDARDS_DIR / f"{slug}.md"
    if md.is_file():
        lines = md.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            if line.startswith("# "):
                title = line[2:].strip()
                for nxt in lines[i + 1:]:
                    s = nxt.strip()
                    if s and not s.startswith("#"):
                        desc = s[:120]
                        break
                break
    return title, desc


def render_standards_grid(present: list[str]) -> str:
    cards = []
    for slug in ordered_standards(present):
        title, desc = standard_title_desc(slug)
        cards.append(
            f'          <a href="{STANDARDS_REPO_BLOB}/{slug}.md" '
            f'class="standard-card" target="_blank" rel="noopener">'
            f"<h3>{title}</h3><p>{desc}</p></a>"
        )
    return "\n" + "\n".join(cards) + "\n        "


def read_version(version_path: Path = VERSION_PATH) -> str:
    return "v" + version_path.read_text(encoding="utf-8").strip()


def build_search_index(
    entries: list[dict[str, Any]], existing: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Registry-driven search index. Basic fields come from the registry;
    skill/rule/MCP-tool name arrays are preserved from *existing* so the
    out-of-band aggregate_search refresh is not clobbered by a sync."""
    index = []
    for e in entries:
        slug = e.get("slug", "")
        prior = existing.get(slug, {})
        entry = {
            "name": e["name"],
            "slug": slug,
            "description": e.get("description", ""),
            "type": e.get("type", ""),
            "topics": e.get("topics", []),
            "npm": e.get("npm", "") or "",
            "url": f"https://github.com/{e['repo']}",
            "homepage": e.get("homepage", ""),
        }
        for field in SEARCH_ARRAY_FIELDS:
            entry[field] = list(prior.get(field, []))
        index.append(entry)
    return index


def render_search_index(index: list[dict[str, Any]]) -> str:
    return json.dumps(index, separators=(",", ":"), ensure_ascii=False)


def load_existing_search_index(
    path: Path = SEARCH_INDEX_PATH,
) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}
    return {e["slug"]: e for e in data if isinstance(e, dict) and e.get("slug")}


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


def replace_script_block(text: str, new_body: str, block_id: str = "registry-data") -> str:
    pattern = re.compile(
        r'(<script id="' + re.escape(block_id) + r'" type="application/json">)(.*?)(</script>)',
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(
            f'Could not find <script id="{block_id}" ...> in docs/index.html'
        )
    return pattern.sub(
        lambda m: m.group(1) + "\n" + new_body + "\n" + m.group(3), text, count=1
    )


def replace_element_text_by_id(text: str, elem_id: str, new_text: str, path: Path) -> str:
    """Replace the inner text of the first element carrying ``id="elem_id"``."""
    pattern = re.compile(
        r'(<[a-zA-Z][\w-]*\b[^>]*\bid="' + re.escape(elem_id) + r'"[^>]*>)(.*?)(</[a-zA-Z][\w-]*>)',
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(f'Element id="{elem_id}" not found in {path}')
    return pattern.sub(lambda m: m.group(1) + new_text + m.group(3), text, count=1)


def replace_standards_grid(text: str, new_body: str, path: Path) -> str:
    pattern = re.compile(
        r'(<div class="standards-grid">)(.*?)(</div>)',
        re.DOTALL,
    )
    if not pattern.search(text):
        raise SystemExit(f'<div class="standards-grid"> not found in {path}')
    return pattern.sub(lambda m: m.group(1) + new_body + m.group(3), text, count=1)


def sync_readme(entries: list[dict[str, Any]], check: bool, root: Path = REPO_ROOT) -> bool:
    readme_path = root / "README.md"
    current = readme_path.read_text(encoding="utf-8")
    new = current
    new = replace_between(
        new,
        "<!-- registry:tools:start -->",
        "<!-- registry:tools:end -->",
        render_readme_tools_table(entries),
        readme_path,
    )
    new = replace_between(
        new,
        "<!-- registry:descriptions:start -->",
        "<!-- registry:descriptions:end -->",
        render_readme_descriptions(entries),
        readme_path,
    )
    new = replace_between(
        new,
        "<!-- registry:stats:start -->",
        "<!-- registry:stats:end -->",
        render_readme_stats(entries),
        readme_path,
    )
    return write_if_changed(readme_path, current, new, check, root)


def sync_claude(entries: list[dict[str, Any]], check: bool, root: Path = REPO_ROOT) -> bool:
    claude_path = root / "CLAUDE.md"
    current = claude_path.read_text(encoding="utf-8")
    new = current
    new = replace_between(
        new,
        "<!-- registry:tools:start -->",
        "<!-- registry:tools:end -->",
        render_claude_tools_table(entries),
        claude_path,
    )
    new = replace_between(
        new,
        "<!-- registry:stats:start -->",
        "<!-- registry:stats:end -->",
        render_claude_stats(entries),
        claude_path,
    )
    return write_if_changed(claude_path, current, new, check, root)


def sync_index(entries: list[dict[str, Any]], check: bool, root: Path = REPO_ROOT) -> bool:
    """Reconcile every registry-derived region of docs/index.html, plus the
    docs/search-index.json companion file.

    The embedded registry block is always required. The search index, footer
    version, and standards grid/count are best-effort: each is rewritten only
    when its anchor (and, for the version/standards, its source) is present, so
    a minimal catalog without a VERSION file or standards/ directory is left
    untouched rather than crashing or being blanked."""
    index_path = root / "docs" / "index.html"
    search_path = root / "docs" / "search-index.json"
    current = index_path.read_text(encoding="utf-8")
    new = replace_script_block(current, render_embedded_registry(entries))

    # Search index: reconcile the companion file and mirror it into the inline
    # fallback block. Skip entirely when the catalog has no inline block.
    search_drift = False
    if '<script id="search-index"' in new:
        existing = load_existing_search_index(search_path)
        search_index = build_search_index(entries, existing)
        new = replace_script_block(new, render_search_index(search_index), "search-index")
        file_current = search_path.read_text(encoding="utf-8") if search_path.is_file() else ""
        file_new = render_search_index(search_index) + "\n"
        search_drift = write_if_changed(search_path, file_current, file_new, check, root)

    # Footer version, sourced from the VERSION file.
    version_path = root / "VERSION"
    if version_path.is_file() and 'id="footerVersion"' in new:
        new = replace_element_text_by_id(
            new, "footerVersion", read_version(version_path), index_path
        )

    # Standards grid and count, sourced from the standards/*.md listing.
    present = list_standards(root / "standards")
    if present and 'class="standards-grid"' in new:
        new = replace_standards_grid(new, render_standards_grid(present), index_path)
        if 'id="standardsCount"' in new:
            new = replace_element_text_by_id(
                new, "standardsCount", str(len(present)), index_path
            )

    html_drift = write_if_changed(index_path, current, new, check, root)
    return html_drift or search_drift


def write_if_changed(
    path: Path, current: str, new: str, check: bool, root: Path = REPO_ROOT
) -> bool:
    if current == new:
        return False
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    if check:
        print(f"DRIFT: {rel} is out of sync with registry.json", file=sys.stderr)
        return True
    path.write_text(new, encoding="utf-8")
    print(f"updated: {rel}")
    return True


def sync_all(root: Path = REPO_ROOT, check: bool = False) -> bool:
    """Regenerate (or check) every derived artifact under ``root`` from
    ``root/registry.json``. Returns True if anything drifted (check mode)
    or changed (write mode). Used by both the CLI and the scaffold's
    auto-registration so there is a single sync code path."""
    entries = load_registry(root / "registry.json")
    drift = False
    drift |= sync_readme(entries, check, root)
    drift |= sync_claude(entries, check, root)
    drift |= sync_index(entries, check, root)
    return drift


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

    drift = sync_all(REPO_ROOT, args.check)

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
