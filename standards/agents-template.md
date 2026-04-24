# AGENTS.md Template

Every developer tool repo must include an `AGENTS.md` file at the root. This file tells AI coding agents how the repository works and how to contribute correctly.

## Required Sections

### 1. Header

Every `AGENTS.md` and `CLAUDE.md` in a tool repo must start with a `standards-version` marker on the first line, followed by a blank line, followed by the H1 title. The marker is an HTML comment so it does not render in GitHub's Markdown viewer.

```markdown
<!-- standards-version: X.Y.Z -->

# AGENTS.md

This file tells AI coding agents how the <Tool Name> repo works
and how to contribute correctly.

**Documentation site:** <URL> (auto-deployed on push to main)
```

`X.Y.Z` matches the `Developer-Tools-Directory` `VERSION` the tool repo is aligned with. Update it when the tool repo is re-aligned with a new meta-repo release; do not update it on every commit.

**Rationale:** the HTML comment format preserves the pure-Markdown, prose-first convention of `AGENTS.md` and `CLAUDE.md` (no YAML frontmatter in files that render as rendered docs), while giving the drift checker in `Developer-Tools-Directory` a deterministic signal to detect which version of the ecosystem standards a tool repo was last aligned with.

`SKILL.md` and `.mdc` rule files use a different mechanism: a YAML frontmatter field named `standards-version`, placed alongside `name`, `description`, `globs`, `alwaysApply`. Those files are metadata-first component files rather than prose documents, so frontmatter is the natural home for the signal. See `standards/skills.md` and `standards/rules.md` for the full frontmatter conventions.

### 2. Repository Overview

List every top-level directory and file with a brief description. Use the same format as the folder structure standard:

```markdown
## Repository overview

This is a Cursor IDE plugin for <domain>. It contains:

- **`.cursor-plugin/plugin.json`** -- plugin manifest (version, skills, rules)
- **`skills/`** -- X SKILL.md files teaching the AI domain-specific knowledge
- **`rules/`** -- Y .mdc rule files enforcing coding conventions
- **`mcp-server/`** -- Python MCP server with Z tools and JSON data files
- **`docs/`** -- documentation and GitHub Pages site
```

### 3. Branching and Commit Model

```markdown
## Branching and commit model

- **Single branch**: `main` only. No develop/release branches.
- **Conventional commits** are required. The release workflow parses them:
  - `feat:` -- triggers a **minor** version bump
  - `feat!:` or `BREAKING CHANGE` -- triggers a **major** version bump
  - Everything else -- triggers a **patch** bump
- Commit messages should be concise and describe the "why", not the "what".
```

### 4. CI/CD Workflows

Describe each workflow in the repo, what it does, and what triggers it. Include any important caveats (e.g., "do not manually edit the version").

### 5. Version Management

```markdown
## Version management

- The **source of truth** for the current version is `.cursor-plugin/plugin.json`.
- The release workflow auto-bumps it and the README badge on every qualifying
  push to main.
- Never manually change the version.
```

### 6. Code Conventions

List project-specific rules that AI agents must follow. Examples:

- File naming conventions
- Forbidden patterns (e.g., no em dashes, no hardcoded credentials)
- Required fields in data files
- Language-specific conventions

### 7. Adding Content

Step-by-step checklists for common tasks:

```markdown
### New skill

1. Create `skills/<name>/SKILL.md` with YAML frontmatter
2. Add the path to `plugin.json` under `"skills"`
3. Update counts in README.md
4. Use `feat:` commit prefix

### New rule

1. Create `rules/<name>.mdc` with frontmatter
2. Add the path to `plugin.json` under `"rules"`
```

### 8. MCP Server (if applicable)

Document the MCP server's entry point, tool modules, data files, and how they connect.

### 9. Key Technical Facts

Domain-specific knowledge that AI agents need to generate correct code. List as bullet points.

### 10. License

State the license so agents know to include it in generated content.

## Guidelines

- Be specific and actionable. Agents follow instructions literally.
- Include file paths, not just descriptions.
- Explain what CI will reject so agents avoid those patterns.
- Update `AGENTS.md` whenever you add workflows, change conventions, or restructure the repo.
