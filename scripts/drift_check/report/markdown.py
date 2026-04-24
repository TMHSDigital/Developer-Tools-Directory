"""Human-friendly markdown renderer.

Output shape (matches the example in the design-doc handoff brief)::

    # Drift report

    Meta-repo version: 1.6.3
    Checked: 8 repos, 248 files

    ## CFX-Developer-Tools (0 errors, 0 warnings)
    Clean.

    ## Example-With-Drift (1 error, 2 warnings)
    | File | Check | Severity | Message |
    | ---- | ----- | -------- | ------- |
    | ... | ... | ... | ... |

    Summary: 1 error, 2 warnings, 3 infos across 8 repos.
"""
from __future__ import annotations

from typing import Iterable, List, Sequence

from ..types import Finding, RepoSnapshot


def render(
    snapshots: Sequence[RepoSnapshot],
    findings: Iterable[Finding],
    *,
    verbose: bool = False,
) -> str:
    findings_list = list(findings)
    if not verbose:
        findings_list = [f for f in findings_list if f.severity != "info"]

    lines: List[str] = []
    meta_version = snapshots[0].meta_version if snapshots else None
    lines.append("# Drift report")
    lines.append("")
    if meta_version is not None:
        lines.append(f"Meta-repo version: {meta_version}")
    total_files = sum(len(s.files) for s in snapshots)
    lines.append(f"Checked: {len(snapshots)} repos, {total_files} files")
    lines.append("")

    by_repo: dict[str, list[Finding]] = {s.slug: [] for s in snapshots}
    for f in findings_list:
        by_repo.setdefault(f.repo, []).append(f)

    for snap in snapshots:
        repo_findings = by_repo.get(snap.slug, [])
        errs = sum(1 for f in repo_findings if f.severity == "error")
        warns = sum(1 for f in repo_findings if f.severity == "warn")
        lines.append(f"## {snap.slug} ({errs} errors, {warns} warnings)")
        if not repo_findings:
            lines.append("Clean.")
            lines.append("")
            continue
        lines.append("| File | Check | Severity | Message |")
        lines.append("| ---- | ----- | -------- | ------- |")
        for f in repo_findings:
            file_label = str(f.file).replace("\\", "/") if f.file else "-"
            msg = f.message.replace("|", "\\|")
            lines.append(f"| {file_label} | {f.check} | {f.severity} | {msg} |")
        lines.append("")

    total_err = sum(1 for f in findings_list if f.severity == "error")
    total_warn = sum(1 for f in findings_list if f.severity == "warn")
    total_info = sum(1 for f in findings_list if f.severity == "info")
    lines.append(
        f"Summary: {total_err} errors, {total_warn} warnings, "
        f"{total_info} infos across {len(snapshots)} repos."
    )
    return "\n".join(lines) + "\n"
