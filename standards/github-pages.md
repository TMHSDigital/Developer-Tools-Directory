# GitHub Pages

Every developer tool repo should have a documentation site deployed to GitHub Pages at `https://tmhsdigital.github.io/<repo-name>/`.

## Approach 1: Static HTML (Recommended Default)

A self-contained `docs/index.html` with inline or co-located CSS/JS. No build step required.

### File Structure

```
docs/
  index.html        # Single-page landing site
  style.css          # (optional) External stylesheet
  script.js          # (optional) External JavaScript
  assets/            # Images referenced by the page
```

### Design Guidelines

- **Dark theme** with a color accent matching the tool's domain
- **Hero section** with plugin name, one-line description, and key stat badges (skills, rules, MCP tools)
- **Feature cards** summarizing capabilities
- **Quick start** section with install/usage instructions
- **Links** to the GitHub repo, README, and related tools
- **Responsive** layout -- works on mobile
- **No external CDN dependencies** -- everything self-contained

### Deployment Workflow (`pages.yml`)

```yaml
name: Deploy GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - "docs/**"
      - "assets/**"
  workflow_dispatch:

permissions:
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Copy assets into docs
        run: cp -r assets docs/assets
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v4
        with:
          path: docs
      - uses: actions/deploy-pages@v5
        id: deployment
```

### GitHub Setup

1. Go to repo Settings > Pages
2. Set Source to **GitHub Actions**
3. The workflow handles the rest

## Approach 2: MkDocs Material

For repos with extensive documentation (multiple pages, skill docs, API references). Uses [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) to build a full documentation site from Markdown.

### When to Use MkDocs

- The repo has 5+ pages of documentation
- Skill files need to be browsable online
- An architecture guide, getting-started tutorial, or API reference exists

### File Structure

```
mkdocs.yml              # MkDocs configuration (repo root)
docs/
  index.md              # Landing page
  GETTING-STARTED.md
  ARCHITECTURE.md
  CONTRIBUTING.md
  ROADMAP.md
  CHANGELOG.md
  skills/               # Symlinked or copied from repo skills/
  mcp-server/           # Symlinked or copied
  assets/
    logo.png
    logo-docs.png
    favicon.png
```

### Minimal `mkdocs.yml`

```yaml
site_name: <Tool Name>
site_url: https://tmhsdigital.github.io/<repo-name>/
site_description: <One-line description>
site_author: TMHSDigital
repo_url: https://github.com/TMHSDigital/<repo-name>
repo_name: TMHSDigital/<repo-name>
edit_uri: edit/main/

theme:
  name: material
  palette:
    - scheme: slate
      primary: deep purple
      accent: amber
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
    - scheme: default
      primary: deep purple
      accent: amber
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
  features:
    - navigation.instant
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy

markdown_extensions:
  - admonition
  - attr_list
  - tables
  - toc:
      permalink: true
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.details
```

### Deployment Workflow (`deploy-docs.yml`)

```yaml
name: Deploy Documentation

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install mkdocs-material
      - name: Copy content into docs/
        run: |
          # Copy files that live outside docs/ but need to be in the site
          cp CHANGELOG.md docs/CHANGELOG.md
          cp -r skills docs/skills
      - run: mkdocs build --strict
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site/
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```
