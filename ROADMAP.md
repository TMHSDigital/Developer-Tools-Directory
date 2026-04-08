# Roadmap

> Developer Tools Directory roadmap. Versions follow semantic versioning.

## Current Status

**v1.1.0** - Centralized directory with 10 registered tools, scaffold generator, unified site template, and GitHub Pages catalog.

## Release Plan

| Version | Theme | Status |
|---------|-------|--------|
| v1.0.0 | Foundation | Released |
| v1.1.0 | Unified Site Template | Released |
| v1.2.0 | Cross-Repo Consistency | Next |
| v1.3.0 | Content-Rich Pages | Planned |
| v1.4.0 | Discovery and Performance | Planned |
| v1.5.0 | Infrastructure and Documentation | Planned |

---

## v1.0.0 - Foundation

Initial release of the centralized directory.

- `registry.json` with schema for all developer tools
- Standards documentation (CI/CD, GitHub Pages, repository structure, versioning)
- Scaffold generator (`create-tool.py`) for new tool repos
- GitHub Pages catalog site
- CI validation of registry schema and scaffold dry-run
- CodeQL, dependency review, stale issue, label sync workflows
- `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `SECURITY.md`
- CC-BY-NC-ND-4.0 licensing

---

## v1.1.0 - Unified Site Template

Shared `site-template/` system consumed by all tool repos via CI.

- `build_site.py` renders GitHub Pages from `plugin.json`, `site.json`, skills, rules, and `mcp-tools.json`
- `template.html.j2` with Jinja2 templating
- Self-hosted Inter and JetBrains Mono fonts
- Collapsible sections (all start collapsed)
- MCP tool search/filter with `/` shortcut
- Copy-to-clipboard on install steps
- Back-to-top button, scroll spy, toast notifications
- Animated stat counters with `prefers-reduced-motion` support
- Mobile-responsive navigation
- Hero section with logo from `plugin.logo`
- Accent glow on section cards (`color-mix` box-shadow)
- Light/dark mode (OS preference + manual 3-state toggle + localStorage)
- Smooth expand/collapse height animation
- Richer footer (social links, build date, version, directory link)
- Scaffold templates updated (`pages.yml.j2`, `site.json.j2`, `mcp-tools.json.j2`)

---

## v1.2.0 - Cross-Repo Consistency

Audit and standardize all tool repos for uniform quality.

### README Style Audit
- Unify badge format across all 4 tool repos (clickable `<a><img></a>`, consistent ordering)
- Standardize structure: badges, description, features, quick-start, install, contributing, license
- Ensure all READMEs use collapsible `<details>` sections for lengthy content

### CI Gaps
- Audit which repos are missing: `codeql.yml`, `dependency-review.yml`, `label-sync.yml`, `release-drafter.yml`
- Add missing workflows from scaffold templates to repos that lack them

### Directory Catalog Site Polish
- Apply the same visual treatment from tool sites to `docs/index.html` in the directory repo
- Dark/light mode toggle, accent glow on cards, richer footer, animations
- Rewrite the older HTML structure to match the unified template aesthetic

---

## v1.3.0 - Content-Rich Pages

Enrich the tool sites with more useful data pulled at build time.

### Skill Detail Expansion
- Click a skill row to expand inline with full description, trigger phrases, usage notes
- `build_site.py` parses full `SKILL.md` body (not just name + first line)
- JS toggle on `<tr>` click to show/hide a detail row

### Changelog Section
- Parse each repo's `CHANGELOG.md` and render the most recent 3-5 entries
- New collapsible "Changelog" section after Install

### Quick-Start Snippet
- Prominent code block in the hero area or right after install for fastest path to usage
- New `quickStart` field in `site.json`

### Compatibility Badges
- Show supported Cursor versions, OS, Node/Python versions as pill badges
- New `compatibility` object in `site.json`

### Related Tools Cross-Links
- Each site links to other tools in the directory
- New `relatedTools` array in `site.json` with `{ name, url }` entries
- Rendered as a section before the footer

---

## v1.4.0 - Discovery and Performance

Make tools easier to find and sites faster to load.

### OG Image / Social Preview
- Auto-generate branded `og:image` per repo at build time
- Include repo logo, name, description, accent color
- Store as `docs/assets/og.png`

### Global Search on Directory Catalog
- Search bar on the directory catalog site filtering across all tools, skills, rules, and MCP tools
- Build-time aggregation from `registry.json` and per-repo data

### Site Performance Audit
- Lighthouse audit across all 5 sites
- Optimize: font preloading, lazy-load below-fold content, minimize unused CSS
- Document baseline and post-optimization scores

---

## v1.5.0 - Infrastructure and Documentation

Maintenance, documentation, and packaging consistency.

### Template Documentation
- Flesh out `site-template/SETUP-PROMPT.md` with full `site.json` schema, `mcp-tools.json` format, `build_site.py` data flow, customization guide, and troubleshooting
- Add site-template contributor section to `CONTRIBUTING.md`

### npm Workspace Audit
- Docker and Home Lab already have `mcp-server/package.json` and publish workflows
  - Docker uses OIDC-based provenance publishing
  - Home Lab uses `NPM_TOKEN` secret
  - Standardize on one approach
- Confirm Steam (plugin-only) and Monday (Python-based) don't need npm
- Verify `registry.json` npm fields are accurate

---

## Completed

- [x] `registry.json` schema with 10 registered tools and full CI validation
- [x] Standards documentation (CI/CD, GitHub Pages, repo structure, versioning)
- [x] Scaffold generator (`create-tool.py`) with Jinja2 templates
- [x] GitHub Pages catalog site (`docs/index.html`)
- [x] CodeQL, dependency review, stale issue, label sync, release-drafter workflows
- [x] `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`
- [x] Repository logo (`assets/logo.png`)
- [x] Unified site template (`site-template/`) with `build_site.py` and `template.html.j2`
- [x] Self-hosted fonts (Inter, JetBrains Mono)
- [x] Collapsible sections, search/filter, copy buttons, toast, back-to-top
- [x] Hero logo, accent glow, light/dark mode, expand animations, rich footer
- [x] Scaffold updated for unified template (`pages.yml.j2`, `site.json.j2`, `mcp-tools.json.j2`)
- [x] All 4 tool repos deployed with unified site template
- [x] `AGENTS.md` created in all 4 tool repos
- [x] Monday CI workflow and dependency-review workflow added
- [x] Monday README badges made clickable

---

## Release Process

1. Implement all items for the milestone
2. Update `registry.json` if tool metadata changed
3. Run `validate.yml` CI (schema validation + scaffold dry-run)
4. Rebuild all affected tool repo sites locally and verify
5. Update `CHANGELOG.md` and this file
6. Commit, tag, push, create GitHub release
7. Trigger `pages.yml` deploys for affected tool repos

---

## Contributing

Have an idea for a new standard, template feature, or tool integration? Check the [Contributing Guide](CONTRIBUTING.md) and open an issue or pull request.
