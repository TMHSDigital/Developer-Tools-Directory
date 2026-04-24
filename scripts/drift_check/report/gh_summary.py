"""GitHub Actions step-summary renderer.

Writes a GitHub-flavored-markdown report to the file path in
``$GITHUB_STEP_SUMMARY`` (set by the Actions runner). Consumers that want
both stdout and step-summary output call ``render()`` and
``write_summary()`` separately — keeping the pure render logic
independent of the env-var side effect.

Not imported from ``cli.py`` by default; it is wired in when
``--format gh-summary`` is passed OR when ``$GITHUB_STEP_SUMMARY`` is set
in the environment. Session C's composite action will rely on this.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Sequence

from ..types import Finding, RepoSnapshot


SEV_EMOJI = {"error": "❌", "warn": "⚠️", "info": "ℹ️"}


def render(
    snapshots: Sequence[RepoSnapshot],
    findings: Iterable[Finding],
    *,
    verbose: bool = False,
) -> str:
    findings_list = list(findings)
    if not verbose:
        findings_list = [f for f in findings_list if f.severity != "info"]

    total_err = sum(1 for f in findings_list if f.severity == "error")
    total_warn = sum(1 for f in findings_list if f.severity == "warn")
    total_info = sum(1 for f in findings_list if f.severity == "info")
    meta_version = snapshots[0].meta_version if snapshots else None
    total_files = sum(len(s.files) for s in snapshots)

    lines: List[str] = ["## Drift report", ""]
    if meta_version is not None:
        lines.append(f"**Meta-repo version:** `{meta_version}`  ")
    lines.append(f"**Checked:** {len(snapshots)} repos, {total_files} files")
    lines.append("")

    badge = _status_badge(total_err, total_warn)
    lines.append(f"**Status:** {badge}")
    lines.append("")

    if total_err + total_warn + total_info == 0:
        lines.append("All repos clean.")
        lines.append("")
        return "\n".join(lines) + "\n"

    by_repo: dict[str, list[Finding]] = {s.slug: [] for s in snapshots}
    for f in findings_list:
        by_repo.setdefault(f.repo, []).append(f)

    for snap in snapshots:
        repo_findings = by_repo.get(snap.slug, [])
        errs = sum(1 for f in repo_findings if f.severity == "error")
        warns = sum(1 for f in repo_findings if f.severity == "warn")
        icon = "✅" if not repo_findings else ("❌" if errs else "⚠️")
        title = f"{icon} {snap.slug} — {errs} errors, {warns} warnings"
        if not repo_findings:
            lines.append(f"- {title} (clean)")
            continue
        lines.append("<details>")
        lines.append(f"<summary>{title}</summary>")
        lines.append("")
        lines.append("| File | Check | Severity | Message |")
        lines.append("| ---- | ----- | -------- | ------- |")
        for f in repo_findings:
            emoji = SEV_EMOJI.get(f.severity, "")
            file_label = str(f.file).replace("\\", "/") if f.file else "-"
            msg = f.message.replace("|", "\\|")
            lines.append(
                f"| `{file_label}` | `{f.check}` | {emoji} {f.severity} | {msg} |"
            )
        lines.append("")
        lines.append("</details>")

    lines.append("")
    lines.append(
        f"**Summary:** {total_err} errors, {total_warn} warnings, "
        f"{total_info} infos across {len(snapshots)} repos."
    )
    return "\n".join(lines) + "\n"


def _status_badge(errors: int, warnings: int) -> str:
    if errors:
        return f"❌ {errors} errors, {warnings} warnings"
    if warnings:
        return f"⚠️ {warnings} warnings"
    return "✅ clean"


class GHSummaryError(Exception):
    """Raised when gh-summary rendering is requested outside Actions."""


def write_summary(
    snapshots: Sequence[RepoSnapshot],
    findings: Iterable[Finding],
    *,
    verbose: bool = False,
    env: dict[str, str] | None = None,
) -> Path:
    """Write the rendered summary to ``$GITHUB_STEP_SUMMARY``. Returns the
    path written. Raises ``GHSummaryError`` if the env var is not set."""
    env = env if env is not None else dict(os.environ)
    target = env.get("GITHUB_STEP_SUMMARY")
    if not target:
        raise GHSummaryError(
            "GITHUB_STEP_SUMMARY is not set; gh-summary format requires "
            "running inside a GitHub Actions job (or set the env var manually)."
        )
    path = Path(target)
    text = render(snapshots, findings, verbose=verbose)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Actions runner appends multiple writes; use append mode to match.
    with path.open("a", encoding="utf-8") as fh:
        fh.write(text)
    return path
