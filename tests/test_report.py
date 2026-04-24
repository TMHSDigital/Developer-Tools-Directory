import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.drift_check.report import json_out, markdown
from scripts.drift_check.semver import parse_version
from scripts.drift_check.snapshot import build_local_snapshot
from scripts.drift_check.types import DriftConfig, Finding

from tests.conftest import FIXTURES


META = parse_version("1.6.3")
assert META is not None
CFG = DriftConfig(globals={"signal_policy": "same-major-minor"})


def _snaps(names):
    return [build_local_snapshot(FIXTURES / n, META, "HEAD", CFG) for n in names]


def test_markdown_clean_repo_reports_clean():
    snaps = _snaps(["clean_repo"])
    out = markdown.render(snaps, [])
    assert "Meta-repo version: 1.6.3" in out
    assert "clean_repo (0 errors, 0 warnings)" in out
    assert "Clean." in out
    assert "Summary: 0 errors, 0 warnings, 0 infos" in out


def test_markdown_groups_findings_by_repo():
    snaps = _snaps(["clean_repo", "drifted_repo"])
    findings = [
        Finding(repo="drifted_repo", file=Path("AGENTS.md"), check="version-signal",
                severity="error", message="bad"),
        Finding(repo="drifted_repo", file=Path("CLAUDE.md"), check="version-signal",
                severity="warn", message="warn"),
    ]
    out = markdown.render(snaps, findings)
    assert "drifted_repo (1 errors, 1 warnings)" in out
    assert "| AGENTS.md | version-signal | error | bad |" in out


def test_markdown_verbose_flag_shows_info():
    snaps = _snaps(["clean_repo"])
    findings = [
        Finding(repo="clean_repo", file=Path("AGENTS.md"), check="version-signal",
                severity="info", message="info msg"),
    ]
    out_nonverbose = markdown.render(snaps, findings, verbose=False)
    assert "info msg" not in out_nonverbose

    out_verbose = markdown.render(snaps, findings, verbose=True)
    assert "info msg" in out_verbose
    assert "1 infos" in out_verbose


def test_markdown_escapes_pipes_in_message():
    snaps = _snaps(["clean_repo"])
    findings = [
        Finding(repo="clean_repo", file=Path("x.md"), check="c", severity="error",
                message="has | pipe"),
    ]
    out = markdown.render(snaps, findings)
    assert "has \\| pipe" in out


def test_json_shape_and_summary():
    snaps = _snaps(["clean_repo", "drifted_repo"])
    findings = [
        Finding(repo="drifted_repo", file=Path("a.md"), check="version-signal",
                severity="error", message="e"),
        Finding(repo="drifted_repo", file=Path("b.md"), check="version-signal",
                severity="warn", message="w"),
        Finding(repo="drifted_repo", file=Path("c.md"), check="version-signal",
                severity="info", message="i"),
    ]
    fixed_time = datetime(2026, 4, 24, 15, 30, 0, tzinfo=timezone.utc)
    payload = json.loads(json_out.render(snaps, findings, verbose=True, now=fixed_time))
    assert payload["meta_version"] == "1.6.3"
    assert payload["checked_at"] == "2026-04-24T15:30:00Z"
    assert payload["summary"] == {"errors": 1, "warnings": 1, "infos": 1}
    slugs = [r["slug"] for r in payload["repos"]]
    assert slugs == ["clean_repo", "drifted_repo"]


def test_json_nonverbose_drops_info():
    snaps = _snaps(["clean_repo"])
    findings = [
        Finding(repo="clean_repo", file=None, check="x", severity="info", message="i"),
    ]
    payload = json.loads(json_out.render(snaps, findings, verbose=False))
    assert payload["summary"]["infos"] == 0
    for r in payload["repos"]:
        assert r["findings"] == []


def test_json_null_file_preserved():
    snaps = _snaps(["clean_repo"])
    findings = [
        Finding(repo="clean_repo", file=None, check="x", severity="error", message="m"),
    ]
    payload = json.loads(json_out.render(snaps, findings))
    assert payload["repos"][0]["findings"][0]["file"] is None
