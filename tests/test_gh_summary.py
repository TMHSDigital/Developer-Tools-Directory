from pathlib import Path

import pytest

from scripts.drift_check.report import gh_summary
from scripts.drift_check.semver import parse_version
from scripts.drift_check.types import (
    DriftConfig,
    Finding,
    RepoConfig,
    RepoSnapshot,
)


META = parse_version("1.6.3")


def _make_snapshot(slug: str, repo_type: str = "cursor-plugin") -> RepoSnapshot:
    return RepoSnapshot(
        slug=slug,
        repo_type=repo_type,
        files={},
        meta_version=META,
        meta_commit="sha",
        config=RepoConfig(slug=slug, repo_type=repo_type),
    )


def test_render_clean():
    text = gh_summary.render([_make_snapshot("repo-a")], [])
    assert "Drift report" in text
    assert "clean" in text.lower()
    assert "1 repos" in text


def test_render_with_findings():
    snap = _make_snapshot("repo-a")
    findings = [
        Finding(
            repo="repo-a",
            file=Path("AGENTS.md"),
            check="version-signal",
            severity="error",
            message="tool at 1.5.0, meta at 1.7.0",
        ),
        Finding(
            repo="repo-a",
            file=Path("CLAUDE.md"),
            check="stale-counts",
            severity="warn",
            message="aggregate count at line 3",
        ),
    ]
    text = gh_summary.render([snap], findings)
    assert "1 errors" in text
    assert "1 warnings" in text
    assert "version-signal" in text
    assert "<details>" in text
    assert "repo-a" in text


def test_render_hides_info_by_default():
    snap = _make_snapshot("repo-a")
    findings = [
        Finding(
            repo="repo-a",
            file=Path("AGENTS.md"),
            check="version-signal",
            severity="info",
            message="patch differs",
        ),
    ]
    assert "patch differs" not in gh_summary.render([snap], findings)
    assert "patch differs" in gh_summary.render([snap], findings, verbose=True)


def test_write_summary_requires_env():
    with pytest.raises(gh_summary.GHSummaryError):
        gh_summary.write_summary([_make_snapshot("r")], [], env={})


def test_write_summary_appends(tmp_path: Path):
    target = tmp_path / "summary.md"
    env = {"GITHUB_STEP_SUMMARY": str(target)}
    p = gh_summary.write_summary([_make_snapshot("r")], [], env=env)
    assert p == target
    first = target.read_text(encoding="utf-8")
    # Second call appends (Actions-runner semantics).
    gh_summary.write_summary([_make_snapshot("r2")], [], env=env)
    assert target.read_text(encoding="utf-8").startswith(first)
    assert "r2" in target.read_text(encoding="utf-8") or "clean" in target.read_text(encoding="utf-8").lower()


def test_escapes_pipes_in_message():
    snap = _make_snapshot("repo-a")
    findings = [
        Finding(
            repo="repo-a",
            file=Path("file.md"),
            check="c",
            severity="error",
            message="bad | pipe",
        ),
    ]
    text = gh_summary.render([snap], findings)
    assert "bad \\| pipe" in text
