"""Tests for the sticky-issue upsert state machine."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import pytest

from scripts.drift_check.report import issue
from scripts.drift_check.report.issue import (
    STICKY_MARKER,
    STICKY_TITLE,
    upsert_sticky_issue,
)
from scripts.drift_check.semver import parse_version
from scripts.drift_check.types import (
    Finding,
    RepoConfig,
    RepoSnapshot,
)


META = parse_version("1.7.1")


def _snap(slug: str = "x") -> RepoSnapshot:
    return RepoSnapshot(
        slug=slug,
        repo_type="cursor-plugin",
        files={},
        meta_version=META,
        meta_commit="sha",
        config=RepoConfig(slug=slug, repo_type="cursor-plugin"),
    )


def _err(repo: str = "x", msg: str = "drift") -> Finding:
    return Finding(
        repo=repo,
        file=Path("AGENTS.md"),
        check="version-signal",
        severity="error",
        message=msg,
    )


class _ScriptedRunner:
    """Records every gh call; returns scripted results in order. If a
    call's first arg matches a registered handler key, that handler is
    used; else falls back to the queue."""

    def __init__(self, queue=None, handlers=None):
        self.queue = list(queue or [])
        self.handlers = handlers or {}
        self.calls = []

    def __call__(self, args: Sequence[str]):
        args = list(args)
        self.calls.append(args)
        for key, handler in self.handlers.items():
            if args[: len(key)] == list(key):
                return handler(args)
        if self.queue:
            return self.queue.pop(0)
        return 0, "", ""


# ------------------------------- create -----------------------------------


def test_create_when_no_existing_and_drift():
    runner = _ScriptedRunner(queue=[
        (0, "[]", ""),  # gh issue list returns empty
        (0, "https://github.com/.../issues/42\n", ""),  # gh issue create
    ])
    action, url = upsert_sticky_issue(
        [_snap()], [_err()], meta_commit="abc123", runner=runner,
    )
    assert action == "created"
    assert "issues/42" in url

    # First call: gh issue list with the marker as search
    list_args = runner.calls[0]
    assert list_args[0] == "issue"
    assert list_args[1] == "list"
    assert "--search" in list_args
    assert STICKY_MARKER in list_args

    # Second call: gh issue create with the title and body containing marker
    create_args = runner.calls[1]
    assert create_args[0] == "issue"
    assert create_args[1] == "create"
    body_idx = create_args.index("--body") + 1
    body = create_args[body_idx]
    assert STICKY_MARKER in body
    assert "abc123" in body  # meta commit appears in body
    assert STICKY_TITLE in create_args


# ------------------------------- update -----------------------------------


def test_update_when_existing_open_and_drift():
    existing = json.dumps([{
        "number": 7,
        "state": "OPEN",
        "title": STICKY_TITLE,
        "url": "https://github.com/.../issues/7",
    }])
    runner = _ScriptedRunner(queue=[
        (0, existing, ""),  # gh issue list
        (0, "", ""),         # gh issue edit
    ])
    action, url = upsert_sticky_issue(
        [_snap()], [_err()], meta_commit="abc", runner=runner,
    )
    assert action == "updated"
    assert "issues/7" in url
    edit_args = runner.calls[1]
    assert edit_args[:3] == ["issue", "edit", "7"]


# ------------------------------- reopen -----------------------------------


def test_reopen_when_existing_closed_and_drift():
    existing = json.dumps([{
        "number": 11,
        "state": "CLOSED",
        "title": STICKY_TITLE,
        "url": "https://github.com/.../issues/11",
    }])
    runner = _ScriptedRunner(queue=[
        (0, existing, ""),  # gh issue list
        (0, "", ""),         # gh issue edit
        (0, "", ""),         # gh issue reopen
        (0, "", ""),         # gh issue comment
    ])
    action, url = upsert_sticky_issue(
        [_snap()], [_err()], meta_commit="abc", runner=runner,
    )
    assert action == "reopened"
    assert "issues/11" in url
    # Verify reopen call exists
    reopen_calls = [c for c in runner.calls if c[:3] == ["issue", "reopen", "11"]]
    assert len(reopen_calls) == 1
    # Verify comment includes "re-detected"
    comment_calls = [c for c in runner.calls if c[:3] == ["issue", "comment", "11"]]
    assert len(comment_calls) == 1
    body_idx = comment_calls[0].index("--body") + 1
    assert "re-detected" in comment_calls[0][body_idx]


# ------------------------------- close ------------------------------------


def test_close_when_existing_open_and_clean():
    existing = json.dumps([{
        "number": 9,
        "state": "OPEN",
        "title": STICKY_TITLE,
        "url": "https://github.com/.../issues/9",
    }])
    runner = _ScriptedRunner(queue=[
        (0, existing, ""),  # gh issue list
        (0, "", ""),         # gh issue comment
        (0, "", ""),         # gh issue close
    ])
    action, url = upsert_sticky_issue(
        [_snap()], [], meta_commit="abc", runner=runner,
    )
    assert action == "closed"
    assert "issues/9" in url
    # Comment posted before close
    assert any(c[:3] == ["issue", "comment", "9"] for c in runner.calls)
    assert any(c[:3] == ["issue", "close", "9"] for c in runner.calls)


# ------------------------------- no_op ------------------------------------


def test_no_op_when_clean_and_no_existing():
    runner = _ScriptedRunner(queue=[(0, "[]", "")])
    action, url = upsert_sticky_issue(
        [_snap()], [], meta_commit="abc", runner=runner,
    )
    assert action == "no_op"
    assert url is None
    # Only one call: the search
    assert len(runner.calls) == 1


def test_no_op_when_clean_and_existing_closed():
    existing = json.dumps([{
        "number": 9,
        "state": "CLOSED",
        "title": STICKY_TITLE,
        "url": "https://github.com/.../issues/9",
    }])
    runner = _ScriptedRunner(queue=[(0, existing, "")])
    action, url = upsert_sticky_issue(
        [_snap()], [], meta_commit="abc", runner=runner,
    )
    assert action == "no_op"
    assert "issues/9" in url
    # No edit/close/reopen calls
    assert len(runner.calls) == 1


# ------------------------------- info-only suppressed ----------------------


def test_info_only_does_not_create_issue():
    info = Finding(
        repo="x", file=Path("AGENTS.md"), check="version-signal",
        severity="info", message="patch differs",
    )
    runner = _ScriptedRunner(queue=[(0, "[]", "")])
    action, _ = upsert_sticky_issue(
        [_snap()], [info], meta_commit="abc", runner=runner,
    )
    # info alone is not blocking; treated as clean for sticky purposes
    assert action == "no_op"


# ------------------------------- gh failures --------------------------------


def test_raises_on_list_failure():
    runner = _ScriptedRunner(queue=[(1, "", "auth error")])
    with pytest.raises(RuntimeError, match="auth error"):
        upsert_sticky_issue([_snap()], [_err()], meta_commit="x", runner=runner)


def test_raises_on_create_failure():
    runner = _ScriptedRunner(queue=[
        (0, "[]", ""),
        (1, "", "permission denied"),
    ])
    with pytest.raises(RuntimeError, match="permission denied"):
        upsert_sticky_issue([_snap()], [_err()], meta_commit="x", runner=runner)


# ------------------------------- body shape --------------------------------


def test_body_includes_marker_and_metadata():
    runner = _ScriptedRunner(queue=[(0, "[]", ""), (0, "u\n", "")])
    fixed = datetime(2026, 4, 24, 22, 0, 0, tzinfo=timezone.utc)
    upsert_sticky_issue(
        [_snap()], [_err()], meta_commit="cafef00d",
        runner=runner, now=fixed,
    )
    body = runner.calls[1][runner.calls[1].index("--body") + 1]
    assert STICKY_MARKER in body
    assert "cafef00d" in body
    assert "2026-04-24T22:00:00+00:00" in body
    assert "1 errors, 0 warnings" in body
