# Unified GitHub Pages Setup Prompt

Copy the prompt below and paste it into Cursor in any tool repo that needs a GitHub Pages site wired to the unified template.

---

## Prompt

```
You are setting up this repo's GitHub Pages site to use the unified auto-sync template from the Developer-Tools-Directory repo (https://github.com/TMHSDigital/Developer-Tools-Directory).

The template system works like this:
- A Python build script (site-template/build_site.py) in Developer-Tools-Directory reads data from THIS repo and generates docs/index.html
- It reads: .cursor-plugin/plugin.json, site.json, skills/*/SKILL.md, rules/*.mdc, and mcp-tools.json
- The pages.yml workflow clones Developer-Tools-Directory at deploy time, runs the build, and deploys docs/

Your tasks:

1. **Create `site.json`** in the repo root with branding config. Use colors that match this tool's brand identity:

{
  "accent": "#BRAND_COLOR",
  "accentLight": "#LIGHTER_VARIANT",
  "heroGradientFrom": "#0d1117",
  "heroGradientTo": "#161b22",
  "favicon": "assets/logo.png",
  "ogImage": "assets/logo.png",
  "installSteps": [
    "Clone the repository",
    "Open the folder in Cursor IDE",
    "TOOL-SPECIFIC INSTALL STEP HERE",
    "Start using the AI skills and rules"
  ],
  "links": {
    "github": "https://github.com/TMHSDigital/THIS-REPO-NAME"
  }
}

If this repo has an npm package, add "npm": "https://www.npmjs.com/package/@tmhs/PACKAGE" to links.

2. **Create `mcp-tools.json`** in the repo root. Scan the MCP server source code (or documentation in CLAUDE.md / README.md) for all registered tool names and descriptions. Format as:

[
  {"name": "tool_name", "description": "What it does", "category": "Logical Group"}
]

Group tools into logical categories. If there's no MCP server, use an empty array [].

3. **Update `.github/workflows/pages.yml`** to this exact structure:

name: Deploy GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - "skills/**"
      - "rules/**"
      - "mcp-tools.json"
      - "site.json"
      - ".cursor-plugin/plugin.json"
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
      - uses: actions/checkout@v6

      - uses: actions/checkout@v6
        with:
          repository: TMHSDigital/Developer-Tools-Directory
          path: _template
          sparse-checkout: site-template

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r _template/site-template/requirements.txt

      - name: Build site
        run: python _template/site-template/build_site.py --repo-root . --out docs

      - name: Configure Pages
        uses: actions/configure-pages@v6

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v4
        with:
          path: docs

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v5

4. **Verify** the repo has .cursor-plugin/plugin.json with displayName, description, version, author, repository, and license fields. If any are missing, add them.

5. **Commit and push** all changes with message: feat: switch to unified auto-sync GitHub Pages template

Do NOT modify the existing skills/, rules/, or .cursor-plugin/plugin.json content -- only add the new files and update the workflow.
```
