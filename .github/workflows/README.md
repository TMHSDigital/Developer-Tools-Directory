# Workflows

CI/CD for the Developer Tools Directory meta-repo. See [`standards/ci-cd.md`](../../standards/ci-cd.md) for the ecosystem-wide standard that applies to tool repos.

## Files

| File | Trigger | Purpose |
|------|---------|---------|
| `validate.yml` | PR and push to main | Registry schema, docs existence, scaffold dry-run, sync-check, safety scan, version-bump-check |
| `sync.yml` | Push to main (registry.json changes), manual | Regenerate derived artifacts and open a PR |
| `pages.yml` | Push to main (docs/, assets/, registry.json changes) | Deploy catalog site to GitHub Pages |
| `release.yml` | Push to main (code changes) | Release when `VERSION` is ahead of latest tag; no-op if equal; fail if lower |
| `release-drafter.yml` | PR activity and push to main | Draft release notes from PRs |
| `stale.yml` | Weekly schedule | Mark and close inactive issues and PRs |
| `codeql.yml` | Push/PR to main and weekly schedule | CodeQL security scanning |
| `dependency-review.yml` | PR to main | Audit new dependencies |
| `label-sync.yml` | PR open/sync | Auto-label PRs by changed paths |

## Action pinning convention

Third-party actions are pinned by full commit SHA, with the version tag in a comment:

```yaml
- uses: peter-evans/create-pull-request@c5a7806660adbe173f04e3e038b0ccdcd758773c # v6.1.0
```

First-party GitHub actions (`actions/`, `github/`) may use a major-version tag:

```yaml
- uses: actions/checkout@v6
- uses: actions/setup-python@v5
```

Rationale: tags are mutable and can be retargeted to a malicious commit. SHAs are immutable. GitHub-owned actions are exempt because GitHub's own security model protects them.

## Permissions

Every workflow has `permissions: {}` at the top level. Jobs grant only what they need, explicitly:

```yaml
permissions: {}

jobs:
  my-job:
    permissions:
      contents: read
      pull-requests: write
```

Never use `permissions: write-all`.

## Branch protection expectations

`CODEOWNERS` and the `sync-check` / `safety-scan` jobs are only meaningful when branch protection on `main` enforces them. The expected settings:

- Require a pull request before merging.
- Require review from Code Owners.
- Require status checks to pass: `validate-registry`, `validate-docs`, `validate-scaffold`, `sync-check`, `safety-scan`.
- Require signed commits (DCO App verifies `Signed-off-by:` on every commit).
- Disallow force pushes to `main`.
- Disallow deletion of `main`.

These settings are not code; they must be configured in the repository settings. A maintainer change to branch protection does not show up in git history, so this file is the canonical record.

## Forbidden patterns

- `pull_request_target` combined with `actions/checkout` of PR code (RCE vector from forks).
- `${{ github.event.* }}` interpolated directly into a `run:` block (command injection).
- `eval` or `bash -c` with untrusted event data.
- Custom PATs for admin operations where the default `GITHUB_TOKEN` suffices.

## The About section

The GitHub About section (description, homepage, topics) is not updated by any workflow. The `GITHUB_TOKEN` does not have `administration:write`, and storing a PAT with that scope would create a supply-chain risk.

Instead, the maintainer runs:

```bash
python scripts/sync_from_registry.py --about
```

The command prints a `gh repo edit ...` invocation. The maintainer reviews and runs it locally.

## Updating a pinned SHA

When a third-party action releases a new version:

1. Find the commit SHA for the tag on GitHub (Actions tab or Releases page).
2. Update the `uses:` line with the new SHA and update the version comment.
3. Commit with `chore: bump <action> to <version>`.
4. Do not update multiple unrelated actions in the same commit.

## Known follow-ups

- `release-drafter/release-drafter@v6` in `release-drafter.yml` is still pinned by major tag. It runs under `pull_request_target` but does not check out PR code, so the fork-RCE vector does not apply. SHA-pinning tracked for v1.7.
- `peter-evans/create-pull-request` in `sync.yml` is SHA-pinned. Update as releases land.
