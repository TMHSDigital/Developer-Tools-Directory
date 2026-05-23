"""Standalone tests for the required-workflows drift check.

No test harness existed before this file. Run directly or with pytest:

    python tests/test_required_workflows.py
    pytest tests/test_required_workflows.py -v

Each test function asserts a single behaviour; failures print the finding
list so the cause is immediately visible without a debugger.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running from repo root: python tests/test_required_workflows.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from drift_check.checks.required_workflows import RequiredWorkflowsCheck
from drift_check.types import (
    DriftConfig,
    Finding,
    RepoConfig,
    RepoSnapshot,
    Version,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_META = Version(major=1, minor=10, patch=0, raw="1.10.0")


def _snap(
    *,
    slug: str = "test-repo",
    repo_type: str = "cursor-plugin",
    present: frozenset[str] = frozenset(),
    required: frozenset[str] = frozenset(),
    skip_checks: frozenset[str] = frozenset(),
) -> RepoSnapshot:
    cfg = RepoConfig(
        slug=slug,
        repo_type=repo_type,
        skip_checks=skip_checks,
        required_workflows=required,
    )
    return RepoSnapshot(
        slug=slug,
        repo_type=repo_type,
        files={},
        meta_version=_META,
        meta_commit="abc1234",
        config=cfg,
        present_workflows=present,
    )


def _run(snap: RepoSnapshot) -> list[Finding]:
    return list(RequiredWorkflowsCheck().run(snap))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_missing_required_workflow_is_error() -> None:
    """A required workflow absent from present_workflows emits an error."""
    findings = _run(_snap(
        required=frozenset({"validate.yml", "stale.yml"}),
        present=frozenset({"validate.yml"}),
    ))
    assert len(findings) == 1, findings
    f = findings[0]
    assert f.severity == "error"
    assert f.check == "required-workflows"
    assert "stale.yml" in f.message
    assert f.file is None


def test_compliant_repo_is_silent() -> None:
    """A repo with all required workflows present emits nothing."""
    required = frozenset({"validate.yml", "release.yml", "stale.yml", "drift-check.yml"})
    findings = _run(_snap(required=required, present=required))
    assert findings == [], findings


def test_unknown_type_is_silent() -> None:
    """repo_type 'unknown' never emits required-workflows findings."""
    findings = _run(_snap(
        repo_type="unknown",
        required=frozenset({"validate.yml"}),
        present=frozenset(),
    ))
    assert findings == [], findings


def test_config_absent_is_silent() -> None:
    """Empty required_workflows (absent from config) produces no findings."""
    findings = _run(_snap(required=frozenset(), present=frozenset()))
    assert findings == [], findings


def test_skip_checks_suppresses() -> None:
    """skip_checks containing 'required-workflows' silences the check."""
    findings = _run(_snap(
        required=frozenset({"validate.yml"}),
        present=frozenset(),
        skip_checks=frozenset({"required-workflows"}),
    ))
    assert findings == [], findings


def test_extra_workflows_not_flagged() -> None:
    """Workflows present but not required are never flagged."""
    required = frozenset({"validate.yml"})
    present = frozenset({"validate.yml", "publish.yml", "codeql.yml", "label-sync.yml"})
    findings = _run(_snap(required=required, present=present))
    assert findings == [], findings


def test_multiple_missing_workflows_each_get_finding() -> None:
    """Each missing required workflow produces its own error finding."""
    required = frozenset({"validate.yml", "release.yml", "stale.yml", "drift-check.yml"})
    findings = _run(_snap(required=required, present=frozenset()))
    assert len(findings) == 4, findings
    assert all(f.severity == "error" for f in findings)
    missing = {f.message.split("'")[1] for f in findings}
    assert missing == required


def test_mcp_server_type_respected() -> None:
    """mcp-server repos use their own required list (publish.yml not release.yml)."""
    findings = _run(_snap(
        repo_type="mcp-server",
        required=frozenset({"drift-check.yml", "stale.yml", "publish.yml"}),
        present=frozenset({"drift-check.yml", "publish.yml"}),
    ))
    # stale.yml missing -> one error
    assert len(findings) == 1, findings
    assert "stale.yml" in findings[0].message


def test_config_tier_merge_adds_requirements() -> None:
    """DriftConfig.resolve merges required_workflows additively across tiers."""
    cfg_data = {
        "globals": {"signal_policy": "same-major-minor", "required_workflows": ["validate.yml"]},
        "types": {"cursor-plugin": {"required_workflows": ["release.yml"]}},
        "repos": {"my-repo": {"required_workflows": ["drift-check.yml"]}},
    }
    import json, tempfile, os
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as fh:
        json.dump(cfg_data, fh)
        tmp = fh.name
    try:
        from drift_check.config import load_config
        cfg = load_config(Path(tmp))
        resolved = cfg.resolve("my-repo", "cursor-plugin")
        assert resolved.required_workflows == frozenset(
            {"validate.yml", "release.yml", "drift-check.yml"}
        ), resolved.required_workflows
    finally:
        os.unlink(tmp)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  ok  {fn.__name__}")
            passed += 1
        except Exception as exc:
            print(f"FAIL  {fn.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
