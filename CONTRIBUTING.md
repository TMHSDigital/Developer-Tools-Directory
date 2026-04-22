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

2. Run the sync script - it regenerates every derived artifact (README tables and stats, CLAUDE.md, embedded registry in `docs/index.html`):

   ```bash
   python scripts/sync_from_registry.py
   ```

3. Verify the sync is clean:

   ```bash
   python scripts/sync_from_registry.py --check
   ```

4. Commit with `feat: add <tool-name> to registry`. Remember to sign off your commit (see DCO section below).

For a full end-to-end walkthrough including scaffolding the tool repo, see [`docs/contributors/adding-a-tool.md`](docs/contributors/adding-a-tool.md).

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

## How to Update the Site Template

The unified site template (`site-template/`) powers GitHub Pages for all tool repos. Changes to the template affect every site at next deploy.

### Files

| File | Purpose |
|------|---------|
| `site-template/template.html.j2` | Jinja2 HTML template rendered by each tool repo |
| `site-template/build_site.py` | Build script that reads repo data and renders the template |
| `site-template/fonts/` | Self-hosted Inter and JetBrains Mono woff2 files |
| `site-template/SETUP-PROMPT.md` | Full schema reference for `site.json`, `mcp-tools.json`, data flow |

### Testing locally

```bash
python site-template/build_site.py --repo-root /path/to/tool-repo --out /tmp/tool-test
```

Open the generated `index.html` in a browser to verify. Repeat for at least one other tool repo to confirm the template works across different data shapes.

### Rebuilding all tool repos after a template change

After modifying `template.html.j2` or `build_site.py`, rebuild each affected tool repo locally:

```bash
for repo in Docker-Developer-Tools Home-Lab-Developer-Tools Steam-Cursor-Plugin Monday-Cursor-Plugin; do
  python site-template/build_site.py --repo-root "$TOOLS_ROOT/$repo" --out "$TOOLS_ROOT/$repo/docs"
done
```

Where `$TOOLS_ROOT` is the parent directory containing your checkouts of each tool repo. Then commit the updated `docs/index.html` in each repo.

### Adding a new site.json field

1. Add the field to `build_site.py` - load it from `site.json` and pass it in the template context
2. Use the field in `template.html.j2` with a Jinja2 conditional so existing repos without the field still render correctly
3. Document the field in `site-template/SETUP-PROMPT.md` (schema table, example, and customization guide)
4. Add a default value to the scaffold's `site.json.j2` template if applicable
5. Test with a repo that uses the field and one that doesn't
6. Commit with `feat: add <field-name> support to site template`

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
- [ ] No em dashes or en dashes in any content (see [`standards/writing-style.md`](standards/writing-style.md))
- [ ] No hardcoded credentials, tokens, business emails, or local filesystem paths
- [ ] If registry changed: run `python scripts/sync_from_registry.py` and commit the result
- [ ] `python scripts/sync_from_registry.py --check` exits 0
- [ ] If standard added: both `standards/README.md` and `README.md` tables are updated
- [ ] If scaffold changed: dry-run test passes
- [ ] Commit messages follow conventional format and are `Signed-off-by:` (see DCO section)

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

## Developer Certificate of Origin (DCO)

All contributions must be signed off under the [Developer Certificate of Origin 1.1](https://developercertificate.org/). This is a lightweight way to certify that you wrote the contribution or have the right to submit it.

### How to sign off

Add `Signed-off-by: Your Name <your-email>` to the end of every commit message. Git can do this automatically with the `-s` flag:

```bash
git commit -s -m "feat: add new standard"
```

Your name and email must match your Git identity. Use a real name - pseudonyms are not accepted.

If you forget to sign off, amend the commit:

```bash
git commit --amend -s --no-edit
git push --force-with-lease
```

### Inbound license grant

By submitting a contribution to this repository, you certify that you have the right to do so under the Developer Certificate of Origin 1.1, and you grant TMHSDigital a perpetual, worldwide, non-exclusive, royalty-free, irrevocable license to use, reproduce, prepare derivative works of, publicly display, publicly perform, sublicense, and distribute your contribution under the project's current license (CC-BY-NC-ND-4.0) or any successor license chosen by the project.

This grant exists because CC-BY-NC-ND-4.0's "NoDerivatives" clause would otherwise prevent the project from accepting pull requests (every PR is a derivative). See [`standards/licensing.md`](standards/licensing.md) for the full rationale.

### Enforcement

The preferred enforcement is the built-in [GitHub DCO App](https://github.com/apps/dco). Maintainers enable it from repo settings; no workflow is required. PRs with unsigned commits are blocked by the App's status check.

If the App is unavailable, a pinned fallback workflow can be added. Contributors do not need to do anything different - just sign off.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.
