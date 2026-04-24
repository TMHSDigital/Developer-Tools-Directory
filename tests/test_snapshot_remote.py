"""Tests for ``build_remote_snapshot`` and the sparse-checkout helper.

Most tests mock ``subprocess.run`` so we never actually clone anything.
The optional integration test (gated on ``DRIFT_CHECK_INTEGRATION_TOKEN``)
exercises a real sparse-checkout against CFX-Developer-Tools and verifies
the snapshot matches what ``build_local_snapshot`` produces against the
local clone at ``E:\\CFX-Developer-Tools``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.drift_check.config import load_config
from scripts.drift_check.semver import parse_version
from scripts.drift_check.snapshot import (
    SPARSE_PATHS,
    RemoteSnapshotError,
    _scrub_token_from_remote,
    build_remote_snapshot,
)


META = parse_version("1.6.3")


def _cfg():
    return load_config(Path("does-not-exist.json"))


class _FakeRun:
    """Records every subprocess.run invocation and returns scripted
    results."""

    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((tuple(args), kwargs))
        if self.results:
            rc, stdout, stderr = self.results.pop(0)
        else:
            rc, stdout, stderr = 0, "", ""

        class _Result:
            returncode = rc
            stdout = ""
            stderr = ""

        result = _Result()
        result.returncode = rc
        result.stdout = stdout
        result.stderr = stderr
        return result


def test_remote_snapshot_issues_correct_git_commands(tmp_path: Path):
    fake = _FakeRun([
        (0, "", ""),  # clone
        (0, "", ""),  # remote set-url (token scrub)
        (0, "", ""),  # sparse-checkout set
    ])
    # Patch tempfile so we know exactly which tempdir gets used.
    sparse_dir = tmp_path / "sparse"
    sparse_dir.mkdir()
    with patch("scripts.drift_check.snapshot.subprocess.run", fake), \
         patch("scripts.drift_check.snapshot.tempfile.mkdtemp", return_value=str(sparse_dir)):
        snap = build_remote_snapshot(
            repo_slug="CFX-Developer-Tools",
            meta_version=META,
            meta_commit="sha",
            config=_cfg(),
            gh_token="ghp_test",
        )

    assert snap.slug == "CFX-Developer-Tools"
    # Empty fixture dir => unknown repo_type
    assert snap.repo_type == "unknown"
    # Tempdir was cleaned up
    assert not sparse_dir.exists()

    # Verify clone command shape
    clone_args = fake.calls[0][0]
    assert clone_args[0] == "git"
    assert clone_args[1] == "clone"
    assert "--filter=blob:none" in clone_args
    assert "--sparse" in clone_args
    assert "--depth" in clone_args
    # Token must be in the clone URL
    url = [a for a in clone_args if a.startswith("https://")]
    assert url and "ghp_test" in url[0]
    assert "github.com/TMHSDigital/CFX-Developer-Tools.git" in url[0]

    # Verify token scrub is the second call
    scrub_args = fake.calls[1][0]
    assert scrub_args[1] == "remote"
    assert scrub_args[2] == "set-url"
    assert "ghp_test" not in " ".join(scrub_args)

    # Verify sparse-checkout uses --no-cone (required for file-level
    # patterns like AGENTS.md) and includes all SPARSE_PATHS
    sparse_args = fake.calls[2][0]
    assert sparse_args[1] == "sparse-checkout"
    assert sparse_args[2] == "set"
    assert "--no-cone" in sparse_args
    for p in SPARSE_PATHS:
        assert p in sparse_args


def test_remote_snapshot_cleans_up_on_clone_failure(tmp_path: Path):
    fake = _FakeRun([(128, "", "fatal: repository not found")])
    sparse_dir = tmp_path / "sparse"
    sparse_dir.mkdir()
    with patch("scripts.drift_check.snapshot.subprocess.run", fake), \
         patch("scripts.drift_check.snapshot.tempfile.mkdtemp", return_value=str(sparse_dir)):
        with pytest.raises(RemoteSnapshotError) as exc_info:
            build_remote_snapshot(
                repo_slug="missing-repo",
                meta_version=META,
                meta_commit="sha",
                config=_cfg(),
                gh_token="ghp_test",
            )
    assert "repository not found" in str(exc_info.value).lower() or "rc=128" in str(exc_info.value)
    # Tempdir must be cleaned up even on error
    assert not sparse_dir.exists()


def test_remote_snapshot_cleans_up_on_sparse_failure(tmp_path: Path):
    fake = _FakeRun([
        (0, "", ""),         # clone OK
        (0, "", ""),         # scrub OK
        (1, "", "bad path"),  # sparse-checkout FAIL
    ])
    sparse_dir = tmp_path / "sparse"
    sparse_dir.mkdir()
    with patch("scripts.drift_check.snapshot.subprocess.run", fake), \
         patch("scripts.drift_check.snapshot.tempfile.mkdtemp", return_value=str(sparse_dir)):
        with pytest.raises(RemoteSnapshotError):
            build_remote_snapshot(
                repo_slug="x",
                meta_version=META,
                meta_commit="sha",
                config=_cfg(),
                gh_token="ghp_test",
            )
    assert not sparse_dir.exists()


def test_remote_snapshot_rejects_empty_token(tmp_path: Path):
    sparse_dir = tmp_path / "sparse"
    sparse_dir.mkdir()
    with patch("scripts.drift_check.snapshot.tempfile.mkdtemp", return_value=str(sparse_dir)):
        with pytest.raises(RemoteSnapshotError, match="empty"):
            build_remote_snapshot(
                repo_slug="x",
                meta_version=META,
                meta_commit="sha",
                config=_cfg(),
                gh_token="   ",
            )
    assert not sparse_dir.exists()


def test_scrub_does_not_raise_on_failure(tmp_path: Path):
    """Scrub is best-effort. If git remote set-url fails for some reason
    (e.g., the clone partially succeeded), the snapshot still completes."""
    fake = _FakeRun([(1, "", "no remote")])
    with patch("scripts.drift_check.snapshot.subprocess.run", fake):
        # Should not raise
        _scrub_token_from_remote(tmp_path, "TMHSDigital", "x")


@pytest.mark.skipif(
    not os.environ.get("DRIFT_CHECK_INTEGRATION_TOKEN"),
    reason="set DRIFT_CHECK_INTEGRATION_TOKEN to run real sparse-checkout test",
)
def test_remote_matches_local_for_cfx():
    """Real sparse-checkout against CFX-Developer-Tools and compare
    against the local clone at E:\\CFX-Developer-Tools."""
    from scripts.drift_check.snapshot import build_local_snapshot
    token = os.environ["DRIFT_CHECK_INTEGRATION_TOKEN"]

    remote = build_remote_snapshot(
        repo_slug="CFX-Developer-Tools",
        meta_version=META,
        meta_commit="sha",
        config=_cfg(),
        gh_token=token,
    )
    local = build_local_snapshot(
        repo_path=Path(r"E:\CFX-Developer-Tools"),
        meta_version=META,
        meta_commit="sha",
        config=_cfg(),
    )

    # Same files, same repo_type. Content may differ if local has
    # uncommitted changes — compare file paths and signal counts only.
    assert remote.repo_type == local.repo_type
    assert set(remote.files.keys()) == set(local.files.keys())
    assert sum(1 for f in remote.files.values() if f.signal) == \
           sum(1 for f in local.files.values() if f.signal)
