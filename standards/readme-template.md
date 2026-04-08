# README Template

Standard structure for TMHSDigital developer tool READMEs. Adapt section content to the specific tool; keep the section order consistent.

## Required Sections

### 1. Title and Badges

```markdown
# <Tool Name>

**<One-line description>**

License: CC BY-NC-ND 4.0
Version
GitHub stars
Documentation
```

The version badge is auto-updated by the release workflow. Use the format `version-X.Y.Z-blue`.

### 2. Navigation Links

```markdown
**Getting Started** - Documentation - Features - Quick Start - MCP Server - Skills - Rules - Roadmap
```

Link to sections within the README and to the external docs site.

### 3. Stats Line

```markdown
> X skills - Y rules - Z MCP tools
```

These counts must match the actual files on disk. The `validate.yml` workflow checks this.

### 4. Description

One paragraph explaining what the plugin does, who it's for, and what it covers.

### 5. How It Works

A Mermaid flowchart showing the relationship between skills, rules, and MCP tools.

### 6. Quick Start

Minimal steps to get the plugin working. Assume the reader already has Cursor installed.

### 7. Features

Bullet list or table of key capabilities.

### 8. Skills Table

| Skill | What it does |
| --- | --- |
| **Skill Name** | One-line description |

### 9. Rules Table

| Rule | What it does |
| --- | --- |
| **Rule Name** | One-line description |

### 10. MCP Tools Table (if applicable)

| Tool | Description |
| --- | --- |
| `tool_name` | One-line description |

### 11. Project Structure

```
<tool-name>/
  .cursor-plugin/     Plugin manifest
  skills/             AI skill files
  rules/              Coding convention rules
  ...
```

### 12. Roadmap

Link to `ROADMAP.md` or inline version table.

### 13. Contributing

Link to `CONTRIBUTING.md`.

### 14. License

State the license and link to `LICENSE`.

### 15. Footer

```markdown
**Built by TMHSDigital**
```

## Guidelines

- Keep the README scannable. Use tables over long prose.
- Do not duplicate content that belongs in `docs/` or skill files.
- Stats in the README must match reality. CI enforces this.
- The release workflow manages the version badge. Don't manually update it.
