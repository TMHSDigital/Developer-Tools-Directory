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
