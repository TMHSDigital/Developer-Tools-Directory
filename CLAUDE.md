# CLAUDE.md

Project documentation for Claude Code and AI assistants working on this repository.

## Project Overview

Developer Tools Directory is a **meta-repository** that catalogs, standardizes, and scaffolds all TMHSDigital Cursor IDE plugins and MCP servers. It does not contain a plugin or MCP server itself.

**Version:** 1.0.0
**License:** CC-BY-NC-ND-4.0
**Author:** TMHSDigital

**Catalog site:** https://tmhsdigital.github.io/Developer-Tools-Directory/

## Architecture

```
Developer-Tools-Directory/
  registry.json              # Source of truth for all 9 tool repos
  standards/                 # 9 convention docs (folder structure, CI/CD, manifests, etc.)
  scaffold/
    create-tool.py           # Python repo generator (Jinja2)
    templates/               # Jinja2 templates for new repos
  site-template/
    build_site.py            # Builds GitHub Pages for tool repos from their metadata
    template.html.j2         # Shared HTML template with configurable branding
    fonts/                   # Self-hosted Inter + JetBrains Mono woff2
    SETUP-PROMPT.md          # Copy-paste prompt for applying template to a repo
  docs/
    index.html               # GitHub Pages catalog site
    style.css                # Dark theme, responsive, card layout
    script.js                # Fetches registry.json, renders cards, filters
  assets/
    logo.png                 # Directory logo
  .github/workflows/
    validate.yml             # Registry schema, docs existence, scaffold dry-run
    pages.yml                # Deploy catalog site to GitHub Pages
    stale.yml                # Mark/close inactive issues and PRs
    codeql.yml               # Python security scanning
    dependency-review.yml    # Audit PR dependencies
    release.yml              # Auto-create releases on push to main
    release-drafter.yml      # Auto-draft release notes from PRs
    label-sync.yml           # Auto-label PRs by changed paths
```

## Key Files

### registry.json

Array of 9 tool objects. Each entry has: `name`, `repo`, `slug`, `description`, `type` (cursor-plugin | mcp-server), `homepage`, `skills`, `rules`, `mcpTools`, `extras`, `topics`, `status`, `version`, `language`, `license`, `pagesType`, `hasCI`.

When updating, also sync:
1. Embedded registry in `docs/index.html` (`<script type="application/json" id="registry-data">`)
2. Tools table and stats line in `README.md`

### scaffold/create-tool.py

CLI args: `--name`, `--slug`, `--description`, `--type`, `--mcp-server`, `--skills N`, `--rules N`, `--license`, `--output`, `--author-name`, `--author-email`.

Templates in `scaffold/templates/` produce: plugin.json, 4 GitHub Actions workflows, README.md, AGENTS.md, CLAUDE.md, CONTRIBUTING.md, CHANGELOG.md, CODE_OF_CONDUCT.md, SECURITY.md, ROADMAP.md, LICENSE, .cursorrules, .gitignore, docs/index.html, and optional mcp-server/ scaffold.

### docs/ (catalog site)

Static HTML/CSS/JS. No build step. No external CDN. The `pages.yml` workflow copies `registry.json` and `assets/` into `docs/` at deploy time. `script.js` fetches `registry.json` at runtime and falls back to an embedded copy.

### standards/

9 Markdown documents defining conventions derived from analyzing existing TMHSDigital tool repos: folder-structure, plugin-manifest, ci-cd, github-pages, commit-conventions, readme-template, agents-template, versioning, and a standards README index.

## Cataloged Tools (9)

| Tool | Type | Skills | Rules | MCP Tools |
|------|------|-------:|------:|----------:|
| CFX Developer Tools | Plugin | 9 | 6 | 6 |
| Unity Developer Tools | Plugin | 18 | 8 | 4 |
| Docker Developer Tools | Plugin | 17 | 10 | 150 |
| Home Lab Developer Tools | Plugin | 22 | 11 | 50 |
| Mobile App Developer Tools | Plugin | 43 | 12 | 36 |
| Plaid Developer Tools | Plugin | 17 | 7 | 30 |
| Monday Cursor Plugin | Plugin | 21 | 8 | 45 |
| Steam Cursor Plugin | Plugin | 30 | 9 | 25 |
| Steam MCP Server | MCP Server | 0 | 0 | 25 |

**Totals:** 177 skills, 71 rules, 371 MCP tools

## Development Workflow

### Prerequisites

```bash
pip install -r requirements.txt  # Jinja2
```

### Testing the scaffold

```bash
python scaffold/create-tool.py \
  --name "Test Plugin" \
  --description "Automated test" \
  --mcp-server \
  --skills 2 \
  --rules 1 \
  --output /tmp/test
```

### Testing the docs site locally

Open `docs/index.html` in a browser. The script falls back to embedded registry data when not served from GitHub Pages.

### CI validation

`validate.yml` runs on every PR and push to main:
- Registry JSON syntax and schema validation
- Docs file existence checks
- Scaffold Python syntax check
- Scaffold dry-run test (generates repo, verifies key files exist)

## Conventions

- **Conventional commits**: `feat:`, `fix:`, `chore:`, `docs:`
- **No em dashes or en dashes** - use hyphens or rewrite
- **No hardcoded credentials** anywhere
- **Public readership** - all standards docs written for external consumption
- **Single branch** - `main` only, no develop/release branches
- **Self-contained docs site** - no CDN dependencies
- **registry.json is the source of truth** - README tables and catalog site derive from it

## Dependencies

| Dependency | Purpose | Where |
|------------|---------|-------|
| Jinja2 >=3.1,<4.0 | Scaffold template rendering | `requirements.txt` |

The docs site has zero runtime dependencies.
