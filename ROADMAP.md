# Roadmap

> Developer Tools Directory roadmap. Versions follow semantic versioning.

## Current Status

**v1.9.5** - Patch release. Removes `paths-ignore` from the meta-repo `release.yml` so content-only changes still gate releases on commit prefix. Companion fix removes `paths-ignore` from the scaffold `release.yml.j2` template so generated repos get the same behavior.

Prior milestones in this line:

- **v1.9.4** - docs: update release-doc-sync header comment to reflect the @v1 / @v1.X floating-tag convention.
- **v1.9.3** - fix: align scaffold output with current ecosystem patterns (ref #45).
- **v1.9.2** - fix: release-doc-sync default meta-repo-ref changed to `v1` (floating major tag).
- **v1.9.1** - fix: stale-counts policy correction; example sections and dialogue lines added to aggregate-scan skip list (DTD#37).
- **v1.9.0** - CI maintenance. Node 24-compatible GitHub Actions versions, dependabot coverage extended to github-actions ecosystem, Sponsor button and FUNDING.yml, stale-counts DTD#12 skip for AGENTS.md and CLAUDE.md.
- **v1.8.x** - release-doc-sync composite action (v1.8.0) plus fixes for checkout pollution, workspace cleanup, label-sync self-healing, floating-tag automation in `release.yml`, and version-bump-check parser.
- **v1.7.x** - drift checker in two phases: Phase 1 (agents-template standard, scaffold updates, workflow docs); Phase 2 (core library, additional checks, CI integration, token separation, exit-code propagation).
- **v1.6.3** - Drafter-body fix and branch-protection ruleset. `release.yml` treats a drafter body of `## What's Changed / * No changes` as empty. `main protection` ruleset established with 7 required checks.
- **v1.6.2** - Release-drafter decoupling. Release-drafter no longer computes its own version; change-note aggregation only. Versioning is fully driven by the `VERSION` file and `release.yml`.
- **v1.6.1** - `VERSION`-file-driven releases. Replaces conventional-commit auto-bump with an authoritative `VERSION` file; `feat:`/`fix:` commits require a VERSION bump enforced by CI.
- **v1.6.0** - Standards and Governance. Nine new standards docs, registry-to-artifact sync automation, DCO + inbound license grant, scope and lifecycle principles, public-repo safety hardening.

## Release Plan

| Version | Theme | Status |
|---------|-------|--------|
| v1.0.0 | Foundation | Released |
| v1.1.0 | Unified Site Template | Released |
| v1.2.0 | Cross-Repo Consistency | Released |
| v1.3.0 | Content-Rich Pages | Released |
| v1.4.0 | Discovery and Performance | Released |
| v1.5.0 | Infrastructure and Documentation | Released |
| v1.6.0 | Standards and Governance | Released |
| v1.6.1 | VERSION-file-driven releases | Released |
| v1.6.2 | Release-drafter decoupling | Released |
| v1.6.3 | Drafter-body fix and branch-protection ruleset | Released |
| v1.7.0 | Drift Checker Foundation | Released |
| v1.7.1 - v1.7.5 | Drift Checker Complete | Released |
| v1.8.0 | Release Doc Sync | Released |
| v1.8.1 - v1.8.5 | Release Doc Sync Fixes | Released |
| v1.9.0 | CI Maintenance | Released |
| v1.9.1 - v1.9.5 | Scaffold and Pipeline Fixes | Released |

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

## v1.6.0 - Standards and Governance

Close the content, automation, and governance gaps identified in the v1.5 audit.

### New standards docs

- [`standards/testing.md`](standards/testing.md) - frameworks by runtime, minimum coverage bar, CI wiring
- [`standards/skills.md`](standards/skills.md) - `SKILL.md` structure and frontmatter
- [`standards/rules.md`](standards/rules.md) - `.mdc` frontmatter, globs, secrets-rule pattern
- [`standards/mcp-server.md`](standards/mcp-server.md) - tool naming, runtime choice, transport, destructive ops, auth
- [`standards/security.md`](standards/security.md) - disclosure, secrets handling, supply-chain hardening
- [`standards/licensing.md`](standards/licensing.md) - DCO + inbound license grant model
- [`standards/scope.md`](standards/scope.md) - what qualifies for the directory and what does not
- [`standards/lifecycle.md`](standards/lifecycle.md) - tool status transitions
- [`standards/writing-style.md`](standards/writing-style.md) - prose conventions (em-dash rule demoted here)

### Automation

- `scripts/sync_from_registry.py` regenerates README tables, CLAUDE.md, and the embedded registry in `docs/index.html` from `registry.json`
- `validate.yml` runs `sync-check` and a public-repo `safety-scan` on every PR
- `sync.yml` opens a PR with the regenerated artifacts when `registry.json` changes on `main` (no PAT required)
- GitHub About section sync is a documented local one-liner (`python scripts/sync_from_registry.py --about`)

### Governance

- Principles in `standards/README.md` and `README.md` rewritten
- DCO + inbound license grant in `CONTRIBUTING.md`, `LICENSE` header updated, `standards/licensing.md` published
- GitHub DCO App as preferred enforcement; no third-party action stored in the repo

### Public-repo hygiene

- Hardened `.gitignore` covering Python, Node, envs, secrets, IDE, and agent caches
- `.github/CODEOWNERS`, `ISSUE_TEMPLATE/`, `PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/README.md` documenting action SHA-pinning convention
- `docs/.well-known/security.txt` per RFC 9116
- All leaked business emails and local drive-letter paths scrubbed; CI blocks reintroduction
- `scaffold/create-tool.py` default author email switched to `contact@users.noreply.github.com`

### Worked example

- `docs/contributors/adding-a-tool.md` walks a new tool from scaffold to registered-in-directory PR

---

## v1.7.0 - Drift Checker Foundation

Phase 1 of the drift checker project. Established the agents-template standard, updated scaffold templates, and aligned workflow documentation with the branch-protection ruleset.

- `standards/agents-template.md` added, documenting the required structure for AI agent guidance files in tool repos
- Scaffold updated to generate compliant `AGENTS.md` from the new template
- Workflow documentation across `AGENTS.md`, `CLAUDE.md`, and `.github/workflows/README.md` updated to reflect the active `main protection` ruleset

---

## v1.7.1 - v1.7.5 - Drift Checker Complete

Phase 2: the drift checker itself. Automated detection of tool-repo policy drift surfaced as GitHub issues.

- `scripts/drift_check/` core library: checks for standards-version signals in `AGENTS.md`, `CLAUDE.md`, skills, and rules files against the meta-repo `VERSION`
- Additional policy checks: broken standards links, required references, stale aggregate counts in markdown
- CI integration: runs on push to `main` (when checker code or standards change), weekly on schedule, and on demand via `workflow_dispatch`
- Token split: `DRIFT_CHECK_TOKEN` for cross-repo sparse-checkout reads, `GITHUB_TOKEN` for issue writes
- Exit-code propagation fix for the composite action caller

---

## v1.8.0 - Release Doc Sync

Composite action for keeping `CHANGELOG.md`, `CLAUDE.md`, and `ROADMAP.md` in sync after an automated release.

- `.github/actions/release-doc-sync/action.yml` composite action checks out the tool repo, runs the sync script, commits and pushes any drift
- Designed for use in tool-repo `release.yml` workflows: `uses: TMHSDigital/Developer-Tools-Directory/.github/actions/release-doc-sync@v1`
- `standards/release-doc-sync.md` documents the contract between the action and calling repos

---

## v1.8.1 - v1.8.5 - Release Doc Sync Fixes

Correctness fixes for the composite action and related CI machinery.

- Checkout pollution: action no longer contaminates the caller's working tree
- Defensive workspace cleanup added on failure paths
- Label-sync self-healing: ports the self-healing pattern to the meta-repo `label-sync.yml`
- Floating-tag automation: `release.yml` now creates and updates `v1` and `v1.X` floating tags on every release
- Version-bump-check parser: fixed silent pass-all bug affecting PRs with multi-line commit subjects

---

## v1.9.0 - CI Maintenance

Routine maintenance to keep the CI stack current and discoverable.

- GitHub Actions bumped to Node 24-compatible versions across all workflows
- Dependabot coverage extended to the `github-actions` ecosystem
- Sponsor button added via `.github/FUNDING.yml`
- Stale-counts check: `AGENTS.md` and `CLAUDE.md` skipped wholesale by filename regardless of config (DTD#12); aggregate-truth for those files belongs in a per-repo validate-counts job

---

## v1.9.1 - v1.9.5 - Scaffold and Pipeline Fixes

- Stale-counts policy correction: example sections and roleplay dialogue lines excluded from aggregate scanning (DTD#37)
- release-doc-sync `action.yml` default `meta-repo-ref` corrected to `v1` (floating major tag)
- Scaffold `release.yml.j2` template: `paths-ignore` removed so content-only changes still gate releases on commit prefix
- Scaffold output aligned with current ecosystem patterns (ref #45)
- Meta-repo `release.yml`: `paths-ignore` removed for the same reason as the scaffold fix

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
- [x] README style audit across all 4 tool repos (clickable badges, consistent structure)
- [x] CI gaps filled: `label-sync.yml`, `release.yml`, `links.yml` added to all tool repos
- [x] Directory catalog site polished (inline CSS/JS, dark/light mode, search, animations)
- [x] Skill detail expansion (click-to-expand rows with triggers and MCP tools)
- [x] Changelog section parsed from `CHANGELOG.md` (latest 2 releases, collapsible)
- [x] Quick-start snippet with copy button (`quickStart` in `site.json`)
- [x] Compatibility badges as pills in hero (`compatibility` in `site.json`)
- [x] Related tools cross-links as card grid (`relatedTools` in `site.json`)
- [x] OG meta tags (`og:title`, `og:description`, `og:type`, `og:image`) on catalog site
- [x] Full-aggregate search index (`aggregate_search.py`) with skills, rules, MCP tools
- [x] Global search on directory catalog with match hints (matched skill/rule/MCP tool)
- [x] `/` keyboard shortcut to focus search on catalog site
- [x] Font preloads (`<link rel="preload">`) on all sites
- [x] Lighthouse performance audit documented in `PERFORMANCE.md`
- [x] Catalog site: hero gradient, section cards, toast, mobile nav, scroll spy, collapsible sections, expand animations, rich footer
- [x] `SETUP-PROMPT.md` expanded with full `site.json` schema, `mcp-tools.json` format, `build_site.py` data flow, customization guide, troubleshooting
- [x] `CONTRIBUTING.md`: added "How to Update the Site Template" section
- [x] Home Lab `publish.yml` standardized to pure OIDC (removed `NPM_TOKEN`)
- [x] steam-mcp `publish.yml` action versions bumped to v6
- [x] `registry.json`: steam-mcp `npm` field set to `@tmhs/steam-mcp`

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
