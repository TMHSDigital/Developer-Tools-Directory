# Developer Tools Directory

**Centralized catalog, standards, and scaffolding for TMHSDigital Cursor IDE plugins, MCP servers, and developer tools.**

![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/license-CC--BY--NC--ND--4.0-green)

---

> 9 repos -- 186 skills -- 77 rules -- 377 MCP tools

## Tools

| Tool | Type | Skills | Rules | MCP Tools | Links |
| --- | --- | ---: | ---: | ---: | --- |
| **CFX Developer Tools** | Plugin | 9 | 6 | 6 | [Repo](https://github.com/TMHSDigital/CFX-Developer-Tools) - [Docs](https://tmhsdigital.github.io/CFX-Developer-Tools/) |
| **Unity Developer Tools** | Plugin | 18 | 8 | 4 | [Repo](https://github.com/TMHSDigital/Unity-Developer-Tools) |
| **Docker Developer Tools** | Plugin | 17 | 10 | 150 | [Repo](https://github.com/TMHSDigital/Docker-Developer-Tools) - [Docs](https://tmhsdigital.github.io/Docker-Developer-Tools/) |
| **Home Lab Developer Tools** | Plugin | 22 | 11 | 50 | [Repo](https://github.com/TMHSDigital/Home-Lab-Developer-Tools) - [Docs](https://tmhsdigital.github.io/Home-Lab-Developer-Tools/) |
| **Mobile App Developer Tools** | Plugin | 43 | 12 | 36 | [Repo](https://github.com/TMHSDigital/Mobile-App-Developer-Tools) |
| **Plaid Developer Tools** | Plugin | 17 | 7 | 30 | [Repo](https://github.com/TMHSDigital/Plaid-Developer-Tools) |
| **Monday Cursor Plugin** | Plugin | 21 | 8 | 45 | [Repo](https://github.com/TMHSDigital/Monday-Cursor-Plugin) - [Docs](https://tmhsdigital.github.io/Monday-Cursor-Plugin/) |
| **Steam Cursor Plugin** | Plugin | 30 | 9 | 25 | [Repo](https://github.com/TMHSDigital/Steam-Cursor-Plugin) - [Docs](https://tmhsdigital.github.io/Steam-Cursor-Plugin/) |
| **Steam MCP Server** | MCP Server | 0 | 0 | 25 | [Repo](https://github.com/TMHSDigital/steam-mcp) - [npm](https://www.npmjs.com/package/@tmhs/steam-mcp) |

## Standards

Documented conventions for building new developer tools. See the full standards in [`standards/`](standards/).

| Standard | Summary |
| --- | --- |
| [Folder Structure](standards/folder-structure.md) | Canonical repo layout for plugins and MCP servers |
| [Plugin Manifest](standards/plugin-manifest.md) | `.cursor-plugin/plugin.json` specification |
| [CI/CD](standards/ci-cd.md) | GitHub Actions workflows every repo must have |
| [GitHub Pages](standards/github-pages.md) | Documentation site setup (static HTML or MkDocs) |
| [Commit Conventions](standards/commit-conventions.md) | Conventional commits and version bumping rules |
| [README Template](standards/readme-template.md) | Standard README structure |
| [AGENTS.md Template](standards/agents-template.md) | AI agent guidance file structure |
| [Versioning](standards/versioning.md) | Semver management and release flow |

## Scaffold Generator

Generate a fully standards-compliant repository from the command line.

### Prerequisites

```bash
pip install Jinja2
```

### Usage

```bash
python scaffold/create-tool.py \
  --name "Unreal Developer Tools" \
  --description "Cursor plugin for Unreal Engine development" \
  --mcp-server \
  --skills 5 \
  --rules 3
```

### Options

| Flag | Required | Default | Description |
| --- | --- | --- | --- |
| `--name` | Yes | -- | Display name (e.g., "Unreal Developer Tools") |
| `--description` | Yes | -- | One-line description |
| `--slug` | No | auto | Kebab-case identifier (derived from name) |
| `--type` | No | `cursor-plugin` | `cursor-plugin` or `mcp-server` |
| `--mcp-server` | No | false | Include MCP server scaffold |
| `--skills N` | No | 0 | Number of placeholder skill directories |
| `--rules N` | No | 0 | Number of placeholder rule files |
| `--license` | No | `cc-by-nc-nd-4.0` | `cc-by-nc-nd-4.0`, `mit`, or `apache-2.0` |
| `--output` | No | `./output` | Output directory |
| `--author-name` | No | TMHSDigital | Author name for manifests |
| `--author-email` | No | contact@... | Author email |

### What It Generates

- Full folder structure per the [standard](standards/folder-structure.md)
- Populated `plugin.json` with provided metadata
- All 4 core GitHub Actions workflows (validate, release, pages, stale)
- Skeleton docs: `AGENTS.md`, `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `ROADMAP.md`
- GitHub Pages site template (`docs/index.html`)
- MCP server scaffold (if `--mcp-server` flag)
- `.cursorrules`, `.gitignore`, `LICENSE`

## Catalog Site

Browse all tools visually at the [GitHub Pages catalog](https://tmhsdigital.github.io/Developer-Tools-Directory/).

## Project Structure

```
Developer-Tools-Directory/
  .github/workflows/     CI/CD for this repo (validate, pages)
  docs/                  GitHub Pages catalog site
  scaffold/              Repo generator script + Jinja2 templates
  standards/             Convention documentation
  registry.json          Tool registry (source of truth)
  README.md
```

## License

CC-BY-NC-ND-4.0 -- see [LICENSE](LICENSE) for details.

---

**Built by [TMHSDigital](https://github.com/TMHSDigital)**
