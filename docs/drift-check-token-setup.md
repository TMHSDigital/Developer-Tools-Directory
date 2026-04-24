# `DRIFT_CHECK_TOKEN` setup

The drift checker's `--all` / `--remote` mode sparse-checks every active
tool repo from the registry. This requires cross-repo read access that
the workflow's auto-issued `GITHUB_TOKEN` does not have. `DRIFT_CHECK_TOKEN`
is the dedicated fine-grained PAT that fills that gap.

## What it does

| Mode    | Token used                  | What it can do                        |
| ------- | --------------------------- | ------------------------------------- |
| `self`  | `GITHUB_TOKEN` (default)    | check the calling repo's checkout     |
| `all`   | `DRIFT_CHECK_TOKEN`         | sparse-checkout every registry entry  |
| sticky  | `DRIFT_CHECK_TOKEN`         | open / edit / close issues on meta-repo |

The composite action accepts the token as the `github-token` input. The
meta-repo workflow falls back to `GITHUB_TOKEN` if `DRIFT_CHECK_TOKEN` is
unset:

```yaml
github-token: ${{ secrets.DRIFT_CHECK_TOKEN || secrets.GITHUB_TOKEN }}
```

## Required scopes

Create a **fine-grained** PAT (not classic) at
<https://github.com/settings/personal-access-tokens>.

**Resource owner:** `TMHSDigital` (the org that owns all 9 tool repos)

**Repository access:** select all 9 active registry repos:

- `TMHSDigital/Developer-Tools-Directory` (the meta-repo itself)
- `TMHSDigital/CFX-Developer-Tools`
- `TMHSDigital/Unity-Developer-Tools`
- `TMHSDigital/Docker-Developer-Tools`
- `TMHSDigital/Home-Lab-Developer-Tools`
- `TMHSDigital/Mobile-App-Developer-Tools`
- `TMHSDigital/Plaid-Developer-Tools`
- `TMHSDigital/Monday-Cursor-Plugin`
- `TMHSDigital/Steam-Cursor-Plugin`
- `TMHSDigital/steam-mcp`

**Repository permissions:**

| Permission | Level | Why                                                       |
| ---------- | ----- | --------------------------------------------------------- |
| Contents   | Read  | sparse-checkout `AGENTS.md`, `CLAUDE.md`, `skills/`, `rules/` |
| Metadata   | Read  | mandatory for any fine-grained PAT                        |

The drift checker does NOT need `Issues: Write` on `DRIFT_CHECK_TOKEN`.
Sticky-issue upsert uses the workflow's auto-issued `GITHUB_TOKEN` (with
`issues: write` granted in the workflow's `permissions:` block) instead,
because fine-grained PATs can have inconsistent GraphQL access — the
`updateIssue` mutation has been observed to fail with "Resource not
accessible" even when the REST `createIssue` succeeds. Two-token model:

- `DRIFT_CHECK_TOKEN` → cross-repo `Contents: Read`
- `GITHUB_TOKEN` → same-repo `Issues: Write`

**Expiration:** 90 days is recommended. Calendar a rotation.

## Add it as a repo secret

```pwsh
gh secret set DRIFT_CHECK_TOKEN `
  --repo TMHSDigital/Developer-Tools-Directory `
  --body "<paste-pat>"
```

Or via the web UI: <https://github.com/TMHSDigital/Developer-Tools-Directory/settings/secrets/actions/new>

## Verify

```pwsh
gh secret list --repo TMHSDigital/Developer-Tools-Directory
```

Should list `DRIFT_CHECK_TOKEN`. Trigger a smoke run:

```pwsh
gh workflow run drift-check.yml `
  --repo TMHSDigital/Developer-Tools-Directory
gh run watch
```

The run completes and writes a step summary even if drift is present
(exit code 1 is the "drift found" signal, not a failure).

## Fallback behavior

If `DRIFT_CHECK_TOKEN` is unset, the workflow falls back to
`GITHUB_TOKEN`. The implications:

| Operation          | Without `DRIFT_CHECK_TOKEN`   |
| ------------------ | ----------------------------- |
| `mode=self`        | works (meta-repo only)        |
| `mode=all`         | fails (cannot read tool repos) |
| sticky issue       | works (issues on meta-repo)   |

Tool-repo workflows that consume the composite action via `mode=self`
do NOT need `DRIFT_CHECK_TOKEN`; their own `GITHUB_TOKEN` is enough.

## Rotation

When the PAT nears expiration:

1. Create the new token with the same scopes.
2. `gh secret set DRIFT_CHECK_TOKEN --body "<new>"` — overwrites in place.
3. Trigger one `workflow_dispatch` run to confirm.
4. Revoke the old token at
   <https://github.com/settings/personal-access-tokens>.

If the old token is revoked before the new one is uploaded, the next
scheduled run fails fast on the first sparse-checkout. Sticky-issue
state is unaffected.
