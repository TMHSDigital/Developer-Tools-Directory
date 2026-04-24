"""Tests for the Session C CLI flags: --remote, --all, --gh-token,
--update-sticky-issue."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.drift_check import cli
from tests.conftest import FIXTURES


@pytest.fixture
def meta_repo(tmp_path: Path) -> Path:
    root = tmp_path / "meta"
    root.mkdir()
    (root / "VERSION").write_text("1.6.3", encoding="utf-8")
    (root / "standards").mkdir()
    (root / "standards" / "required-refs.json").write_text(
        '{"version": 1, "requirements": {"cursor-plugin": {}, "mcp-server": {}}}',
        encoding="utf-8",
    )
    (root / "registry.json").write_text(
        json.dumps([
            {"repo": "TMHSDigital/Alpha", "status": "active"},
            {"repo": "TMHSDigital/Beta", "status": "active"},
            {"repo": "TMHSDigital/Stale", "status": "archived"},
        ]),
        encoding="utf-8",
    )
    return root


def _base(meta_repo: Path) -> list[str]:
    return ["--meta-repo", str(meta_repo), "--config", "nonexistent.json"]


def test_remote_without_token_errors(capsys, meta_repo: Path, monkeypatch):
    monkeypatch.delenv("DRIFT_CHECK_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    rc = cli.main(["--remote", "TMHSDigital/Alpha", *_base(meta_repo)])
    assert rc == 2
    assert "gh-token" in capsys.readouterr().err.lower()


def test_all_without_registry_errors(capsys, tmp_path: Path):
    bare = tmp_path / "bare-meta"
    bare.mkdir()
    (bare / "VERSION").write_text("1.6.3", encoding="utf-8")
    rc = cli.main([
        "--all",
        "--meta-repo", str(bare),
        "--config", "nonexistent.json",
        "--gh-token", "x",
    ])
    assert rc == 2
    assert "registry.json" in capsys.readouterr().err


def test_all_expands_active_repos(capsys, meta_repo: Path):
    """--all without a working network would normally fail at sparse-checkout.
    We patch build_remote_snapshot to verify the expansion logic only."""
    seen = []

    def fake_remote(repo_slug, **kw):
        seen.append((repo_slug, kw["owner"]))
        from scripts.drift_check.types import RepoConfig, RepoSnapshot
        return RepoSnapshot(
            slug=repo_slug,
            repo_type="cursor-plugin",
            files={},
            meta_version=kw["meta_version"],
            meta_commit=kw["meta_commit"],
            config=RepoConfig(slug=repo_slug, repo_type="cursor-plugin"),
        )

    with patch("scripts.drift_check.cli.build_remote_snapshot", side_effect=fake_remote):
        rc = cli.main(["--all", "--gh-token", "x", *_base(meta_repo)])
    # 2 active entries; archived is skipped
    assert {s for s, _ in seen} == {"Alpha", "Beta"}
    assert all(o == "TMHSDigital" for _, o in seen)
    # Empty snapshots have no findings -> exit 0
    assert rc == 0


def test_remote_slug_without_owner_defaults_to_TMHSDigital(meta_repo: Path):
    seen = []

    def fake_remote(repo_slug, **kw):
        seen.append((repo_slug, kw["owner"]))
        from scripts.drift_check.types import RepoConfig, RepoSnapshot
        return RepoSnapshot(
            slug=repo_slug, repo_type="cursor-plugin", files={},
            meta_version=kw["meta_version"], meta_commit=kw["meta_commit"],
            config=RepoConfig(slug=repo_slug, repo_type="cursor-plugin"),
        )

    with patch("scripts.drift_check.cli.build_remote_snapshot", side_effect=fake_remote):
        cli.main(["--remote", "Foo-Bar", "--gh-token", "x", *_base(meta_repo)])
    assert seen == [("Foo-Bar", "TMHSDigital")]


def test_remote_slug_with_owner_parses(meta_repo: Path):
    seen = []

    def fake_remote(repo_slug, **kw):
        seen.append((repo_slug, kw["owner"]))
        from scripts.drift_check.types import RepoConfig, RepoSnapshot
        return RepoSnapshot(
            slug=repo_slug, repo_type="cursor-plugin", files={},
            meta_version=kw["meta_version"], meta_commit=kw["meta_commit"],
            config=RepoConfig(slug=repo_slug, repo_type="cursor-plugin"),
        )

    with patch("scripts.drift_check.cli.build_remote_snapshot", side_effect=fake_remote):
        cli.main(["--remote", "OtherOrg/Foo", "--gh-token", "x", *_base(meta_repo)])
    assert seen == [("Foo", "OtherOrg")]


def test_token_env_fallback(meta_repo: Path, monkeypatch):
    monkeypatch.setenv("DRIFT_CHECK_TOKEN", "from-env")
    seen = []

    def fake_remote(repo_slug, **kw):
        seen.append(kw["gh_token"])
        from scripts.drift_check.types import RepoConfig, RepoSnapshot
        return RepoSnapshot(
            slug=repo_slug, repo_type="cursor-plugin", files={},
            meta_version=kw["meta_version"], meta_commit=kw["meta_commit"],
            config=RepoConfig(slug=repo_slug, repo_type="cursor-plugin"),
        )

    with patch("scripts.drift_check.cli.build_remote_snapshot", side_effect=fake_remote):
        cli.main(["--remote", "Alpha", *_base(meta_repo)])
    assert seen == ["from-env"]


def test_update_sticky_issue_invokes_upsert(capsys, meta_repo: Path):
    # Use clean_repo locally so there's nothing to flag => sticky upsert
    # is called with no findings (no_op state).
    captured = {}

    def fake_upsert(snapshots, findings, meta_commit, **kw):
        captured["snapshots"] = list(snapshots)
        captured["findings"] = list(findings)
        captured["meta_commit"] = meta_commit
        captured["repo"] = kw.get("repo")
        return ("no_op", None)

    with patch("scripts.drift_check.cli.issue.upsert_sticky_issue", side_effect=fake_upsert):
        rc = cli.main([
            "--local", str(FIXTURES / "clean_repo"),
            "--update-sticky-issue",
            "--gh-token", "x",
            "--meta-commit", "deadbeef",
            *_base(meta_repo),
        ])
    assert rc == 0
    assert captured["meta_commit"] == "deadbeef"
    assert captured["repo"] == "TMHSDigital/Developer-Tools-Directory"
    out = capsys.readouterr().out
    assert "Sticky issue: no_op" in out


def test_update_sticky_issue_without_token_errors(capsys, meta_repo: Path, monkeypatch):
    monkeypatch.delenv("DRIFT_CHECK_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    rc = cli.main([
        "--local", str(FIXTURES / "clean_repo"),
        "--update-sticky-issue",
        *_base(meta_repo),
    ])
    assert rc == 2
    assert "gh-token" in capsys.readouterr().err.lower()


def test_update_sticky_issue_propagates_runtime_error(meta_repo: Path):
    def fake_upsert(*a, **kw):
        raise RuntimeError("gh failed")

    with patch("scripts.drift_check.cli.issue.upsert_sticky_issue", side_effect=fake_upsert):
        rc = cli.main([
            "--local", str(FIXTURES / "clean_repo"),
            "--update-sticky-issue",
            "--gh-token", "x",
            *_base(meta_repo),
        ])
    assert rc == 2
