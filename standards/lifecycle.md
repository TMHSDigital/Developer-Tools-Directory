# Lifecycle

Every tool in `registry.json` has a `status` field that tracks its maturity. This document defines the allowed states, the criteria for each, and the transitions between them.

## States

| State | Meaning |
| --- | --- |
| `experimental` | Pre-0.1.0. Prototype exploring an idea. Not recommended for any use. |
| `beta` | 0.x.y. Functional but API may change. Early adopters only. |
| `active` | 1.0.0 or later. Stable API, tests in place, docs shipped. Default recommended status. |
| `maintenance` | Stable but no longer receiving new features. Security and critical bug fixes only. |
| `deprecated` | Scheduled for removal. Still installable, but users should migrate. Deprecation notice required. |
| `archived` | No longer maintained or supported. Read-only. Removed from catalog display. |

The `registry.json` schema allows all six values. CI validates.

## Criteria per state

### `experimental`

- Pre-release version (0.0.x or 0.1.0-alpha).
- No stability guarantee.
- May have skeleton tests.
- `README.md` clearly labels experimental status.
- Does not appear in the default catalog view; surfaces behind a filter.

### `beta`

- Version 0.x.y where x >= 1.
- Feature-complete for its announced scope.
- Has at least one release tag.
- Has a documentation site deployed (if `pagesType` != `none`).
- Has partial test coverage (every public MCP tool smoke-tested).
- README documents known gaps.

### `active`

- Version 1.0.0 or later.
- Meets the minimum bar in [testing.md](testing.md).
- Has a documentation site deployed.
- Has run without breaking API changes for at least 30 days after reaching 1.0.0.
- Meets all checklist items in [scope.md](scope.md).
- Maintainer responds to issues within 14 days.

### `maintenance`

- Was `active` at some point.
- Owner has announced no new features will land.
- Security and critical bug fixes still shipped.
- `README.md` has a "Maintenance mode" banner.

### `deprecated`

- Announced deprecation with a sunset date (minimum 6 months from announcement).
- `README.md` opens with a deprecation banner linking to the replacement (if any).
- Catalog site renders the card with a muted style and a deprecation badge.
- Installs still work.
- No new features, no new tools, no new tests.

### `archived`

- Past the sunset date of a deprecation, or abandoned.
- GitHub repo is archived (read-only).
- Removed from the default catalog view.
- Entry remains in `registry.json` for historical record, but sorts last.

## Transitions

Allowed transitions:

```
experimental -> beta      (feature complete)
beta         -> active    (1.0.0 cut, tests, docs, 30 days stable)
active       -> maintenance  (owner decision)
active       -> deprecated   (owner decision, sunset announced)
maintenance  -> deprecated   (owner decision, sunset announced)
deprecated   -> archived     (sunset date reached)
```

Not allowed:

- `archived` to any other state (create a new repo instead).
- `active` directly to `archived` (must pass through `deprecated`).
- `experimental` directly to `active` (must pass through `beta`).

## Deprecation process

1. Owner opens a PR updating `registry.json` `status` to `deprecated`.
2. PR body announces the sunset date (minimum 6 months out) and the recommended replacement.
3. Owner updates the tool's `README.md` with a deprecation banner at the top.
4. Owner updates the tool's docs site with a deprecation notice.
5. Owner tags a final release note.
6. On the sunset date, owner opens a follow-up PR moving status to `archived`.
7. Owner archives the GitHub repo (Settings > General > Archive).

## Graduation from `beta` to `active`

Requires:

- [ ] A `v1.0.0` tag exists.
- [ ] `tests/` folder exists, meets [testing.md](testing.md) minimum.
- [ ] Docs site is live and renders without errors.
- [ ] No breaking API changes in the last 30 days.
- [ ] `plugin.json`, `site.json`, `mcp-tools.json` all pass schema validation.
- [ ] `registry.json` entry passes the [scope.md](scope.md) review checklist.

A PR updating `status` from `beta` to `active` links to the commit for each checklist item.

## Catalog site behavior

| Status | Display |
| --- | --- |
| `experimental` | Hidden by default, appears with "Show experimental" filter |
| `beta` | Shown, badged "Beta" |
| `active` | Shown, no badge |
| `maintenance` | Shown, badged "Maintenance" |
| `deprecated` | Shown, muted style, badged "Deprecated" |
| `archived` | Hidden by default, appears with "Show archived" filter |

## Metrics

Aggregate stats on the catalog site and in `README.md` count only `active` and `maintenance` tools by default. Experimental, beta, deprecated, and archived tools are excluded unless the reader toggles the relevant filter.
