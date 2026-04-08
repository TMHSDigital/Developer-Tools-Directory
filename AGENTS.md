# AGENTS.md

This file tells AI coding agents how the Developer Tools Directory repo works and how to contribute correctly.

**Catalog site:** https://tmhsdigital.github.io/Developer-Tools-Directory/ (auto-deployed on push to main)

## Repository overview

This is a **meta-repository** -- it does not contain a Cursor plugin or MCP server itself. It catalogs, standardizes, and scaffolds other TMHSDigital developer tool repos. It contains:

- **`registry.json`** -- single source of truth for all tool repos (9 entries). The catalog site and README tables are derived from it.
- **`standards/`** -- 9 Markdown docs defining conventions for folder structure, CI/CD, plugin manifests, GitHub Pages, commit conventions, README format, AGENTS.md format, and versioning.
- **`scaffold/`** -- Python repo generator (`create-tool.py`) with 18 Jinja2 templates that produce a fully standards-compliant new tool repo.
- **`docs/`** -- static GitHub Pages catalog site (vanilla HTML/CSS/JS, no build step). Reads `registry.json` at runtime to render tool cards.
- **`assets/`** -- logo image.
- **`.github/workflows/`** -- CI/CD for this repo (validate, pages, release, release-drafter, stale, codeql, dependency-review, label-sync).

## Branching and commit model

- **Single branch**: `main` only. No develop/release branches.
- **Conventional commits** are required:
  - `feat:` -- new tool added to registry, new standard doc, new scaffold template
  - `fix:` -- corrections to existing content
  - `chore:` -- dependency updates, CI changes
  - `docs:` -- documentation-only changes
- Commit messages should be concise and describe the "why", not the "what".

## CI/CD workflows

### `validate.yml` (runs on PR and push to main)

Checks:
- `registry.json` is valid JSON with correct schema (required fields, valid types, integer counts)
- `docs/index.html`, `docs/style.css`, `docs/script.js` exist
- `scaffold/create-tool.py` compiles without syntax errors
- Scaffold dry-run test: generates a test repo and verifies key files exist

### `pages.yml` (runs on push to main when docs/, assets/, or registry.json change)

1. Copies `registry.json` into `docs/` for client-side fetch
2. Copies `assets/` into `docs/assets/`
3. Uploads `docs/` as a Pages artifact
4. Deploys to GitHub Pages via `actions/deploy-pages`

### `release.yml` (runs on push to main, ignores docs/md/standards changes)

1. Gets the latest git tag
2. Determines version bump from conventional commit prefixes since last tag
3. Creates annotated tag and pushes it
4. Creates a GitHub Release with auto-generated notes

Has a concurrency guard -- only one release can run at a time. Commits with `[skip ci]` are ignored.

The repo About section (description, homepage, topics) must be updated manually after registry changes since the GITHUB_TOKEN lacks permission for `gh repo edit`. Run locally:

```
gh repo edit TMHSDigital/Developer-Tools-Directory --description "Centralized catalog, standards, and scaffolding for <N> TMHSDigital developer tools - <S> skills, <R> rules, <M> MCP tools"
```

### `release-drafter.yml` (runs on push to main and PR activity)

Auto-drafts release notes from merged PR titles/labels. Config in `.github/release-drafter.yml` defines categories (Features, Standards, Scaffold, Bug Fixes, Documentation, CI) and version resolution rules.

### `stale.yml` (weekly on Sunday midnight UTC)

Marks and closes inactive issues and PRs. Issues: 60-day stale / 14-day close. PRs: 30-day stale / 14-day close. Exempt labels: `pinned`, `security`, `enhancement`.

### `codeql.yml` (push/PR to main + weekly Monday 06:00 UTC)

Runs GitHub CodeQL security scanning for Python code.

### `dependency-review.yml` (runs on PRs to main)

Audits new dependencies for known vulnerabilities. Comments a summary in the PR. Fails on high severity.

### `label-sync.yml` (runs on PR open/sync)

Auto-labels PRs by changed file paths: `standards/` -> standards, `scaffold/` -> scaffold, `docs/` -> documentation, `registry.json` -> registry, `.github/` -> ci.

## Key files and what they do

### `registry.json`

Array of tool objects. Required fields per entry:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name |
| `repo` | string | `Owner/RepoName` |
| `slug` | string | Kebab-case identifier |
| `description` | string | One-line summary |
| `type` | string | `cursor-plugin` or `mcp-server` |
| `homepage` | string | Docs site URL (empty string if none) |
| `skills` | int | Number of skills |
| `rules` | int | Number of rules |
| `mcpTools` | int | Number of MCP tools |
| `extras` | object | Optional extra counts (snippets, templates, natives, events) |
| `npm` | string | npm package name (empty string or omit if none) |
| `topics` | string[] | Discovery tags |
| `status` | string | `active`, `beta`, `deprecated` |
| `version` | string | Current semver version |
| `language` | string | Primary language |
| `license` | string | SPDX identifier |
| `pagesType` | string | `static`, `mkdocs`, or `none` |
| `hasCI` | bool | Whether the repo has CI workflows |

### `docs/index.html`

The catalog site. It embeds a copy of the registry data in a `<script type="application/json">` tag as a fallback, and also fetches `registry.json` at runtime. When updating the registry, **also update the embedded copy in index.html** to keep them in sync.

### `scaffold/create-tool.py`

Python script using Jinja2. Templates live in `scaffold/templates/`. The script accepts CLI args (`--name`, `--description`, `--type`, `--mcp-server`, `--skills`, `--rules`, `--license`, `--output`).

### `standards/`

Pure documentation -- no code. Each file documents a convention derived from analyzing existing TMHSDigital tool repos (CFX, Docker, Steam, Home Lab, etc.).

## Adding a new tool to the registry

1. Add an entry to `registry.json` following the schema above
2. Update the embedded registry in `docs/index.html` to match
3. Update the tools table and aggregate stats line in `README.md`
4. Use `feat:` commit prefix

## Adding or updating a standard

1. Edit or create the file in `standards/`
2. If new, add a row to the standards table in `README.md` and in `standards/README.md`
3. If the standard affects the scaffold output, update the corresponding `.j2` template in `scaffold/templates/`
4. Use `docs:` commit prefix for docs-only changes, `feat:` if adding a new standard

## Updating the scaffold

1. Edit templates in `scaffold/templates/`
2. If adding a new template file, update `scaffold/create-tool.py` to render it
3. Test with: `python scaffold/create-tool.py --name "Test" --description "Test" --mcp-server --skills 2 --rules 1 --output /tmp/test`
4. CI runs a dry-run test on every push

## When editing registry.json

- Every entry requires all fields listed in the schema table above. CI validates this on every push and PR.
- `type` must be exactly `cursor-plugin` or `mcp-server`. No other values are accepted.
- `skills`, `rules`, and `mcpTools` must be integers, not strings.
- `status` must be `active`, `beta`, or `deprecated`.
- After adding or modifying an entry, you must also update:
  1. The embedded registry copy in `docs/index.html` -- find the `<script type="application/json" id="registry-data">` tag and sync it with `registry.json`
  2. The tools table in `README.md` -- add/update the row
  3. The tool descriptions `<details>` block in `README.md` -- add/update the description
  4. The aggregate stats line in `README.md` (total repos, skills, rules, MCP tools)
- Use `feat:` commit prefix when adding a new tool, `fix:` when correcting existing entries.

## When editing standards/

- Standards are pure Markdown documentation. They contain no executable code.
- Each standard should have an H1 title, a brief overview paragraph, and H2 sections for major topics.
- Write for public readership. Do not reference internal repos, private URLs, or credentials.
- No em dashes or en dashes -- use hyphens or rewrite.
- If adding a new standard document:
  1. Create the `.md` file in `standards/`
  2. Add a row to the table in `standards/README.md`
  3. Add a row to the Standards table in the main `README.md`
- If a standard change affects what the scaffold should generate, update the corresponding `.j2` template in `scaffold/templates/` to match.
- Use `docs:` commit prefix for edits, `feat:` for entirely new standards.

## When editing scaffold/

- The generator script is `scaffold/create-tool.py`. It uses Jinja2 `Environment` with `FileSystemLoader` pointed at `scaffold/templates/`.
- Templates use `.j2` extension. Available context variables: `name`, `slug`, `description`, `type`, `has_mcp`, `skills`, `rules`, `skill_count`, `rule_count`, `license_spdx`, `license_key`, `author_name`, `author_email`, `repo_owner`, `repo_name`.
- If adding a new template file:
  1. Create the `.j2` file in `scaffold/templates/` (or a subdirectory for MCP server templates)
  2. Add a `write_file()` call in `create-tool.py` to render and write it
  3. If the file is conditional (e.g., MCP-only), wrap the call in `if args.mcp_server`
- Always test changes locally before committing:
  ```
  python scaffold/create-tool.py --name "Test" --description "Test" --mcp-server --skills 2 --rules 1 --output /tmp/test
  ```
- CI runs a scaffold dry-run test on every push. If you add a new required file, add a `test -f` check to the `validate.yml` scaffold test step.
- The `LICENSE.j2` template has conditional logic for MIT, Apache-2.0, and CC-BY-NC-ND-4.0. If adding a new license option, update both the template and the `LICENSE_FILES`/`SPDX` dicts in `create-tool.py`.

## When editing docs/ (catalog site)

- `docs/index.html` is the single-page catalog site. It embeds a copy of `registry.json` inside a `<script type="application/json" id="registry-data">` tag as a fallback for when the direct fetch fails.
- `docs/script.js` fetches `registry.json` at runtime. If the fetch fails, it reads the embedded copy. It renders aggregate stats (total skills, rules, MCP tools) and tool cards with filtering by type and topic.
- `docs/style.css` contains all styling -- dark theme, responsive layout, card design. No CSS framework.
- **No external CDN dependencies.** The site must work fully offline except for badge images. No jQuery, no Bootstrap, no Google Fonts.
- The `pages.yml` workflow copies `registry.json` and `assets/` into `docs/` at deploy time. You do not need to manually place these files in `docs/`.
- When testing locally, open `docs/index.html` directly in a browser. The embedded fallback will kick in since `registry.json` won't be in `docs/` locally.
- Do not use `innerHTML` or `eval` with registry data. Use `textContent` for any user-facing text to prevent XSS.

## When editing workflows

- **`validate.yml`** runs on PR and push to main. It has three jobs: registry validation, docs existence checks, and scaffold syntax + dry-run test. Keep checks fast -- avoid installing unnecessary dependencies.
- **`pages.yml`** deploys to GitHub Pages on push to main when `docs/`, `assets/`, or `registry.json` change. It copies `registry.json` into `docs/` and `assets/` into `docs/assets/` before uploading. Uses `actions/deploy-pages`.
- **`release.yml`** auto-creates a GitHub release on push to main (excluding docs/md/standards changes). It determines the version bump from conventional commit prefixes since the last tag. Has a concurrency guard -- only one release can run at a time. Commits containing `[skip ci]` are ignored. The repo About section must be updated manually via `gh repo edit` after registry changes (the GITHUB_TOKEN lacks permission for this).
- **`release-drafter.yml`** auto-drafts release notes from merged PR titles/labels. Config is in `.github/release-drafter.yml`. Categories: Features, Standards, Scaffold, Bug Fixes, Documentation, CI/Infrastructure. The autolabeler assigns labels based on changed file paths.
- **`stale.yml`** runs weekly (Sunday midnight UTC). Issues: 60-day stale, 14-day close. PRs: 30-day stale, 14-day close. Labels exempt from staleness: `pinned`, `security`, `enhancement` (issues) and `pinned`, `security` (PRs).
- **`codeql.yml`** runs Python security scanning on push/PR to main and weekly (Monday 06:00 UTC). Uses `github/codeql-action` v3.
- **`dependency-review.yml`** runs on PRs to main. Audits new dependencies and comments a summary in the PR. Fails on `high` severity vulnerabilities.
- **`label-sync.yml`** runs on PR open/sync. Labels PRs based on changed paths: `standards/` -> standards, `scaffold/` -> scaffold, `docs/` -> documentation, `registry.json` -> registry, `.github/` -> ci.

## Code conventions

- No hardcoded credentials anywhere
- No em dashes or en dashes -- use hyphens or rewrite
- `registry.json` must be valid JSON at all times -- CI enforces this
- The catalog site uses no external CDN dependencies -- everything is self-contained
- Standards docs are written for public readership -- no internal references or private repo mentions
- Conventional commits are required (`feat:`, `fix:`, `chore:`, `docs:`)
- Single branch: `main` only

## Dependencies

This repo has one Python dependency: `Jinja2` (in `requirements.txt`). The docs site has zero dependencies -- vanilla HTML, CSS, and JavaScript.

## License

CC-BY-NC-ND-4.0. All contributions fall under this license.
