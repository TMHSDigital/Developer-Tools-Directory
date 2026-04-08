# Plugin Manifest

The `.cursor-plugin/plugin.json` file is the plugin manifest. It declares the plugin's identity, contents, and metadata.

## Required Fields

| Field | Type | Description |
| --- | --- | --- |
| `name` | `string` | Kebab-case identifier (e.g., `cfx-developer-tools`). Must match `^[a-z0-9]+(-[a-z0-9]+)*$`. |
| `displayName` | `string` | Human-readable name shown in the marketplace |
| `description` | `string` | One-line summary of what the plugin does |
| `version` | `string` | Semver version (e.g., `1.0.0`). **Managed by CI -- do not edit manually.** |
| `author` | `object` | `{ "name": "TMHSDigital", "email": "..." }` |
| `license` | `string` | SPDX identifier (e.g., `CC-BY-NC-ND-4.0`) |
| `keywords` | `string[]` | Discovery tags for the marketplace |
| `skills` | `string[]` | Relative paths to SKILL.md files |
| `rules` | `string[]` | Relative paths to .mdc rule files |

## Example

```json
{
  "name": "example-developer-tools",
  "displayName": "Example Developer Tools",
  "description": "Cursor IDE plugin for Example development",
  "version": "1.0.0",
  "author": {
    "name": "TMHSDigital",
    "email": "contact@tmhospitalitystrategies.com"
  },
  "license": "CC-BY-NC-ND-4.0",
  "keywords": ["example", "cursor-plugin", "mcp"],
  "skills": [
    "skills/getting-started/SKILL.md",
    "skills/advanced-usage/SKILL.md"
  ],
  "rules": [
    "rules/code-conventions.mdc",
    "rules/security.mdc"
  ]
}
```

## Validation

The `validate.yml` workflow checks:

1. JSON is syntactically valid
2. All required fields are present
3. `name` is lowercase kebab-case
4. Every path in `skills` points to an existing file
5. Every path in `rules` points to an existing file

## Version Management

The `version` field is the **single source of truth** for the project version. The release workflow:

1. Reads the current version from this file
2. Determines the bump type from conventional commit messages
3. Computes the new semver version
4. Writes the new version back to this file
5. Updates the README badge to match
6. Commits with `[skip ci]`, tags, and creates a GitHub Release

Never manually change the version. If you need to force a specific version, do so through the release workflow or by creating a manual tag.
