#!/usr/bin/env python3
"""
Scaffold generator for TMHSDigital developer tool repositories.

Generates a fully standards-compliant repository with all required files,
workflows, manifests, and documentation skeleton.
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("Error: Jinja2 is required. Install it with: pip install Jinja2")
    sys.exit(1)


TEMPLATES_DIR = Path(__file__).parent / "templates"

LICENSE_FILES = {
    "cc-by-nc-nd-4.0": "CC-BY-NC-ND-4.0",
    "mit": "MIT",
    "apache-2.0": "Apache-2.0",
}

SPDX = {
    "cc-by-nc-nd-4.0": "CC-BY-NC-ND-4.0",
    "mit": "MIT",
    "apache-2.0": "Apache-2.0",
}


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scaffold a new TMHSDigital developer tool repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create-tool.py --name "Unreal Developer Tools" --description "Cursor plugin for Unreal Engine"
  python create-tool.py --name "AWS MCP Server" --type mcp-server --mcp-server
  python create-tool.py --name "K8s Developer Tools" --mcp-server --skills 5 --rules 3
        """,
    )
    parser.add_argument("--name", required=True, help="Display name (e.g., 'Unreal Developer Tools')")
    parser.add_argument("--slug", help="Kebab-case identifier (auto-derived from name if omitted)")
    parser.add_argument("--description", required=True, help="One-line description")
    parser.add_argument(
        "--type",
        choices=["cursor-plugin", "mcp-server"],
        default="cursor-plugin",
        help="Repository type (default: cursor-plugin)",
    )
    parser.add_argument("--mcp-server", action="store_true", help="Include MCP server scaffold")
    parser.add_argument("--skills", type=int, default=0, help="Number of placeholder skill directories to create")
    parser.add_argument("--rules", type=int, default=0, help="Number of placeholder rule files to create")
    parser.add_argument(
        "--license",
        choices=list(LICENSE_FILES.keys()),
        default="cc-by-nc-nd-4.0",
        help="License for the generated repo (default: cc-by-nc-nd-4.0)",
    )
    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--author-name",
        default="TMHSDigital",
        help="Author name for plugin.json (default: TMHSDigital)",
    )
    parser.add_argument(
        "--author-email",
        default="contact@tmhospitalitystrategies.com",
        help="Author email for plugin.json",
    )
    return parser.parse_args()


def render_template(env, template_name: str, context: dict) -> str:
    tmpl = env.get_template(template_name)
    return tmpl.render(**context)


def write_file(base: Path, rel_path: str, content: str):
    full = base / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    print(f"  created {rel_path}")


def main():
    args = parse_args()

    slug = args.slug or slugify(args.name)
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", slug):
        print(f"Error: slug '{slug}' is not valid kebab-case")
        sys.exit(1)

    output_dir = Path(args.output) / slug
    if output_dir.exists():
        print(f"Error: output directory already exists: {output_dir}")
        sys.exit(1)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
        lstrip_blocks=True,
        trim_blocks=True,
    )

    skill_names = [f"skill-{i + 1}" for i in range(args.skills)]
    rule_names = [f"rule-{i + 1}" for i in range(args.rules)]

    ctx = {
        "name": args.name,
        "slug": slug,
        "description": args.description,
        "type": args.type,
        "has_mcp": args.mcp_server,
        "skills": skill_names,
        "rules": rule_names,
        "skill_count": args.skills,
        "rule_count": args.rules,
        "license_spdx": SPDX[args.license],
        "license_key": args.license,
        "author_name": args.author_name,
        "author_email": args.author_email,
        "repo_owner": "TMHSDigital",
        "repo_name": slug,
    }

    print(f"\nScaffolding '{args.name}' ({slug}) into {output_dir}\n")

    # Plugin manifest
    if args.type == "cursor-plugin":
        write_file(output_dir, ".cursor-plugin/plugin.json", render_template(env, "plugin.json.j2", ctx))

    # GitHub workflows
    write_file(output_dir, ".github/workflows/validate.yml", render_template(env, "validate.yml.j2", ctx))
    write_file(output_dir, ".github/workflows/release.yml", render_template(env, "release.yml.j2", ctx))
    write_file(output_dir, ".github/workflows/pages.yml", render_template(env, "pages.yml.j2", ctx))
    write_file(output_dir, ".github/workflows/stale.yml", render_template(env, "stale.yml.j2", ctx))

    # Documentation files
    write_file(output_dir, "README.md", render_template(env, "README.md.j2", ctx))
    write_file(output_dir, "AGENTS.md", render_template(env, "AGENTS.md.j2", ctx))
    write_file(output_dir, "CLAUDE.md", render_template(env, "CLAUDE.md.j2", ctx))
    write_file(output_dir, "CONTRIBUTING.md", render_template(env, "CONTRIBUTING.md.j2", ctx))
    write_file(output_dir, "CHANGELOG.md", render_template(env, "CHANGELOG.md.j2", ctx))
    write_file(output_dir, "CODE_OF_CONDUCT.md", render_template(env, "CODE_OF_CONDUCT.md.j2", ctx))
    write_file(output_dir, "SECURITY.md", render_template(env, "SECURITY.md.j2", ctx))
    write_file(output_dir, "ROADMAP.md", render_template(env, "ROADMAP.md.j2", ctx))
    write_file(output_dir, "LICENSE", render_template(env, "LICENSE.j2", ctx))

    # Cursor config
    write_file(output_dir, ".cursorrules", render_template(env, "cursorrules.j2", ctx))
    write_file(output_dir, ".gitignore", render_template(env, "gitignore.j2", ctx))

    # GitHub Pages docs site
    write_file(output_dir, "docs/index.html", render_template(env, "index.html.j2", ctx))

    # Assets placeholder
    (output_dir / "assets").mkdir(parents=True, exist_ok=True)
    (output_dir / "assets" / ".gitkeep").touch()
    print("  created assets/.gitkeep")

    # Skills
    for skill in skill_names:
        skill_content = f"""---
title: {skill.replace('-', ' ').title()}
description: TODO - describe this skill
globs: ["**/*"]
alwaysApply: false
---

# {skill.replace('-', ' ').title()}

TODO: Add skill content here.
"""
        write_file(output_dir, f"skills/{skill}/SKILL.md", skill_content)

    # Rules
    for rule in rule_names:
        rule_content = f"""---
description: TODO - describe this rule
globs: ["**/*"]
alwaysApply: false
---

# {rule.replace('-', ' ').title()}

TODO: Add rule content here.
"""
        write_file(output_dir, f"rules/{rule}.mdc", rule_content)

    # Tests placeholder
    (output_dir / "tests").mkdir(parents=True, exist_ok=True)
    (output_dir / "tests" / ".gitkeep").touch()
    print("  created tests/.gitkeep")

    # MCP server scaffold
    if args.mcp_server:
        write_file(
            output_dir,
            "mcp-server/server.py",
            render_template(env, "mcp-server/server.py.j2", ctx),
        )
        write_file(
            output_dir,
            "mcp-server/requirements.txt",
            render_template(env, "mcp-server/requirements.txt.j2", ctx),
        )
        (output_dir / "mcp-server" / "tools").mkdir(parents=True, exist_ok=True)
        (output_dir / "mcp-server" / "tools" / ".gitkeep").touch()
        print("  created mcp-server/tools/.gitkeep")
        (output_dir / "mcp-server" / "data").mkdir(parents=True, exist_ok=True)
        (output_dir / "mcp-server" / "data" / ".gitkeep").touch()
        print("  created mcp-server/data/.gitkeep")

        write_file(
            output_dir,
            ".cursor/mcp.json",
            render_template(env, "mcp-server/mcp.json.j2", ctx),
        )

    print(f"\nDone! Repository scaffolded at: {output_dir}")
    print(f"\nNext steps:")
    print(f"  1. cd {output_dir}")
    print(f"  2. git init && git add -A && git commit -m 'feat: initial scaffold'")
    print(f"  3. Create GitHub repo: gh repo create TMHSDigital/{slug} --public --source .")
    print(f"  4. Enable GitHub Pages in Settings > Pages > Source: GitHub Actions")
    print(f"  5. Start adding skills, rules, and MCP tools!")


if __name__ == "__main__":
    main()
