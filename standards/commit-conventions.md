# Commit Conventions

All TMHSDigital developer tool repos use [Conventional Commits](https://www.conventionalcommits.org/). The release workflow parses commit messages to determine version bumps automatically.

## Format

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

- **type** is required
- **scope** is optional (e.g., `feat(mcp):`, `fix(skills):`)
- **description** is a concise summary of the change -- describe the "why", not the "what"

## Types and Version Bumps

| Type | Bump | When to use |
| --- | --- | --- |
| `feat:` | **minor** | A new feature, skill, rule, MCP tool, or capability |
| `feat!:` | **major** | A breaking change (also triggered by `BREAKING CHANGE` in footer) |
| `fix:` | patch | A bug fix |
| `chore:` | patch | Maintenance, dependency updates, CI changes |
| `docs:` | patch | Documentation-only changes |
| `refactor:` | patch | Code restructuring without behavior change |
| `test:` | patch | Adding or updating tests |
| `style:` | patch | Formatting, whitespace, linting fixes |
| `perf:` | patch | Performance improvements |
| `ci:` | patch | CI/CD workflow changes |

## Examples

```
feat: add state-bags skill for entity data sync

fix(mcp): handle missing category field in native lookup

chore: bump mkdocs-material to 9.5

docs: add troubleshooting section to getting-started guide

feat!: rename scaffold_resource_tool to scaffold_tool

feat(skills): add NUI Svelte template

BREAKING CHANGE: remove deprecated lua54 directive support
```

## Rules

1. **One logical change per commit.** Don't bundle unrelated changes.
2. **Use imperative mood** in the description: "add feature" not "added feature" or "adding feature".
3. **Keep the first line under 72 characters.**
4. **The release workflow skips commits with `[skip ci]`** in the message. This is used by the release workflow itself when it commits version bumps.
5. **CI-only changes** (edits to `.github/`, `docs/`, `*.md`, `LICENSE`, `mkdocs.yml`) are excluded from release triggers via `paths-ignore`.

## Breaking Changes

A breaking change triggers a **major** version bump. Signal it with either:

- An exclamation mark after the type: `feat!: remove legacy API`
- A `BREAKING CHANGE` footer in the commit body

Use breaking changes sparingly. Most plugin changes are additive (new skills, rules, tools) and should be `feat:` (minor).
