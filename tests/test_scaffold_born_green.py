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
import os
import re
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

# Render parameters per type. mcp-server is rendered with zero skills/rules so
# the no-plugin-manifest detection shape (no skills/, no rules/, CLAUDE.md
# present) holds; rendering it with skills would create skills/ and make
# _detect_repo_type return "unknown".
_CASES = {
    "cursor-plugin": ["--skills", "2", "--rules", "1"],
    "mcp-server": [],
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


def _render(repo_type: str, dest: Path) -> Path:
    slug = f"born-green-{repo_type}"
    cmd = [
        sys.executable,
        str(CREATE_TOOL),
        "--name",
        f"Born Green {repo_type}",
        "--description",
        "born green probe",
        "--type",
        repo_type,
        "--slug",
        slug,
        "--output",
        str(dest),
        *_CASES[repo_type],
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, f"scaffold failed:\n{proc.stdout}\n{proc.stderr}"
    repo = dest / slug
    assert repo.is_dir(), f"expected generated repo at {repo}"
    return repo


@pytest.fixture(scope="module")
def rendered(tmp_path_factory) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for repo_type in _CASES:
        dest = tmp_path_factory.mktemp(repo_type)
        out[repo_type] = _render(repo_type, dest)
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


@pytest.mark.parametrize("repo_type", list(_CASES))
def test_detected_type_matches(rendered, repo_type):
    repo = rendered[repo_type]
    assert _detect_repo_type(repo) == repo_type, (
        f"{repo_type} scaffold detected as {_detect_repo_type(repo)!r}"
    )


@pytest.mark.parametrize("repo_type", list(_CASES))
def test_born_green_no_drift(rendered, repo_type):
    repo = rendered[repo_type]
    snap, findings = _run_drift_checks(repo, f"born-green-{repo_type}")
    assert snap.repo_type == repo_type
    actionable = [f for f in findings if f.severity in ("error", "warn")]
    assert actionable == [], (
        "freshly scaffolded repo is not born green: "
        + "; ".join(f"{f.check}/{f.severity}: {f.message}" for f in actionable)
    )


@pytest.mark.parametrize("repo_type", list(_CASES))
def test_standards_markers_current(rendered, repo_type):
    repo = rendered[repo_type]
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


@pytest.mark.parametrize("repo_type", list(_CASES))
def test_action_pins_derived(rendered, repo_type):
    repo = rendered[repo_type]
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


@pytest.mark.parametrize("repo_type", list(_CASES))
def test_readme_counts_consistent(rendered, repo_type):
    repo = rendered[repo_type]
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


@pytest.mark.parametrize("repo_type", list(_CASES))
def test_emitted_workflow_set_exact(rendered, repo_type):
    repo = rendered[repo_type]
    present = frozenset(
        p.name
        for p in (repo / ".github" / "workflows").iterdir()
        if p.suffix in (".yml", ".yaml")
    )
    expected = _required_workflows(repo_type) | OPTIONAL_FOR_BOTH
    assert present == expected, (
        f"{repo_type} emitted workflows {sorted(present)} != expected "
        f"{sorted(expected)} (required ∪ optional-for-both)"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
