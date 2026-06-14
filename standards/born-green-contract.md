# Born-Green Contract

The acceptance criterion that any generator producing a TMHSDigital tool repo must satisfy. A repo is "born green" when, the moment it is generated, it already passes every check the ecosystem enforces - no manual reconcile step, no first-day drift, no catalog gap.

This is a specification, not prose. Each clause is a testable assertion. The canonical generator (`scaffold/generator.py`, driven by `scaffold/create-tool.py`) satisfies it and is locked in by `tests/test_scaffold_born_green.py`. A second generator (for example the Developer-Tools-MCP `createTool` path) is compliant only if it satisfies every clause, ideally by delegating to the canonical entrypoint rather than reimplementing it.

## Why this exists

The ecosystem has had two recurring "born wrong" failure modes:

1. A repo generated with the wrong workflow set (an mcp-server emitted with `validate.yml`/`release.yml`, which assume a plugin manifest). Fixed in PR #74.
2. A repo whose type the drift checker could not detect, because detection keyed on incidental directory presence rather than a positive manifest marker. An mcp-server rendered with a `skills/` directory silently classified as `unknown` and lost required-workflow enforcement.
3. A repo born outside the catalog: generated, pushed, and never added to `registry.json`, so it never appears in the docs site, README tables, or drift `mode: all`.

Each was discovered reconciles later, by hand. The contract turns each into a generation-time invariant and a CI failure.

## Acceptance clauses

A generated repo MUST satisfy all of the following.

### C1. Positive-marker type

The repo carries the positive manifest marker for its type, and `scripts/drift_check/snapshot.py::_detect_repo_type` returns that exact type (never `unknown`):

| Type | Positive marker (always written) |
| --- | --- |
| `cursor-plugin` | `.cursor-plugin/plugin.json` |
| `mcp-server` | `package.json` (the server's own manifest and version source of truth) |

Detection MUST key only on these positive markers, never on the presence or absence of optional directories such as `skills/` or `rules/`. A type's classification MUST be stable regardless of which optional content the repo happens to include (an mcp-server with `skills/` is still an mcp-server).

### C2. Exact workflow set

The emitted `.github/workflows/` set EXACTLY equals the per-type required set in [`drift-checker.config.json`](drift-checker.config.json) plus the two optional-for-both workflows (`label-sync.yml`, `pages.yml`) - no more, no less. See [`ci-cd.md`](ci-cd.md) for the per-type matrix. mcp-server repos MUST NOT emit `validate.yml` or `release.yml` (their jobs assume a plugin manifest; `publish.yml` replaces `release.yml`).

### C3. Empty drift

Running the drift checker against the generated tree yields zero error-severity and zero warning-severity findings. The generated repo tolerates zero skill/rule content: an empty repo (no `skills/`, no `rules/`) is still born green.

### C4. Current markers and pins

- Every `standards-version` marker equals the meta `STANDARDS_VERSION` at generation time.
- Every workflow action pin is DERIVED from the meta `VERSION` at generation time (for example `drift-check@vMAJOR.MINOR`, `release-doc-sync@vMAJOR`, `meta-repo-ref: vMAJOR.MINOR.PATCH`). No pin, year, or version is a hardcoded literal in a template.

### C5. Consistent README counts

The generated README's aggregate counts (`N skills`, `N rules`, ...) match the generated content, so the repo's own `validate-counts` check passes on day one.

### C6. Registered in the catalog

Generation registers the repo in `registry.json` with a complete, schema-valid entry (the schema in [`../AGENTS.md`](../AGENTS.md) and enforced by `validate.yml`), and regenerates the derived artifacts (`README.md`, `CLAUDE.md`, `docs/index.html`) via the single `sync_from_registry.sync_all` code path so `python scripts/sync_from_registry.py --check` is clean. The entry's `type` is resolved from the same positive-marker detector as C1. The entry carries no `version` field (removed in PR #73). Registration is the default; an explicit escape hatch (`--no-register`) exists for the rare deliberate case.

## Canonical entrypoint

The single, importable implementation lives in `scaffold/generator.py`:

```python
from scaffold.generator import generate_repo

generate_repo(
    name="Example Developer Tools",
    description="One-line description",
    repo_type="cursor-plugin",   # or "mcp-server"
    skills=0,
    rules=0,
    register=True,               # C6; set False only for throwaway generation
    registry_root=None,          # override for tests / temp catalogs
)
```

`generate_repo` renders the repo (C1-C5), resolves the type from the generated tree via `_detect_repo_type` (failing loudly if it is `unknown`), and registers it (C6). A second generator SHOULD delegate to this function rather than reimplement the render-and-register logic; reimplementation is how two generators drift apart. `build_registry_entry` and `register_in_registry` are exposed for callers that need the pieces independently.

## Verification

`tests/test_scaffold_born_green.py` renders a repo for each supported type, including the previously-breaking shapes (an mcp-server with `skills/`, and an empty cursor-plugin), and asserts C1-C5 against the generated tree plus a C6 registration round-trip against a temporary registry root. "Born wrong, born unknown, or born unregistered" are all CI failures.
