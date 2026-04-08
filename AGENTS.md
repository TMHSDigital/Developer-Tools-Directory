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
- **`.github/workflows/`** -- CI/CD for this repo (validate + pages deploy).

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

## Code conventions

- No hardcoded credentials anywhere
- `registry.json` must be valid JSON at all times -- CI enforces this
- The catalog site uses no external CDN dependencies -- everything is self-contained
- Standards docs are written for public readership -- no internal references or private repo mentions
- Use hyphens, not em dashes or en dashes, in all content

## Dependencies

This repo has one Python dependency: `Jinja2` (for the scaffold generator). It is listed in `requirements.txt`.

The docs site has zero dependencies -- vanilla HTML, CSS, and JavaScript.

## License

CC-BY-NC-ND-4.0. All contributions fall under this license.
