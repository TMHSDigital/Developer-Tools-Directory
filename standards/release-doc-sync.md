# Release-doc-sync

The `release-doc-sync` composite action keeps `CHANGELOG.md`, `CLAUDE.md`, and `ROADMAP.md` aligned with the new `plugin.json` version on every auto-release. It exists because `release.yml` only edits `plugin.json` and the README badge today, which lets doc-consistency tests fail on every PR after a release until the docs are manually updated. This document is the contract that tool-repo `release.yml` workflows consume.

## Source

- Action: `.github/actions/release-doc-sync/action.yml`
- Sync logic: `scripts/release_doc_sync/sync.py`
- Tests: `tests/test_release_doc_sync.py`

## Pinning

Tool repos MUST consume this action via `@v1.0` (or a full commit SHA), never `@main`. The pinning rule matches the `drift-check@v1.7` precedent in this repo: `@main` from a tool repo means every meta-repo PR can break every tool-repo release. The `v1.0` floating tag points at the latest `1.x.y` of this repo and is updated by the maintainer when a relevant change ships. Floating-tag automation is tracked in DTD#14.

```yaml
uses: TMHSDigital/Developer-Tools-Directory/.github/actions/release-doc-sync@v1.0
```

## Inputs

| Input | Required | Default | Purpose |
| --- | --- | --- | --- |
| `plugin-version` | yes | -- | New plugin version after the bump (semver, no `v` prefix). Example: `1.2.1`. |
| `previous-version` | yes | -- | Previous plugin version. Used to scope CLAUDE.md replacements so unrelated version mentions are not mangled. |
| `repository` | no | `${{ github.repository }}` | `owner/repo` for constructing the GitHub release-notes URL in the CHANGELOG entry. |
| `release-date` | no | today (UTC) | `YYYY-MM-DD` date stamp for the new CHANGELOG header. |
| `python-version` | no | `3.11` | Python interpreter for the sync script. |
| `meta-repo-ref` | no | `v1.0` | git ref of `TMHSDigital/Developer-Tools-Directory` to use for the sync script. |
| `caller-path` | no | `.` | Path inside `GITHUB_WORKSPACE` that points at the caller checkout. |

## Outputs

| Output | Values |
| --- | --- |
| `changed` | `true` if at least one doc file was modified, `false` otherwise. |
| `files-changed` | Space-separated list of file basenames modified. Empty when `changed=false`. |
| `changelog-action` | One of `inserted`, `idempotent`, `missing`. |
| `claude-action` | One of `updated`, `idempotent`, `missing`. |
| `roadmap-action` | One of `updated`, `idempotent`, `missing`. |

## What the action edits

### `CHANGELOG.md`

Prepends a stub section at the top of the releases list:

```markdown
## [X.Y.Z] - YYYY-MM-DD

See [release notes](https://github.com/<owner>/<repo>/releases/tag/vX.Y.Z) for details.
```

The stub is intentionally minimal. Curated narrative belongs in GitHub Releases (which `release.yml` already generates). Insertion point is immediately before the first existing `## [` section; if there are no prior release sections, the stub is appended after the file's preamble. If `[X.Y.Z]` already appears anywhere in the file, the action no-ops.

### `CLAUDE.md`

Two patterns are rewritten, both idempotent:

1. The canonical `**Version:** X.Y.Z` line (Docker convention) is replaced with the new version. The `v` prefix is preserved if it was originally present.
2. Any `vOLD` token (Steam-style prose mentions like `(v1.0.0)` and `The current release is v1.0.0`) is rewritten to `vNEW`. The match uses a strict lookahead so `v1.0.0` does NOT match inside `v1.0.0-beta` or `v1.0.01`.

The action does NOT touch:

- `<!-- standards-version: A.B.C -->` HTML comment markers. Those are owned by the drift checker (DTD#1) and represent a different concept (ecosystem standards version).
- Bare `OLD` substrings (e.g., the literal `1.0.0` without a `v` prefix or `**Version:**` label). Doing so would mangle CHANGELOG-style references buried inside CLAUDE.md or quoted command output.

### `ROADMAP.md`

Updates only the `**Current:** vX.Y.Z` line if present. Tool repos that use a different roadmap layout (e.g., Docker's bold-prefix style without a `**Current:**` label) get a no-op, which is intentional. The action explicitly does NOT touch:

- The themed-release table. Patch releases do not get table rows per the policy in [`versioning.md`](versioning.md).
- `(current)` markers anywhere in the file. The marker tracks the currently-released theme, which is a human-curated minor/major decision.

## Recommended integration in a tool-repo `release.yml`

Insert one step between the existing `Update version files` step (which bumps `plugin.json` and the README badge) and the existing `Commit and tag` step (which runs `git add -A && git commit`). The `release-doc-sync` step's edits land in the working tree and are picked up by the same release commit:

```yaml
- name: Update version files
  # ... existing python block bumps plugin.json and README badge ...

- name: Sync doc version references
  if: steps.check.outputs.skip == 'false'
  uses: TMHSDigital/Developer-Tools-Directory/.github/actions/release-doc-sync@v1.0
  with:
    plugin-version: ${{ steps.new.outputs.version }}
    previous-version: ${{ steps.current.outputs.version }}

- name: Commit and tag
  # unchanged: git add -A picks up the action's edits
```

The action does NOT do its own git operations, does NOT request a `github-token`, and does NOT call the GitHub API. All it does is read and write files in the caller's working tree.

## Exit-code contract

The Python script under the action follows the same convention as `drift-check`:

| Exit code | Meaning |
| --- | --- |
| `0` | Ran successfully, no files changed (already aligned, or all absent). |
| `1` | Ran successfully, at least one file changed. |
| `2` | Tool error (bad args, unreadable files, malformed inputs). |

The composite action treats both `0` and `1` as success and only fails the calling job on `>=2`. The `1` "made a change" signal is informational; consumers can branch on the `changed` output if they need to react.

## Idempotency

Every edit is idempotent at the file level. Running the action twice in a row leaves the second invocation as a pure no-op: the files are byte-identical to their post-first-run state. This guarantee is exercised by `test_second_run_is_pure_noop` and is what makes the action safe to wire into `release.yml` even when a release re-runs (manual `workflow_dispatch`, retried job, etc.).

## Out of scope

- `AGENTS.md` plugin-version stamping. The drift checker uses a different concept (`standards-version`) for AGENTS.md and adding plugin-version stamping needs a separate design discussion.
- Roadmap table row insertion. See [`versioning.md`](versioning.md) for why patch releases do not get rows; humans curate the table for minor/major releases.
- README badge updates. Already handled by the existing `Update version files` step in `release.yml`.
- Footer link references in CHANGELOG (`[X.Y.Z]: <url>`). Steam's Keep-a-Changelog format uses them, but maintaining the link table requires either upserting alphabetical-by-version order or relying on Markdown allowing duplicates -- both fragile. The Steam doc-consistency test only requires the `[X.Y.Z]` substring, which the header alone satisfies.
