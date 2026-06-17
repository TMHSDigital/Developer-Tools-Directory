"""Born-green integration test for the scaffold generator.

Renders a repo of each supported type with ``scaffold/create-tool.py`` and
asserts the Phase-2-B properties against the generated tree:

* ``_detect_repo_type`` returns the intended type (not ``unknown``);
* the meta drift checker reports zero error/warn findings (born green);
* every standards-version marker equals the meta ``STANDARDS_VERSION``;
* workflow action pins equal the train derived from the meta ``VERSION``;
* the README aggregate counts match the generated content, so the repo's
  own ``validate-counts`` job would pass on day one;
* the emitted workflow set EXACTLY equals the per-type required set from
  ``standards/drift-checker.config.json`` plus the two optional-for-both
  workflows (``label-sync.yml``, ``pages.yml``) - no more, no less.

The last assertion is the regression guard for the
"mcp-server-got-plugin-workflows" bug class: it fails CI the moment the
renderer emits a workflow that does not belong to a type, instead of the
drift surfacing three reconciles later.

Run directly or with pytest::

    pytest tests/test_scaffold_born_green.py -v
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.drift_check.checks import (  # noqa: E402
    BrokenRefsCheck,
    RequiredRefsCheck,
    RequiredWorkflowsCheck,
    StaleCountsCheck,
    VersionSignalCheck,
)
from scripts.drift_check.checks.required_refs import load_required_refs  # noqa: E402
from scripts.drift_check.config import load_config  # noqa: E402
from scripts.drift_check.semver import parse_version  # noqa: E402
from scripts.drift_check.snapshot import (  # noqa: E402
    _detect_repo_type,
    build_local_snapshot,
    list_meta_standards,
)

CREATE_TOOL = REPO_ROOT / "scaffold" / "create-tool.py"
CONFIG_PATH = REPO_ROOT / "standards" / "drift-checker.config.json"
REQUIRED_REFS_PATH = REPO_ROOT / "standards" / "required-refs.json"

OPTIONAL_FOR_BOTH = frozenset({"label-sync.yml", "pages.yml"})

# Workflows a type emits beyond its drift-required set and the
# optional-for-both pair. mcp-server repos emit a build/test CI and an
# auto-release workflow; these are intentionally NOT drift-required (a sibling
# that lacks them must not go red), so they live here rather than in
# drift-checker.config.json.
EMITTED_EXTRA: dict[str, frozenset[str]] = {
    "mcp-server": frozenset({"ci.yml", "release.yml"}),
}

# Each case is a distinct render. ``type`` is the intended repo type, ``args``
# are extra CLI flags, ``detect`` is the type _detect_repo_type MUST return.
# The "*-with-skills" / "*-empty" variants are the regression guards:
#   - mcp-server-with-skills was the PR #74 latent fragility: the old detector
#     keyed on directory presence and flipped it to "unknown", silently losing
#     required-workflow enforcement. With positive-marker detection (package.json)
#     it must classify as mcp-server.
#   - cursor-plugin-empty proves born-green tolerates ZERO skill/rule content.
_CASES: dict[str, dict] = {
    "cursor-plugin": {
        "type": "cursor-plugin",
        "args": ["--skills", "2", "--rules", "1"],
        "detect": "cursor-plugin",
    },
    "cursor-plugin-empty": {
        "type": "cursor-plugin",
        "args": [],
        "detect": "cursor-plugin",
    },
    "mcp-server": {
        "type": "mcp-server",
        "args": [],
        "detect": "mcp-server",
    },
    "mcp-server-with-skills": {
        "type": "mcp-server",
        "args": ["--skills", "3", "--rules", "2"],
        "detect": "mcp-server",
    },
}

# Registry schema mirrored from validate.yml's registry check, used by the
# registration round-trip test to assert a generated entry is schema-valid.
_REQUIRED_FIELDS = {
    "name": str,
    "repo": str,
    "slug": str,
    "description": str,
    "type": str,
    "homepage": str,
    "skills": int,
    "rules": int,
    "mcpTools": int,
    "extras": dict,
    "topics": list,
    "status": str,
    "language": str,
    "license": str,
    "pagesType": str,
    "hasCI": bool,
}


def _standards_version() -> str:
    return (REPO_ROOT / "STANDARDS_VERSION").read_text(encoding="utf-8").strip()


def _meta_version_parts() -> tuple[int, int, int]:
    raw = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", raw)
    assert m, f"VERSION is not X.Y.Z: {raw!r}"
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def _required_workflows(repo_type: str) -> frozenset[str]:
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return frozenset(cfg["types"][repo_type]["required_workflows"])


def _render(label: str, dest: Path) -> Path:
    """Render a case with --no-register (these assertions are about the
    generated tree, not the catalog; registration is covered separately)."""
    case = _CASES[label]
    slug = f"born-green-{label}"
    cmd = [
        sys.executable,
        str(CREATE_TOOL),
        "--name",
        f"Born Green {label}",
        "--description",
        "born green probe",
        "--type",
        case["type"],
        "--slug",
        slug,
        "--output",
        str(dest),
        "--no-register",
        *case["args"],
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"scaffold failed:\n{proc.stdout}\n{proc.stderr}"
    repo = dest / slug
    assert repo.is_dir(), f"expected generated repo at {repo}"
    return repo


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for label in _CASES:
        dest = tmp_path_factory.mktemp(label)
        out[label] = _render(label, dest)
    return out


def _run_drift_checks(repo: Path, slug: str):
    meta_version = parse_version(_standards_version())
    cfg = load_config(CONFIG_PATH)
    required_refs = load_required_refs(REQUIRED_REFS_PATH)
    meta_standards = list_meta_standards(REPO_ROOT)
    snap = build_local_snapshot(
        repo_path=repo,
        meta_version=meta_version,
        meta_commit="born-green-test",
        config=cfg,
        slug=slug,
        meta_standards=meta_standards,
        meta_required_refs=dict(required_refs),
    )
    checks = (
        VersionSignalCheck(),
        BrokenRefsCheck(),
        RequiredRefsCheck(),
        RequiredWorkflowsCheck(),
        StaleCountsCheck(),
    )
    findings = []
    for check in checks:
        findings.extend(check.run(snap))
    return snap, findings


@pytest.mark.parametrize("label", list(_CASES))
def test_detected_type_matches(rendered, label):
    repo = rendered[label]
    expected = _CASES[label]["detect"]
    got = _detect_repo_type(repo)
    assert got == expected, (
        f"case {label!r} ({_CASES[label]['type']}) detected as {got!r}, "
        f"expected {expected!r}"
    )


@pytest.mark.parametrize("label", list(_CASES))
def test_born_green_no_drift(rendered, label):
    repo = rendered[label]
    repo_type = _CASES[label]["type"]
    snap, findings = _run_drift_checks(repo, f"born-green-{label}")
    assert snap.repo_type == repo_type
    actionable = [f for f in findings if f.severity in ("error", "warn")]
    assert actionable == [], (
        f"freshly scaffolded {label} repo is not born green: "
        + "; ".join(f"{f.check}/{f.severity}: {f.message}" for f in actionable)
    )


@pytest.mark.parametrize("label", list(_CASES))
def test_standards_markers_current(rendered, label):
    repo = rendered[label]
    expected = _standards_version()
    marker_files = [repo / "AGENTS.md", repo / "CLAUDE.md"]
    for skill_md in (repo / "skills").glob("*/SKILL.md"):
        marker_files.append(skill_md)
    for rule_mdc in (repo / "rules").glob("*.mdc"):
        marker_files.append(rule_mdc)
    for f in marker_files:
        text = f.read_text(encoding="utf-8")
        assert f"standards-version: {expected}" in text, (
            f"{f.relative_to(repo)} missing current standards-version {expected}"
        )


@pytest.mark.parametrize("label", list(_CASES))
def test_action_pins_derived(rendered, label):
    repo = rendered[label]
    repo_type = _CASES[label]["type"]
    major, minor, patch = _meta_version_parts()
    drift = (repo / ".github" / "workflows" / "drift-check.yml").read_text(encoding="utf-8")
    assert f"drift-check@v{major}.{minor}" in drift, (
        f"drift-check.yml not pinned to derived @v{major}.{minor}"
    )
    if repo_type == "cursor-plugin":
        release = (repo / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        assert f"release-doc-sync@v{major}" in release, (
            f"release.yml does not consume derived release-doc-sync@v{major}"
        )
        assert f"meta-repo-ref: v{major}.{minor}.{patch}" in release, (
            "release.yml meta-repo-ref not pinned to derived full meta tag"
        )


@pytest.mark.parametrize("label", list(_CASES))
def test_readme_counts_consistent(rendered, label):
    repo = rendered[label]
    repo_type = _CASES[label]["type"]
    skills_dir = repo / "skills"
    rules_dir = repo / "rules"
    skill_count = (
        len([d for d in skills_dir.iterdir() if (d / "SKILL.md").is_file()])
        if skills_dir.is_dir()
        else 0
    )
    rule_count = (
        len([f for f in rules_dir.iterdir() if f.suffix == ".mdc"])
        if rules_dir.is_dir()
        else 0
    )
    readme = (repo / "README.md").read_text(encoding="utf-8")
    if repo_type == "cursor-plugin":
        assert f"{skill_count} skills" in readme, (
            f"README missing '{skill_count} skills' (validate-counts would fail)"
        )
        assert f"{rule_count} rules" in readme, (
            f"README missing '{rule_count} rules' (validate-counts would fail)"
        )


@pytest.mark.parametrize("label", list(_CASES))
def test_emitted_workflow_set_exact(rendered, label):
    repo = rendered[label]
    repo_type = _CASES[label]["type"]
    present = frozenset(
        p.name
        for p in (repo / ".github" / "workflows").iterdir()
        if p.suffix in (".yml", ".yaml")
    )
    expected = (
        _required_workflows(repo_type)
        | OPTIONAL_FOR_BOTH
        | EMITTED_EXTRA.get(repo_type, frozenset())
    )
    assert present == expected, (
        f"{label} emitted workflows {sorted(present)} != expected "
        f"{sorted(expected)} (required for {repo_type} union optional-for-both)"
    )


def _make_temp_registry_root(tmp_path: Path) -> Path:
    """Copy the catalog artifacts sync_all touches into a temp root so
    registration can be exercised without mutating the live registry."""
    root = tmp_path / "catalog"
    (root / "docs").mkdir(parents=True)
    for rel in ("registry.json", "README.md", "CLAUDE.md", "VERSION"):
        shutil.copy2(REPO_ROOT / rel, root / rel)
    shutil.copy2(REPO_ROOT / "docs" / "index.html", root / "docs" / "index.html")
    shutil.copy2(REPO_ROOT / "docs" / "search-index.json", root / "docs" / "search-index.json")
    shutil.copytree(REPO_ROOT / "standards", root / "standards")
    return root


@pytest.mark.parametrize("label", ["cursor-plugin", "mcp-server-with-skills"])
def test_registration_round_trips(tmp_path, label):
    """Generation-with-registration must produce a schema-valid registry
    entry and leave the catalog sync-clean (sync --check passes), so a repo
    cannot be born unregistered or born inconsistent. Exercised against a
    TEMP registry root - the live registry.json is never touched."""
    from scripts.sync_from_registry import sync_all  # noqa: E402

    case = _CASES[label]
    root = _make_temp_registry_root(tmp_path)
    slug = f"reg-{label}"
    cmd = [
        sys.executable,
        str(CREATE_TOOL),
        "--name",
        f"Reg {label}",
        "--description",
        "registration round-trip probe",
        "--type",
        case["type"],
        "--slug",
        slug,
        "--output",
        str(tmp_path / "out"),
        "--registry-root",
        str(root),
        *case["args"],
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"register failed:\n{proc.stdout}\n{proc.stderr}"

    entries = json.loads((root / "registry.json").read_text(encoding="utf-8"))
    matches = [e for e in entries if e["slug"] == slug]
    assert len(matches) == 1, f"{slug} not registered exactly once"
    entry = matches[0]

    for field, typ in _REQUIRED_FIELDS.items():
        assert field in entry, f"registry entry missing required field {field!r}"
        assert isinstance(entry[field], typ), (
            f"field {field!r} is {type(entry[field]).__name__}, expected {typ.__name__}"
        )
    assert "version" not in entry, "registry entry must not carry a version field"
    assert entry["type"] == case["detect"], (
        f"registered type {entry['type']!r} != detected {case['detect']!r}"
    )

    drift = sync_all(root, check=True)
    assert drift is False, "catalog is not sync-clean after registration"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
