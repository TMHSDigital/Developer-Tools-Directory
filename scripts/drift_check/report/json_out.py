"""Machine-readable JSON renderer.

Output shape::

    {
      "meta_version": "1.6.3",
      "checked_at": "2026-04-24T15:30:00Z",
      "repos": [
        {"slug": "...", "repo_type": "...", "findings": [...]},
        ...
      ],
      "summary": {"errors": 1, "warnings": 2, "infos": 3}
    }

``checked_at`` is UTC ISO-8601 with second precision, suffixed ``Z``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Iterable, Sequence

from ..types import Finding, RepoSnapshot


def render(
    snapshots: Sequence[RepoSnapshot],
    findings: Iterable[Finding],
    *,
    verbose: bool = False,
    now: datetime | None = None,
) -> str:
    findings_list = list(findings)
    if not verbose:
        findings_list = [f for f in findings_list if f.severity != "info"]

    checked_at = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta_version = str(snapshots[0].meta_version) if snapshots else ""

    by_repo: dict[str, list[Finding]] = {s.slug: [] for s in snapshots}
    for f in findings_list:
        by_repo.setdefault(f.repo, []).append(f)

    repos_out = []
    for snap in snapshots:
        repos_out.append(
            {
                "slug": snap.slug,
                "repo_type": snap.repo_type,
                "files_checked": len(snap.files),
                "findings": [_finding_to_dict(f) for f in by_repo.get(snap.slug, [])],
            }
        )

    summary = {
        "errors": sum(1 for f in findings_list if f.severity == "error"),
        "warnings": sum(1 for f in findings_list if f.severity == "warn"),
        "infos": sum(1 for f in findings_list if f.severity == "info"),
    }

    payload = {
        "meta_version": meta_version,
        "checked_at": checked_at,
        "repos": repos_out,
        "summary": summary,
    }
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def _finding_to_dict(f: Finding) -> dict:
    return {
        "repo": f.repo,
        "file": str(f.file).replace("\\", "/") if f.file else None,
        "check": f.check,
        "severity": f.severity,
        "message": f.message,
        "suggested_fix": f.suggested_fix,
    }
