# Adding a Tool: Worked Example

A complete end-to-end walkthrough of adding a new tool to the Developer Tools Directory, from scaffold to PR to merge. Every command is copy-pasteable. This example adds a fictional tool called "Cloudflare Developer Tools".

## Prerequisites

- A GitHub account in the TMHSDigital organization (or a fork with intent to PR back)
- Python 3.11+ and `pip install -r requirements.txt`
- `git` with DCO sign-off configured (see [`CONTRIBUTING.md`](../../CONTRIBUTING.md))
- `gh` CLI authenticated

## Step 1: Scaffold the tool repo

From your local checkout of Developer-Tools-Directory:

```bash
python scaffold/create-tool.py \
  --name "Cloudflare Developer Tools" \
  --description "Cursor IDE plugin for Cloudflare Workers, Pages, and edge platform workflows" \
  --mcp-server \
  --skills 6 \
  --rules 4 \
  --license CC-BY-NC-ND-4.0 \
  --output ../
```

This produces `../Cloudflare-Developer-Tools/` with the full standards-compliant layout.

## Step 2: Push the new repo

```bash
cd ../Cloudflare-Developer-Tools
git init -b main
git add .
git commit -s -m "feat: initial scaffold"
gh repo create TMHSDigital/Cloudflare-Developer-Tools \
  --public \
  --description "Cursor IDE plugin for Cloudflare Workers, Pages, and edge platform workflows" \
  --homepage "https://tmhsdigital.github.io/Cloudflare-Developer-Tools/"
git remote add origin https://github.com/TMHSDigital/Cloudflare-Developer-Tools.git
git push -u origin main
```

At this point the tool repo exists with placeholder skills and rules. Fill them in over subsequent commits following the per-repo standards.

## Step 3: Populate skills, rules, and MCP tools

Follow [`standards/skills.md`](../../standards/skills.md), [`standards/rules.md`](../../standards/rules.md), and [`standards/mcp-server.md`](../../standards/mcp-server.md). Verify with:

```bash
python -c "
import yaml, pathlib
for p in pathlib.Path('skills').glob('*/SKILL.md'):
    f = p.read_text().split('---', 2)[1]
    meta = yaml.safe_load(f)
    assert 'name' in meta and 'description' in meta and 'triggers' in meta, p
print('skills ok')
"
```

Add tests under `tests/` per [`standards/testing.md`](../../standards/testing.md). CI blocks the merge if tests fail.

## Step 4: Cut a release

```bash
git commit -s --allow-empty -m "feat: first public release"
git push
```

The release workflow tags `v1.0.0` and publishes a GitHub Release. The Pages workflow deploys `https://tmhsdigital.github.io/Cloudflare-Developer-Tools/`.

## Step 5: Register the tool in the directory

Back in your Developer-Tools-Directory checkout:

```bash
git checkout -b feat/register-cloudflare
```

Edit `registry.json`. Add a new entry at the bottom of the array:

```json
{
  "name": "Cloudflare Developer Tools",
  "repo": "TMHSDigital/Cloudflare-Developer-Tools",
  "slug": "cloudflare-developer-tools",
  "description": "Cursor IDE plugin for Cloudflare Workers, Pages, and edge platform workflows",
  "type": "cursor-plugin",
  "homepage": "https://tmhsdigital.github.io/Cloudflare-Developer-Tools/",
  "skills": 6,
  "rules": 4,
  "mcpTools": 20,
  "extras": {},
  "topics": ["cloudflare", "workers", "pages", "edge", "serverless"],
  "status": "beta",
  "version": "1.0.0",
  "language": "TypeScript",
  "license": "CC-BY-NC-ND-4.0",
  "pagesType": "static",
  "hasCI": true
}
```

Status is `beta` on first registration unless the tool meets the `active` graduation checklist in [`standards/lifecycle.md`](../../standards/lifecycle.md).

## Step 6: Regenerate derived artifacts

```bash
python scripts/sync_from_registry.py
```

This updates:
- `README.md` tools table, descriptions, and stats
- `CLAUDE.md` cataloged tools and totals
- `docs/index.html` embedded registry block

Confirm the sync check is clean:

```bash
python scripts/sync_from_registry.py --check
```

Exit code 0 and message `registry sync: ok` means you are good.

## Step 7: Commit and open the PR

```bash
git add registry.json README.md CLAUDE.md docs/index.html
git commit -s -m "feat: add Cloudflare Developer Tools to registry"
git push -u origin feat/register-cloudflare
gh pr create \
  --title "feat: add Cloudflare Developer Tools to registry" \
  --body "Registers the Cloudflare Workers and Pages tool. Status: beta. 6 skills, 4 rules, 20 MCP tools."
```

## Step 8: Address review and merge

The PR triggers:

| Check | What it verifies |
|-------|------------------|
| `validate-registry` | Schema validity of the new entry |
| `validate-scaffold` | Scaffold output still passes leak scan |
| `sync-check` | Derived artifacts match `registry.json` |
| `safety-scan` | No leaked secrets, emails, or drive-letter paths |
| DCO | Every commit signed off |

Fix any failures, push the fix commit signed off. Once green and reviewed by a CODEOWNER, merge with squash.

## Step 9: Update the GitHub About section

After merge, locally:

```bash
git checkout main
git pull
python scripts/sync_from_registry.py --about
```

Copy the printed `gh repo edit ...` command and run it. This updates the directory's About section with the new aggregate stats.

## Step 10: Verify the catalog site

Visit https://tmhsdigital.github.io/Developer-Tools-Directory/ and confirm the new card appears. The Pages deploy runs automatically on merge to `main` when `registry.json`, `docs/`, or `assets/` changes.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Edited README tables manually | Run the sync script; CI will block merge otherwise |
| Forgot `git commit -s` | `git commit --amend -s --no-edit && git push --force-with-lease` |
| Added entry with wrong `type` | Only `cursor-plugin` or `mcp-server` are accepted |
| Counted `skills` as a string `"6"` | Must be an integer |
| Set `status: active` without meeting graduation criteria | Start at `beta`; see [`standards/lifecycle.md`](../../standards/lifecycle.md) |
| Left placeholder business email in scaffold output | Update `--author-email` or let CI's leak scan catch it |

## Timeline

A typical new-tool PR from scaffold to merged directory entry takes one day of focused work:

- 1-2 hours: scaffold, push, populate skills
- 2-3 hours: write rules, MCP tools, tests
- 1 hour: cut release, verify Pages deploy
- 30 min: open registry PR, address review, merge
- 15 min: refresh About section
