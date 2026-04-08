# TMHSDigital Developer Tools Standards

Standards and conventions for building Cursor IDE plugins, MCP servers, and developer tool repositories under the TMHSDigital organization.

## Quick Reference

| Standard | Summary |
| --- | --- |
| [Folder Structure](folder-structure.md) | Canonical repo layout for plugins and MCP servers |
| [Plugin Manifest](plugin-manifest.md) | `.cursor-plugin/plugin.json` specification |
| [CI/CD](ci-cd.md) | GitHub Actions workflows every repo must have |
| [GitHub Pages](github-pages.md) | Documentation site setup (static HTML or MkDocs) |
| [Commit Conventions](commit-conventions.md) | Conventional commits and version bumping rules |
| [README Template](readme-template.md) | Standard README structure and required sections |
| [AGENTS.md Template](agents-template.md) | AI agent guidance file structure |
| [Versioning](versioning.md) | Semver management and release flow |

## Principles

1. **Automation first** -- CI handles versioning, releases, badge updates, and repo metadata. Manual edits to managed fields will be overwritten.
2. **Single branch** -- All repos use `main` only. No develop, staging, or release branches.
3. **Conventional commits** -- Every commit message follows the conventional format. The release workflow parses them to determine version bumps.
4. **AI-agent friendly** -- Every repo includes `AGENTS.md` and `.cursorrules` so AI coding agents understand the project structure and conventions.
5. **Public by default** -- Standards, docs, and tooling are written for public consumption. No internal-only references.

## Applying These Standards

New repos should be created using the [scaffold generator](../scaffold/). It produces a fully standards-compliant repository with all required files, workflows, and structure.

Existing repos can adopt these standards incrementally. The standards docs describe what compliance looks like; there is no automated migration tool.
