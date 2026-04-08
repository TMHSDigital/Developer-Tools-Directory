# Folder Structure

Canonical repository layout for TMHSDigital developer tool repos. Items marked **(optional)** may be omitted if the repo does not need them.

```
<tool-name>/
  .cursor-plugin/
    plugin.json               # Plugin manifest -- version source of truth
  .cursor/                    # (optional) Cursor IDE config
    mcp.json                  # MCP server connection config
  .cursorrules                # Root cursor rules file
  .github/
    workflows/
      validate.yml            # PR/push validation checks
      release.yml             # Auto version bump + GitHub Release
      stale.yml               # Stale issue/PR cleanup
      pages.yml               # GitHub Pages deployment
    scripts/                  # (optional) CI helper scripts
  assets/
    logo.png                  # 512x512 plugin logo
    logo-docs.png             # (optional) Logo variant for docs site
    favicon.png               # (optional) 32x32 favicon
  docs/
    index.html                # GitHub Pages landing page
    assets/                   # (optional) Docs-specific static assets
  mcp-server/                 # (optional) Python MCP server
    server.py                 # Entry point
    tools/                    # Tool module files
    data/                     # JSON data files
    requirements.txt          # Pinned Python dependencies
  rules/                      # Cursor rule files (.mdc)
  skills/                     # AI skill directories
    <skill-name>/
      SKILL.md                # Skill definition with YAML frontmatter
  snippets/                   # (optional) Code snippet files
  templates/                  # (optional) Starter project templates
  tests/                      # (optional) Test suite
  AGENTS.md                   # AI agent guidance
  CHANGELOG.md                # Manually maintained release history
  CLAUDE.md                   # (optional) Claude Code agent guidance
  CODE_OF_CONDUCT.md          # (optional) Community code of conduct
  CONTRIBUTING.md             # Contribution guidelines
  LICENSE                     # CC-BY-NC-ND-4.0 by default
  README.md                   # Project README
  ROADMAP.md                  # (optional) Release roadmap
  SECURITY.md                 # (optional) Security policy
```

## Key Conventions

### `.cursor-plugin/plugin.json`

This is the **only** source of truth for the current version. The release workflow reads and writes it. Never manually edit the `version` field.

### `skills/<name>/SKILL.md`

Each skill lives in its own directory. The `SKILL.md` file must start with YAML frontmatter containing at minimum `title`, `description`, and `globs`.

### `rules/<name>.mdc`

Rule files use `.mdc` extension and must start with YAML frontmatter containing `description`, `globs`, and `alwaysApply`.

### `docs/`

For GitHub Pages deployment. Can be a static HTML site (recommended) or the source for an MkDocs Material build. See [GitHub Pages](github-pages.md).

### `mcp-server/`

Only present in repos that bundle a Python MCP server. The server is configured in `.cursor/mcp.json` and starts automatically when Cursor invokes a tool.

### `tests/`

When present, tests are run by the `validate.yml` workflow. Use `pytest` for Python MCP servers.

## Files That CI Manages

Do **not** manually edit these -- the release workflow owns them:

- `version` field in `.cursor-plugin/plugin.json`
- Version badge in `README.md`
- Git tags (`vX.Y.Z`)
- GitHub Releases
- GitHub repo About section (description, homepage, topics)

## Files You Maintain Manually

- `CHANGELOG.md` -- update when making significant changes
- All skill, rule, snippet, and template content
- `AGENTS.md` and `CLAUDE.md`
- `README.md` (except the version badge)
