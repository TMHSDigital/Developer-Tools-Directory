# Versioning

All TMHSDigital developer tool repos use [Semantic Versioning](https://semver.org/) with fully automated version management.

## Source of Truth

The **only** source of truth for the current version is the `version` field in `.cursor-plugin/plugin.json`.

Do not store version numbers anywhere else (except the README badge, which is auto-synced by CI).

## How Versions Change

Versions are bumped automatically by the `release.yml` workflow on every qualifying push to `main`.

```
push to main
  -> release.yml runs
    -> reads current version from plugin.json
    -> scans commits since last tag
    -> determines bump type (major/minor/patch)
    -> computes new version
    -> updates plugin.json + README badge
    -> commits [skip ci]
    -> creates git tag vX.Y.Z
    -> creates GitHub Release
```

## Bump Rules

| Commit pattern | Bump | Example |
| --- | --- | --- |
| `feat!:` or `BREAKING CHANGE` | **major** (X.0.0) | `feat!: remove deprecated API` |
| `feat:` or `feat(scope):` | **minor** (x.Y.0) | `feat: add new skill` |
| Anything else | **patch** (x.y.Z) | `fix: handle null in lookup` |

## What NOT to Do

- **Do not manually edit the version in `plugin.json`.** The release workflow will overwrite it.
- **Do not manually create git tags.** The release workflow creates them.
- **Do not manually edit the version badge in README.md.** The release workflow updates it.
- **Do not manually edit the GitHub repo About section.** The release workflow syncs it.

## Skipping Releases

Pushes that only change these paths do not trigger the release workflow:

- `.github/**`
- `docs/**`
- `*.md`
- `LICENSE`
- `mkdocs.yml`

This prevents docs-only commits from creating empty releases.

## Pre-1.0 Development

During initial development (`0.x.y`), the same rules apply but with the understanding that the API is unstable. Once the plugin reaches feature completeness and has been validated, tag `v1.0.0` manually (or via a `feat:` commit when ready) to signal stability.

## Release Notes

The release workflow auto-generates release notes grouped by commit type:

- **Features** (`feat:`)
- **Bug Fixes** (`fix:`)
- **Other Changes** (everything else)

`CHANGELOG.md` is maintained manually for curated, human-readable release history. It is not auto-generated.

## What a MINOR bump means for ecosystem standards

The meta-repo's `VERSION` file carries the ecosystem-wide standards version. It follows the same SemVer rules, but each component has a second, standards-specific meaning for tool repos that embed a `standards-version` signal in their agent files.

- **MAJOR** (e.g., `1.x.y` → `2.0.0`) — an incompatible change to the standards themselves. New required elements, removed fields, or restructured file conventions that existing tool repos will fail to validate against without re-alignment.
- **MINOR** (e.g., `1.6.x` → `1.7.0`) — ecosystem standards changed in a way that tool repos need to re-align with. Typical triggers: new required elements in agent files, changed frontmatter schemas, new required standards references, restructured validation rules, or new checks in the drift checker that introduce findings for existing tool-repo content. A mechanical rollout session across the tool repos is typically scheduled after a MINOR bump.
- **PATCH** (e.g., `1.7.0` → `1.7.1`) — bug fixes, clarifications, or additions that do not change the standards surface. Tool repos with a PATCH-behind signal are reported as `info` by the drift checker — visible in verbose runs but not blocking CI.

The drift checker enforces this mapping via the `same-major-minor` signal policy (see `standards/drift-checker.config.json`). Tool repos whose `standards-version` differs from the meta-repo's `VERSION` in MAJOR or MINOR are reported as `error`; PATCH differences are `info`; tool values ahead of meta are `warn` (either an in-flight rollout or a missed meta-repo bump, both worth surfacing).
