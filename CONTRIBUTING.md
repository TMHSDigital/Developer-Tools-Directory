# Contributing to Developer Tools Directory

Thank you for your interest in contributing. This guide covers everything you need to get started.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Developer-Tools-Directory.git
   cd Developer-Tools-Directory
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```

## Repository Structure

```
Developer-Tools-Directory/
  registry.json              # Tool catalog (source of truth)
  standards/                 # Convention documentation (9 docs)
  scaffold/
    create-tool.py           # Repo generator script
    templates/               # Jinja2 templates for new repos
  site-template/
    build_site.py            # Shared GitHub Pages build for tool repos
    template.html.j2         # HTML template with configurable branding
    fonts/                   # Self-hosted Inter + JetBrains Mono woff2
  docs/                      # GitHub Pages catalog site
  assets/                    # Logo image
  .github/workflows/         # CI/CD automation
```

## How to Add a New Tool to the Registry

1. Open `registry.json` and add a new entry at the end of the array:

```json
{
  "name": "Your Tool Name",
  "repo": "TMHSDigital/Your-Tool-Repo",
  "slug": "your-tool-repo",
  "description": "One-line description of the tool",
  "type": "cursor-plugin",
  "homepage": "https://tmhsdigital.github.io/Your-Tool-Repo/",
  "skills": 0,
  "rules": 0,
  "mcpTools": 0,
  "extras": {},
  "npm": "",
  "topics": ["topic-1", "topic-2"],
  "status": "active",
  "version": "0.1.0",
  "language": "Python",
  "license": "CC-BY-NC-ND-4.0",
  "pagesType": "static",
  "hasCI": true
}
```

2. Update the embedded registry copy in `docs/index.html` - find the `<script type="application/json" id="registry-data">` tag and add the same entry there.

3. Update `README.md`:
   - Add a row to the Tools table
   - Add a row to the Tool descriptions table (inside the `<details>` block)
   - Update the aggregate stats line (total repos, skills, rules, MCP tools)

4. Commit with `feat: add <tool-name> to registry`

### Required fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | Display name |
| `repo` | string | `Owner/RepoName` format |
| `slug` | string | Kebab-case, matches repo name |
| `description` | string | One line, no em dashes |
| `type` | string | `cursor-plugin` or `mcp-server` |
| `homepage` | string | URL or empty string |
| `skills` | int | >= 0 |
| `rules` | int | >= 0 |
| `mcpTools` | int | >= 0 |
| `extras` | object | Optional counts (snippets, templates, etc.) |
| `topics` | string[] | Discovery tags |
| `status` | string | `active`, `beta`, or `deprecated` |
| `version` | string | Semver |
| `language` | string | Primary language |
| `license` | string | SPDX identifier |
| `pagesType` | string | `static`, `mkdocs`, or `none` |
| `hasCI` | bool | Whether repo has CI workflows |

## How to Write a New Standard

1. Create a new Markdown file in `standards/`:
   ```bash
   # Example: standards/testing.md
   ```

2. Structure the document:
   - Start with an H1 title
   - Include a brief overview paragraph
   - Use H2 sections for major topics
   - Include concrete examples and code blocks
   - Write for public readership - no internal references

3. Add the standard to two index locations:
   - `standards/README.md` - add a row to the table
   - `README.md` - add a row to the Standards table

4. If the standard affects scaffold output, update the corresponding `.j2` template in `scaffold/templates/`.

5. Commit with `feat: add <standard-name> standard`

## How to Update the Scaffold

### Editing an existing template

1. Edit the `.j2` file in `scaffold/templates/`
2. Test locally:
   ```bash
   python scaffold/create-tool.py \
     --name "Test Plugin" \
     --description "Test description" \
     --mcp-server \
     --skills 2 \
     --rules 1 \
     --output /tmp/scaffold-test
   ```
3. Verify the generated files look correct
4. Commit with `fix:` or `chore:` prefix

### Adding a new template

1. Create the `.j2` file in `scaffold/templates/`
2. Update `scaffold/create-tool.py` to render it via `write_file()`
3. Run a test generation and verify the new file appears
4. Update `README.md` "What it generates" section if visible to users
5. Commit with `feat: add <template-name> scaffold template`

### Template syntax

Templates use Jinja2. Available context variables:

| Variable | Type | Description |
|----------|------|-------------|
| `name` | string | Display name |
| `slug` | string | Kebab-case identifier |
| `description` | string | One-line description |
| `type` | string | `cursor-plugin` or `mcp-server` |
| `has_mcp` | bool | Whether MCP server scaffold is included |
| `skills` | list | Skill name strings |
| `rules` | list | Rule name strings |
| `skill_count` | int | Number of skills |
| `rule_count` | int | Number of rules |
| `license_spdx` | string | SPDX license identifier |
| `license_key` | string | License key for template selection |
| `author_name` | string | Author name |
| `author_email` | string | Author email |
| `repo_owner` | string | GitHub org (TMHSDigital) |
| `repo_name` | string | Repository name (same as slug) |

## How to Update the Catalog Site

The catalog site lives in `docs/` and is vanilla HTML/CSS/JS with zero dependencies.

- `docs/index.html` - page structure, embedded registry fallback
- `docs/style.css` - dark theme, responsive cards
- `docs/script.js` - fetches registry.json, renders stats and tool cards, filtering

The `pages.yml` workflow copies `registry.json` and `assets/` into `docs/` at deploy time, so you don't need to manually copy files.

To test locally, open `docs/index.html` in a browser. The script falls back to the embedded registry data.

## Pull Request Process

### Branch naming

Use descriptive branch names with a type prefix:
- `feat/add-tool-name` - new registry entries or standards
- `fix/correct-registry-field` - corrections
- `chore/update-jinja2` - dependency or CI changes
- `docs/improve-scaffold-docs` - documentation improvements

### Commit style

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add kubernetes developer tools to registry
fix: correct homepage URL for steam-mcp
docs: clarify scaffold --license flag usage
chore: bump Jinja2 to 3.1.5
```

### Review checklist

Before submitting a PR, verify:

- [ ] `registry.json` is valid JSON (run `python -c "import json; json.load(open('registry.json'))"`)
- [ ] No em dashes or en dashes in any content
- [ ] No hardcoded credentials or tokens
- [ ] If registry changed: embedded copy in `docs/index.html` is updated
- [ ] If registry changed: README.md tools table and stats are updated
- [ ] If standard added: both `standards/README.md` and `README.md` tables are updated
- [ ] If scaffold changed: dry-run test passes
- [ ] Commit messages follow conventional format

### CI checks

All PRs must pass:
- Registry schema validation
- Docs file existence
- Scaffold syntax and dry-run test
- CodeQL security scan
- Dependency review

## Style Guidelines

- **No em dashes.** Use regular hyphens (-) or rewrite the sentence.
- **No hardcoded credentials.** Environment variables or config files only.
- **Concise descriptions.** No filler text or marketing language.
- **Public readership.** All content should make sense to external contributors.
- **Consistent formatting.** Use existing files as reference for Markdown structure.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.
