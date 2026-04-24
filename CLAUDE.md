# CLAUDE.md

Project documentation for Claude Code and AI assistants working on this repository.

## Project Overview

Developer Tools Directory is a **meta-repository** that catalogs, standardizes, and scaffolds all TMHSDigital Cursor IDE plugins and MCP servers. It does not contain a plugin or MCP server itself.

**License:** CC-BY-NC-ND-4.0 outbound, DCO + broader inbound grant (see [`CONTRIBUTING.md`](CONTRIBUTING.md))
**Author:** TMHSDigital

**Catalog site:** https://tmhsdigital.github.io/Developer-Tools-Directory/

## Architecture

```
Developer-Tools-Directory/
  registry.json              # Source of truth for all tool repos
  standards/                 # 17 convention docs (structure, CI/CD, testing, MCP, security, licensing, etc.)
  scaffold/
    create-tool.py           # Python repo generator (Jinja2)
    templates/               # Jinja2 templates for new repos
  scripts/
    sync_from_registry.py    # Regenerates README, CLAUDE.md, and docs embedded registry
  site-template/
    build_site.py            # Builds GitHub Pages for tool repos from their metadata
    template.html.j2         # Shared HTML template with configurable branding
    fonts/                   # Self-hosted Inter + JetBrains Mono woff2
    SETUP-PROMPT.md          # Copy-paste prompt for applying template to a repo
  docs/
    index.html               # GitHub Pages catalog site
    style.css                # Dark theme, responsive, card layout
    script.js                # Fetches registry.json, renders cards, filters
    .well-known/security.txt # RFC 9116 security contact
    contributors/            # Worked examples for new contributors
  assets/
    logo.png                 # Directory logo
  .github/
    CODEOWNERS               # Review routing
    PULL_REQUEST_TEMPLATE.md
    ISSUE_TEMPLATE/          # Bug report, feature request, config
    workflows/               # Validate, sync, pages, release, stale, codeql, etc.
      README.md              # Action-pinning convention
```

## Key Files

### registry.json

Array of tool objects. Each entry has: `name`, `repo`, `slug`, `description`, `type` (cursor-plugin | mcp-server), `homepage`, `skills`, `rules`, `mcpTools`, `extras`, `topics`, `status`, `version`, `language`, `license`, `pagesType`, `hasCI`. `status` is one of `experimental`, `beta`, `active`, `maintenance`, `deprecated`, or `archived` (see [`standards/lifecycle.md`](standards/lifecycle.md)).

When updating, run `python scripts/sync_from_registry.py` to regenerate every derived artifact. The `sync-check` CI job blocks PRs that drift.

### scripts/sync_from_registry.py

Pure-stdlib Python script that regenerates README tables and stats, CLAUDE.md cataloged tools and totals, and the embedded registry JSON in `docs/index.html`. Modes: no flag (write), `--check` (CI drift detection), `--about` (print the `gh repo edit` command for the GitHub About section, run locally).

### scaffold/create-tool.py

CLI args: `--name`, `--slug`, `--description`, `--type`, `--mcp-server`, `--skills N`, `--rules N`, `--license`, `--output`, `--author-name`, `--author-email`.

Templates in `scaffold/templates/` produce: plugin.json, GitHub Actions workflows, README.md, AGENTS.md, CLAUDE.md, CONTRIBUTING.md, CHANGELOG.md, CODE_OF_CONDUCT.md, SECURITY.md, ROADMAP.md, LICENSE, .cursorrules, .gitignore, docs/index.html, and optional mcp-server/ scaffold.

### docs/ (catalog site)

Static HTML/CSS/JS. No build step. No external CDN. The `pages.yml` workflow copies `registry.json` and `assets/` into `docs/` at deploy time. `script.js` fetches `registry.json` at runtime and falls back to an embedded copy. Never use `innerHTML`/`eval` with registry data - the safety-scan CI job blocks reintroduction.

### standards/

17 Markdown documents defining conventions for every tool repo. Index in [`standards/README.md`](standards/README.md).

## Cataloged Tools

<!-- registry:tools:start -->
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
<!-- registry:tools:end -->

<!-- registry:stats:start -->
**Totals:** 177 skills, 71 rules, 371 MCP tools across 9 repos
<!-- registry:stats:end -->

## Development Workflow

### Contribution flow

`main` is protected by the `main protection` ruleset. Direct pushes, force pushes, and branch deletion are all blocked for every contributor including the repo owner (empty bypass list). All changes land via pull request with squash merge only.

Standard loop for any change, including single-file edits:

```bash
git checkout -b <type>/<short-description>
# edits
git add <paths>
git commit -s -m "<conventional subject>"
git push -u origin HEAD
gh pr create --base main
gh pr checks <number> --watch
gh pr merge <number> --squash --delete-branch
```

A PR cannot be merged until all 8 required status checks pass: `Validate registry.json`, `Validate docs site`, `Validate scaffold`, `Registry sync check`, `Public-repo safety scan`, `feat/fix commits require VERSION bump`, `Check VERSION vs latest tag`, `CodeQL`. Required approvals are 0 (solo maintainer).

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
- Scaffold dry-run test (generates repo, verifies key files exist, scans for leaked business email)
- `sync-check` job: runs `python scripts/sync_from_registry.py --check` and fails on drift
- `safety-scan` job: blocks leaked business emails, drive-letter paths, unsafe DOM sinks (`innerHTML`/`eval` in `docs/`), and committed credential files
- `version-bump-check` job (PR only): requires a `VERSION` bump when the PR contains any `feat:` or `fix:` commit; opt out per commit with `[skip version]`

### Release workflow

`release.yml` runs on push to main and reads the `VERSION` file at the repo root. If `VERSION` is ahead of the latest git tag, it creates tag `v<VERSION>` and a GitHub Release. If `VERSION` equals the latest tag, the workflow no-ops. If `VERSION` is lower, the workflow fails. Release notes come from release-drafter's current draft body when present, otherwise from the commit log since the previous tag. The meta-repo uses VERSION-file-driven releases; tool repos use conventional-commit auto-bumps per `standards/versioning.md`.

## Conventions

- **Conventional commits** with DCO sign-off (`git commit -s`)
- **No em dashes, en dashes, or emoji** - see [`standards/writing-style.md`](standards/writing-style.md)
- **No hardcoded credentials, business emails, or local filesystem paths** anywhere
- **Public readership** - all docs written for external consumption
- **Single branch** - `main` only
- **Self-contained docs site** - no CDN, no unsafe DOM sinks
- **`registry.json` is the single source of truth** - README, CLAUDE.md, and `docs/index.html` embedded data are generated

## Dependencies

| Dependency | Purpose | Where |
|------------|---------|-------|
| Jinja2 >=3.1,<4.0 | Scaffold template rendering | `requirements.txt` |

The docs site has zero runtime dependencies. The sync script is pure stdlib.
