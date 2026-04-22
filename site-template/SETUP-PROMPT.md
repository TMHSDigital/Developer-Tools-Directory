# Unified GitHub Pages - Site Template Reference

> Full documentation for the shared site template system that powers GitHub Pages for all TMHSDigital tool repositories.

## Overview

The site template lives in `Developer-Tools-Directory/site-template/` and is consumed by each tool repo's `pages.yml` workflow at deploy time. A single `build_site.py` script reads metadata from the tool repo and renders `template.html.j2` into a static `docs/index.html`.

---

## Quick Start (Setup Prompt)

Copy the prompt below into Cursor in any tool repo that needs a GitHub Pages site:

```
You are setting up this repo's GitHub Pages site to use the unified auto-sync template from the Developer-Tools-Directory repo (https://github.com/TMHSDigital/Developer-Tools-Directory).

The template system works like this:
- A Python build script (site-template/build_site.py) in Developer-Tools-Directory reads data from THIS repo and generates docs/index.html
- It reads: .cursor-plugin/plugin.json, site.json, skills/*/SKILL.md, rules/*.mdc, and mcp-tools.json
- The pages.yml workflow clones Developer-Tools-Directory at deploy time, runs the build, and deploys docs/

Your tasks:

1. Create `site.json` in the repo root (see schema below)
2. Create `mcp-tools.json` in the repo root (see format below)
3. Update `.github/workflows/pages.yml` to clone the template and run build_site.py
4. Verify .cursor-plugin/plugin.json has all required fields
5. Commit and push with message: feat: switch to unified auto-sync GitHub Pages template

Do NOT modify existing skills/, rules/, or .cursor-plugin/plugin.json content.
```

---

## site.json Schema

The `site.json` file in each tool repo root controls branding, content, and layout.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `accent` | string | no | `#7c3aed` | Primary accent color (hex) |
| `accentLight` | string | no | `#a78bfa` | Lighter accent variant for dark backgrounds |
| `heroGradientFrom` | string | no | `#0d1117` | Hero section gradient start color |
| `heroGradientTo` | string | no | `#161b22` | Hero section gradient end color |
| `favicon` | string | no | - | Path to favicon (relative to docs/) |
| `ogImage` | string | no | - | Path to OG image for social previews |
| `installSteps` | string[] | no | - | Ordered list of install instructions (HTML allowed) |
| `links.github` | string | no | from plugin.json | GitHub repo URL |
| `links.npm` | string | no | - | npm package page URL |
| `quickStart` | object | no | - | Quick-start snippet shown in hero |
| `quickStart.title` | string | no | `Get started` | Title above the code block |
| `quickStart.command` | string | yes (if quickStart) | - | Command(s) to display |
| `compatibility` | object | no | - | Compatibility badges shown as pills |
| `compatibility.cursor` | string | no | - | Cursor version requirement |
| `compatibility.os` | string[] | no | - | Supported operating systems |
| `compatibility.node` | string | no | - | Node.js version requirement |
| `compatibility.claude` | string | no | - | Claude Code compatibility note |
| `relatedTools` | array | no | - | Links to related tools |
| `relatedTools[].name` | string | yes | - | Tool display name |
| `relatedTools[].url` | string | yes | - | URL to the tool |
| `relatedTools[].description` | string | no | - | Short description |

### Example site.json

```json
{
  "accent": "#2563eb",
  "accentLight": "#60a5fa",
  "heroGradientFrom": "#0d1117",
  "heroGradientTo": "#161b22",
  "favicon": "assets/logo.png",
  "ogImage": "assets/logo.png",
  "installSteps": [
    "Clone the repository: <code>git clone https://github.com/TMHSDigital/My-Tool.git</code>",
    "Open the folder in <strong>Cursor IDE</strong>",
    "Install MCP server: <code>npm install -g @tmhs/my-mcp</code>",
    "Start using the AI skills and rules"
  ],
  "links": {
    "github": "https://github.com/TMHSDigital/My-Tool",
    "npm": "https://www.npmjs.com/package/@tmhs/my-mcp"
  },
  "quickStart": {
    "title": "Get started in seconds",
    "command": "npm install -g @tmhs/my-mcp"
  },
  "compatibility": {
    "cursor": "0.49+",
    "os": ["Windows", "macOS", "Linux"],
    "node": "18+",
    "claude": "Claude Code compatible"
  },
  "relatedTools": [
    {
      "name": "Docker Developer Tools",
      "url": "https://tmhsdigital.github.io/Docker-Developer-Tools/",
      "description": "Container management and Dockerfile support"
    }
  ]
}
```

---

## mcp-tools.json Format

A flat JSON array of MCP tool definitions. Each entry has:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Tool function name (e.g. `docker_ps`) |
| `description` | string | yes | One-line description of what the tool does |
| `category` | string | no | Logical grouping (e.g. `Containers`, `Images`) |

If the tool has no MCP server, use an empty array `[]`.

### Example mcp-tools.json

```json
[
  { "name": "docker_ps", "description": "List running containers", "category": "Containers" },
  { "name": "docker_build", "description": "Build a Docker image from a Dockerfile", "category": "Images" },
  { "name": "docker_composeUp", "description": "Start all services defined in docker-compose.yml", "category": "Compose" }
]
```

When categories are present and there are multiple categories, tools are grouped into collapsible sections on the rendered page.

---

## build_site.py Data Flow

The build script reads files from the tool repo and passes them as context to the Jinja2 template.

```
.cursor-plugin/plugin.json  -->  plugin (dict)
site.json                   -->  site (dict)
skills/*/SKILL.md           -->  parse_skills()   -->  skills (list), skill_count (int)
rules/*.mdc|*.md            -->  parse_rules()    -->  rules (list), rule_count (int)
mcp-tools.json              -->  load_mcp_tools() -->  mcp_tools (list), mcp_tool_count (int), mcp_grouped (dict)
CHANGELOG.md                -->  parse_changelog()-->  changelog (list), has_changelog (bool)
                                                       build_date (str, ISO date)
```

### Parsers

**parse_skills(repo_root)**: Iterates `skills/*/SKILL.md`. Extracts YAML frontmatter (`name`, `description`, `category`), trigger phrases from a `## Trigger` section, and tool names from a `tools:` YAML list in frontmatter.

**parse_rules(repo_root)**: Iterates `rules/*.mdc` and `rules/*.md`. Extracts `description` and `globs`/`scope` from frontmatter-style key-value pairs.

**parse_changelog(repo_root)**: Reads `CHANGELOG.md` in Keep-a-Changelog format. Returns the 2 most recent non-`[Unreleased]` entries with version, date, and categorized items.

**load_mcp_tools(repo_root)**: Reads `mcp-tools.json` as a flat list.

**group_by_category(items)**: Groups MCP tools by their `category` field into a sorted dict.

### Running locally

```bash
python site-template/build_site.py --repo-root /path/to/your-tool --out /path/to/your-tool/docs
```

The script also copies `site-template/fonts/` and the repo's `assets/` directory into the output folder.

---

## Customization Guide

### Colors

Set `accent` and `accentLight` in `site.json` to match your tool's brand. The template derives all other accent-related styles (glow, hover, gradient text) from these two values.

### Install steps

The `installSteps` array supports inline HTML (`<code>`, `<strong>`, `<a>`). Each step is rendered as a numbered list with copy buttons on `<code>` elements.

### Quick-start

The `quickStart.command` field supports multi-line strings (use `\n`). The command is displayed in a monospace code block with a copy button.

### Compatibility badges

Only non-null fields in `compatibility` are rendered. Omit fields that don't apply (e.g. omit `node` for Python-only tools).

### Related tools

The `relatedTools` array renders as a card grid before the footer. Each card links to the tool's site and shows a short description.

---

## pages.yml Workflow

Each tool repo needs this workflow at `.github/workflows/pages.yml`:

```yaml
name: Deploy GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - "skills/**"
      - "rules/**"
      - "mcp-tools.json"
      - "site.json"
      - ".cursor-plugin/plugin.json"
      - "assets/**"
  workflow_dispatch:

permissions:
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - uses: actions/checkout@v6
        with:
          repository: TMHSDigital/Developer-Tools-Directory
          path: _template
          sparse-checkout: site-template

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r _template/site-template/requirements.txt

      - name: Build site
        run: python _template/site-template/build_site.py --repo-root . --out docs

      - name: Configure Pages
        uses: actions/configure-pages@v6

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v4
        with:
          path: docs

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v5
```

---

## Troubleshooting

### "ERROR: .cursor-plugin/plugin.json not found"

The build script requires this file. Ensure your repo has `.cursor-plugin/plugin.json` with at least `displayName`, `description`, `version`, `author`, `repository`, and `license`.

### "ERROR: site.json not found"

Create a `site.json` in the repo root. At minimum it can be `{}` and the template will use default colors.

### Empty skills/rules sections

If your `skills/` directory is empty or missing, those sections are simply omitted from the rendered page. Same for rules and MCP tools.

### Jinja2 errors during build

Ensure `requirements.txt` is installed (`pip install -r _template/site-template/requirements.txt`). The only dependency is `Jinja2`.

### Fonts not loading

The build script copies `site-template/fonts/` into `docs/fonts/`. If fonts are missing, check that the `_template` checkout in your workflow includes the `site-template` directory.

### Changelog not appearing

The parser expects Keep-a-Changelog format: `## [1.0.0] - 2026-01-01` headings with `### Added`, `### Changed`, etc. subsections. `[Unreleased]` entries are skipped.
