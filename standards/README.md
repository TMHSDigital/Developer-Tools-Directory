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
| [Release-doc-sync](release-doc-sync.md) | Composite action contract for keeping CHANGELOG, CLAUDE, and ROADMAP in sync after auto-release |
| [Testing](testing.md) | Test frameworks, minimum coverage bar, CI wiring |
| [Skills](skills.md) | `SKILL.md` structure, frontmatter, and conventions |
| [Rules](rules.md) | `.mdc` structure, globs, and the secrets rule pattern |
| [MCP Server](mcp-server.md) | Tool naming, runtime choice, transport, destructive ops |
| [Security](security.md) | Vulnerability disclosure, secrets, workflow supply chain |
| [Licensing](licensing.md) | DCO + inbound license grant model |
| [Scope](scope.md) | What belongs in the directory and what does not |
| [Lifecycle](lifecycle.md) | Tool status transitions (experimental to archived) |
| [Writing Style](writing-style.md) | Prose conventions across all repos |

## Principles

1. **Derived artifacts are generated, not edited** - `registry.json` is the single source of truth. The README tables, catalog site, and About section are emitted from it. Manual edits drift and get overwritten.
2. **Single branch** - All repos use `main` only. No develop, staging, or release branches.
3. **Conventional commits** - Every commit follows the conventional format. Release workflows parse them to determine version bumps.
4. **AI-agent friendly** - Every repo includes `AGENTS.md` and `.cursorrules`. Standards docs are written so an agent can apply them without guessing.
5. **Inbound DCO, outbound CC-BY-NC-ND-4.0** - Contributors sign off under the Developer Certificate of Origin and grant a broader inbound license so the project can accept pull requests under its outbound license. See [licensing.md](licensing.md).
6. **Scope gate** - Tools must be developer-facing, Cursor or MCP native, and actively maintained. See [scope.md](scope.md).
7. **Lifecycle transitions are explicit** - Tools move through `experimental to beta to active to maintenance to deprecated to archived` with documented criteria. See [lifecycle.md](lifecycle.md).

## Applying These Standards

New repos should be created using the [scaffold generator](../scaffold/). It produces a fully standards-compliant repository with all required files, workflows, and structure.

Existing repos can adopt these standards incrementally. The standards docs describe what compliance looks like; there is no automated migration tool.
