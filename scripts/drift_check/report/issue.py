"""Sticky-issue upsert (Decision 3 + Q1 reopen-on-drift).

State machine:

| findings have err/warn | issue exists | issue state | action          |
| ---------------------- | ------------ | ----------- | --------------- |
| yes                    | no           | -           | create          |
| yes                    | yes          | open        | update body     |
| yes                    | yes          | closed      | reopen + update + comment |
| no                     | yes          | open        | close + comment |
| no                     | yes          | closed      | no_op           |
| no                     | no           | -           | no_op           |

Identification: a sticky-marker HTML comment in the body. A title-based
search is fragile (titles drift); the marker is exact and version-bumpable.

Implementation uses the ``gh`` CLI via subprocess. The function shells
out one or two times per call. Tests inject a runner so they can assert
the exact gh commands issued without spawning real processes.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Literal, Optional, Sequence

from ..types import Finding, RepoSnapshot
from . import markdown as md_renderer


# Marker is versioned so future schema changes don't collide with the
# current sticky issue. Bump the suffix when the body schema changes
# in a way that would confuse downstream consumers.
STICKY_MARKER = "<!-- drift-check-sticky-issue-v1 -->"
STICKY_TITLE = "Ecosystem drift report (live)"

IssueAction = Literal["created", "updated", "reopened", "closed", "no_op"]


# GitHub rejects issue bodies over 65,536 characters. Leave headroom for
# the truncation notice.
MAX_BODY_CHARS = 60_000
GH_TIMEOUT_SECONDS = 120

# Runner type: takes a list of args plus an optional ``stdin`` keyword
# (used for ``--body-file -``), returns (rc, stdout, stderr).
GhRunner = Callable[..., "tuple[int, str, str]"]


def make_gh_runner(gh_token: str | None = None) -> GhRunner:
    """Build the default subprocess runner. When *gh_token* is given it is
    exported as ``GH_TOKEN`` for every ``gh`` call, so the token the caller
    supplied is the one used for writes (not whatever ambient login or
    ``GITHUB_TOKEN`` happens to exist)."""
    env = {**os.environ}
    if gh_token:
        env["GH_TOKEN"] = gh_token

    def _run(args: Sequence[str], stdin: str | None = None) -> "tuple[int, str, str]":
        try:
            result = subprocess.run(
                ["gh", *args],
                input=stdin,
                capture_output=True,
                text=True,
                env=env,
                timeout=GH_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return 124, "", f"gh {' '.join(args[:2])} timed out after {GH_TIMEOUT_SECONDS}s"
        return result.returncode, result.stdout, result.stderr

    return _run


def _default_gh_runner(args: Sequence[str], stdin: str | None = None) -> "tuple[int, str, str]":
    """Default runner using the ambient ``gh`` authentication."""
    return make_gh_runner()(args, stdin=stdin)


def _truncate_body(body: str) -> str:
    if len(body) <= MAX_BODY_CHARS:
        return body
    notice = "\n".join([
        "",
        "",
        "---",
        "",
        "_Report truncated to fit GitHub's issue size limit. "
        "The full report is in the drift-check workflow run summary._",
        "",
    ])
    return body[: MAX_BODY_CHARS - len(notice)] + notice


def _has_blocking_findings(findings: Iterable[Finding]) -> bool:
    """Anything that should make the sticky issue exist (open). ``info`` is
    intentionally excluded; info findings do not justify a sticky issue."""
    return any(f.severity in ("error", "warn") for f in findings)


def _build_issue_body(
    snapshots: Sequence[RepoSnapshot],
    findings: Sequence[Finding],
    meta_commit: str,
    *,
    now: datetime | None = None,
) -> str:
    now = now or datetime.now(timezone.utc)
    err = sum(1 for f in findings if f.severity == "error")
    warn = sum(1 for f in findings if f.severity == "warn")
    info = sum(1 for f in findings if f.severity == "info")
    body = [
        STICKY_MARKER,
        "",
        f"**Generated:** `{now.isoformat(timespec='seconds')}`  ",
        f"**Meta-repo commit:** `{meta_commit}`  ",
        f"**Tally:** {err} errors, {warn} warnings, {info} infos across "
        f"{len(snapshots)} repos",
        "",
        "---",
        "",
        md_renderer.render(snapshots, findings, verbose=False),
        "",
        "---",
        "",
        "_This issue is updated automatically by the drift checker. "
        "It is closed when all repos are clean and reopened on the "
        "next run that detects drift._",
    ]
    return "\n".join(body)


def _find_sticky_issue(
    repo: str,
    runner: GhRunner,
) -> Optional[dict]:
    """Search by marker. Returns the first issue (open OR closed) whose
    body actually contains the marker, or None.

    ``gh issue list --search`` is a tokenized full-text search, so it can
    return near-misses; each candidate's body is checked for the exact
    marker. Title is not used because humans may edit it; the marker is
    structural."""
    rc, out, err = runner([
        "issue", "list",
        "--repo", repo,
        "--state", "all",
        "--search", STICKY_MARKER,
        "--json", "number,state,title,url,body",
        "--limit", "20",
    ])
    if rc != 0:
        raise RuntimeError(f"gh issue list failed: {err.strip() or out.strip()}")
    items = json.loads(out or "[]")
    for item in items:
        if STICKY_MARKER in (item.get("body") or ""):
            return item
    return None


def upsert_sticky_issue(
    snapshots: Sequence[RepoSnapshot],
    findings: Sequence[Finding],
    meta_commit: str,
    *,
    repo: str = "TMHSDigital/Developer-Tools-Directory",
    runner: GhRunner | None = None,
    now: datetime | None = None,
    gh_token: str | None = None,
) -> "tuple[IssueAction, Optional[str]]":
    """Run the sticky-issue state machine.

    Returns ``(action, issue_url)``. ``issue_url`` is None for ``no_op``.
    *gh_token*, when given, authenticates the default runner.
    """
    runner = runner or make_gh_runner(gh_token)
    findings = list(findings)
    snapshots = list(snapshots)

    has_drift = _has_blocking_findings(findings)
    existing = _find_sticky_issue(repo, runner)

    if not has_drift:
        if existing and existing["state"].upper() == "OPEN":
            comment = (
                f"Drift cleared as of `{meta_commit}`. Closing sticky issue."
            )
            _gh_comment(repo, existing["number"], comment, runner)
            _gh_close(repo, existing["number"], runner)
            return "closed", existing["url"]
        return "no_op", existing["url"] if existing else None

    body = _truncate_body(_build_issue_body(snapshots, findings, meta_commit, now=now))

    if existing is None:
        url = _gh_create(repo, STICKY_TITLE, body, runner)
        return "created", url

    number = existing["number"]
    _gh_edit(repo, number, body, runner)
    state = existing["state"].upper()
    if state in ("CLOSED", "COMPLETED"):
        _gh_reopen(repo, number, runner)
        comment = (
            f"Drift re-detected as of `{meta_commit}`. See body for details."
        )
        _gh_comment(repo, number, comment, runner)
        return "reopened", existing["url"]
    return "updated", existing["url"]


# ---- gh CLI shims (small so tests can intercept individually) -------------


def _gh_create(repo: str, title: str, body: str, runner: GhRunner) -> str:
    rc, out, err = runner([
        "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body-file", "-",
    ], stdin=body)
    if rc != 0:
        raise RuntimeError(f"gh issue create failed: {err.strip() or out.strip()}")
    # gh prints the issue URL on stdout.
    return out.strip().splitlines()[-1] if out.strip() else ""


def _gh_edit(repo: str, number: int, body: str, runner: GhRunner) -> None:
    rc, out, err = runner([
        "issue", "edit", str(number),
        "--repo", repo,
        "--body-file", "-",
    ], stdin=body)
    if rc != 0:
        raise RuntimeError(f"gh issue edit failed: {err.strip() or out.strip()}")


def _gh_close(repo: str, number: int, runner: GhRunner) -> None:
    rc, out, err = runner([
        "issue", "close", str(number),
        "--repo", repo,
    ])
    if rc != 0:
        raise RuntimeError(f"gh issue close failed: {err.strip() or out.strip()}")


def _gh_reopen(repo: str, number: int, runner: GhRunner) -> None:
    rc, out, err = runner([
        "issue", "reopen", str(number),
        "--repo", repo,
    ])
    if rc != 0:
        raise RuntimeError(f"gh issue reopen failed: {err.strip() or out.strip()}")


def _gh_comment(repo: str, number: int, body: str, runner: GhRunner) -> None:
    rc, out, err = runner([
        "issue", "comment", str(number),
        "--repo", repo,
        "--body-file", "-",
    ], stdin=body)
    if rc != 0:
        raise RuntimeError(f"gh issue comment failed: {err.strip() or out.strip()}")
