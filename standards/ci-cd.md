# CI/CD Standards

Every developer tool repository must have these four core GitHub Actions workflows. Optional workflows are documented at the end.

## Core Workflows

### 1. `validate.yml`

**Triggers:** `push` to `main`, `pull_request` to `main`

Validates the structural integrity of the plugin before merging.

**Required checks:**

| Check | Description |
| --- | --- |
| JSON validity | `plugin.json` (and `mcp.json` if present) parse without errors |
| Manifest fields | All required fields exist, `name` is kebab-case |
| Skill file existence | Every path in `plugin.json` `skills` array points to a real file |
| Rule file existence | Every path in `plugin.json` `rules` array points to a real file |
| Frontmatter | Skills have YAML frontmatter starting with `---`; rules have `.mdc` frontmatter |
| Credential scanning | No hardcoded passwords, API keys, or tokens in source files |

**Conditional checks (include if applicable):**

| Check | Condition |
| --- | --- |
| Python syntax | If `mcp-server/` exists, `py_compile` all `.py` files |
| Test suite | If `tests/` exists, run `pytest tests/ -v` |
| Content counts | If README contains stat counts, verify they match actual file counts |

### 2. `release.yml`

**Triggers:** `push` to `main` (with `paths-ignore` for docs, markdown, and `.github/` changes)

Automatic version bump, tagging, and GitHub Release creation.

**Flow:**

1. Read current version from `.cursor-plugin/plugin.json`
2. Parse commit messages since last tag for bump type:
   - `feat!:` or `BREAKING CHANGE` = major
   - `feat:` = minor
   - Everything else = patch
3. Compute new semver version
4. Update `plugin.json` version and `README.md` version badge
5. Commit with `chore: bump version to X.Y.Z [skip ci]`
6. Create git tag `vX.Y.Z`
7. Create GitHub Release with grouped release notes
8. Sync repo About section (description, homepage, topics) via `gh repo edit`

**Requirements:**

- `concurrency: { group: release, cancel-in-progress: false }` to prevent race conditions
- `permissions: contents: write`
- `fetch-depth: 0` on checkout for full git history

### 3. `pages.yml`

**Triggers:** `push` to `main` (paths: `docs/**`, `assets/**`), `workflow_dispatch`

Deploys the `docs/` directory to GitHub Pages.

**Static HTML approach (default):**

```yaml
steps:
  - uses: actions/checkout@v4
  - name: Copy assets into docs
    run: cp -r assets docs/assets
  - uses: actions/configure-pages@v5
  - uses: actions/upload-pages-artifact@v4
    with:
      path: docs
  - uses: actions/deploy-pages@v5
```

**MkDocs approach (for repos with extensive docs):**

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with:
      python-version: "3.12"
  - run: pip install mkdocs-material
  - run: mkdocs build --strict
  - uses: actions/upload-pages-artifact@v3
    with:
      path: site/
  - uses: actions/deploy-pages@v4
```

**Required permissions:**

```yaml
permissions:
  pages: write
  id-token: write
```

### 4. `stale.yml`

**Triggers:** `schedule` (daily or weekly), `workflow_dispatch`

Marks issues and PRs as stale after inactivity and closes them after further inactivity. Use `actions/stale` with sensible defaults (e.g., 30 days stale, 7 days to close).

## Optional Workflows

| Workflow | Purpose | When to include |
| --- | --- | --- |
| `codeql.yml` | Security scanning via GitHub CodeQL | Repos with substantial code (MCP servers, TypeScript packages) |
| `dependency-review.yml` | PR dependency audit | Repos with external dependencies |
| `release-drafter.yml` | Draft release notes automatically | Repos with frequent PRs |
| `ci.yml` | Extended test/lint/build pipeline | Repos with complex test suites |
| Domain-specific update | Auto-fetch external data (e.g., native DBs, API schemas) | Repos that consume external data |

## Workflow Naming

- Use lowercase with hyphens: `validate.yml`, `release.yml`, `pages.yml`
- The `name:` field inside the workflow should be title case: `Validate`, `Release`, `Deploy GitHub Pages`
- Job names should be descriptive: `validate-json`, `bump-version-and-release`, `deploy`

## Secrets and Permissions

- Use `${{ secrets.GITHUB_TOKEN }}` (automatically provided) for all Git operations
- Never store custom secrets unless absolutely required (e.g., npm publish tokens)
- Set minimal `permissions` at the workflow level, not at the job level

## Branch Protection and Merge Policy

Every repo must protect `main` with a GitHub ruleset or classic branch protection that enforces the following. The meta-repo's `main protection` ruleset is the reference implementation.

**Required rules:**

- Direct pushes to `main` blocked; all changes land via pull request.
- Force pushes blocked (`non_fast_forward`).
- Branch deletion blocked.
- Empty bypass-actors list (policy applies to repo owner and admins).
- Squash-merge only. Merge commits and rebase merges should be disabled.

**Required status checks** (minimum for plugin/tool repos):

- JSON/manifest validation job
- Skill and rule file-existence job
- Credential-scanning / safety-scan job
- `CodeQL` (if the repo includes source code substantive enough to scan)
- Any repo-specific sync-check or safety-scan jobs

Repos using the meta-repo's `VERSION`-file-driven release model additionally require:

- `Check VERSION vs latest tag`
- `feat/fix commits require VERSION bump`

Required approvals are a per-repo decision: solo-maintainer repos may set 0 approvals provided all other gates pass; multi-maintainer repos should require at least 1.

**Configuration lives in repo settings, not in git.** Document the current ruleset in `.github/workflows/README.md` so the state is discoverable without admin access.

> Note: the tool-repo release model described in `release.yml` above uses conventional-commit auto-bumps and does not currently require the `VERSION`/`version-bump-check` gates. The meta-repo deviates intentionally. A decision on whether to propagate the `VERSION`-file model to tool repos is deferred; see `ROADMAP.md`.
