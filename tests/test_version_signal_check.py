from pathlib import Path

from scripts.drift_check.checks import VersionSignalCheck
from scripts.drift_check.semver import parse_version
from scripts.drift_check.snapshot import build_local_snapshot
from scripts.drift_check.types import DriftConfig

from tests.conftest import FIXTURES


META = parse_version("1.6.3")
assert META is not None
DEFAULT_CFG = DriftConfig(globals={"signal_policy": "same-major-minor"})


def _run(fixture_name: str):
    snap = build_local_snapshot(FIXTURES / fixture_name, META, "HEAD", DEFAULT_CFG)
    return list(VersionSignalCheck().run(snap))


def test_clean_repo_silent():
    findings = _run("clean_repo")
    assert findings == []


def test_drifted_repo_tiers():
    findings = _run("drifted_repo")
    by_sev = {f.severity: [] for f in findings}
    for f in findings:
        by_sev.setdefault(f.severity, []).append(f)

    # AGENTS.md 1.5.0 -> error (major_minor_differs)
    # CLAUDE.md 1.6.1 -> info (patch_differs)
    # majorminor SKILL 1.5.0 -> error
    # patch SKILL 1.6.1 -> info
    # newer.mdc 1.7.0 -> warn (tool_newer)
    sev_counts = {k: len(v) for k, v in by_sev.items()}
    assert sev_counts.get("error", 0) == 2
    assert sev_counts.get("warn", 0) == 1
    assert sev_counts.get("info", 0) == 2


def test_broken_repo_errors():
    findings = _run("broken_repo")
    # AGENTS missing, CLAUDE malformed, 3 skill/rule missing/wrongpos -> all errors
    assert all(f.severity == "error" for f in findings)
    assert len(findings) >= 5
    # Every error carries a suggested_fix with the Phase 1 script name.
    assert all(f.suggested_fix for f in findings)
    assert any("add_comment_marker.py" in (f.suggested_fix or "") for f in findings)
    assert any("add_frontmatter.py" in (f.suggested_fix or "") for f in findings)


def test_ignored_repo_emits_info_not_error():
    findings = _run("ignored_repo")
    assert len(findings) == 3
    assert all(f.severity == "info" for f in findings)
    assert all("skipped by drift-ignore pragma" in f.message for f in findings)


def test_skip_via_config():
    cfg = DriftConfig(
        repos={"drifted_repo": {"skip_checks": ["version-signal"]}},
        globals={"signal_policy": "same-major-minor"},
    )
    snap = build_local_snapshot(FIXTURES / "drifted_repo", META, "HEAD", cfg)
    findings = list(VersionSignalCheck().run(snap))
    assert findings == []


def test_mcp_repo_is_clean():
    findings = _run("mcp_repo")
    assert findings == []


def test_check_name_attribute():
    assert VersionSignalCheck.name == "version-signal"
    assert VersionSignalCheck().name == "version-signal"
