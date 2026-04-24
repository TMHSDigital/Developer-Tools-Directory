"""The live version-signal check (Decision 1 + Q7 adjustment).

Tier -> Finding severity mapping (this is the only place this mapping
lives; keep it here, not in ``semver.py``):

  exact_match          -> no finding
  patch_differs        -> info
  major_minor_differs  -> error
  tool_newer           -> warn   (per Q7 adjustment)
  malformed (parsed)   -> error  (signal present but did not parse)

Additional branches handled by this check (not tiers from semver):

  missing signal       -> error
  drift-ignore pragma  -> info (skipped silently in non-verbose mode;
                          callers filter on severity)
  config skip_checks   -> no findings at all for this check
"""
from __future__ import annotations

from typing import Iterable, List

from ..semver import compare_policy
from ..signals import _classify_by_name
from ..types import Finding, RepoSnapshot, Severity


NAME = "version-signal"


class VersionSignalCheck:
    """Implements the ``Check`` protocol from ``types.py``."""

    name: str = NAME

    def run(self, snapshot: RepoSnapshot) -> Iterable[Finding]:
        if NAME in snapshot.config.skip_checks:
            return ()

        out: List[Finding] = []
        for rel_path, file in snapshot.files.items():
            fmt = _classify_by_name(rel_path)
            if fmt is None:
                continue  # not a checked file

            pragma = next(
                (p for p in file.pragmas if p.check_name == NAME), None
            )
            if pragma is not None:
                out.append(
                    Finding(
                        repo=snapshot.slug,
                        file=rel_path,
                        check=NAME,
                        severity="info",
                        message=(
                            f"skipped by drift-ignore pragma"
                            + (f" (reason: {pragma.reason})" if pragma.reason else "")
                        ),
                        suggested_fix=None,
                    )
                )
                continue

            signal = file.signal
            if signal is None:
                out.append(
                    Finding(
                        repo=snapshot.slug,
                        file=rel_path,
                        check=NAME,
                        severity="error",
                        message=(
                            f"missing standards-version signal; expected "
                            f"{fmt} at the canonical position"
                        ),
                        suggested_fix=_suggested_fix(fmt, snapshot.meta_version.raw),
                    )
                )
                continue

            if signal.malformed or signal.version is None:
                out.append(
                    Finding(
                        repo=snapshot.slug,
                        file=rel_path,
                        check=NAME,
                        severity="error",
                        message=(
                            f"malformed standards-version signal "
                            f"{signal.raw_value!r} at line {signal.line}"
                        ),
                        suggested_fix=_suggested_fix(fmt, snapshot.meta_version.raw),
                    )
                )
                continue

            tier = compare_policy(signal.version, snapshot.meta_version)
            severity = _tier_to_severity(tier)
            if severity is None:
                continue  # exact_match, silent
            out.append(
                Finding(
                    repo=snapshot.slug,
                    file=rel_path,
                    check=NAME,
                    severity=severity,
                    message=_tier_message(tier, signal.version, snapshot.meta_version),
                    suggested_fix=_suggested_fix(fmt, snapshot.meta_version.raw),
                )
            )
        return out


def _tier_to_severity(tier: str):
    """Return the Finding severity for a semver tier. None means silent."""
    mapping: dict[str, Severity] = {
        "patch_differs": "info",
        "major_minor_differs": "error",
        "tool_newer": "warn",
        "malformed": "error",
    }
    return mapping.get(tier)


def _tier_message(tier: str, tool_v, meta_v) -> str:
    if tier == "patch_differs":
        return f"patch-level drift: tool={tool_v}, meta={meta_v}"
    if tier == "major_minor_differs":
        return f"MAJOR.MINOR drift: tool={tool_v}, meta={meta_v}"
    if tier == "tool_newer":
        return f"tool signal ahead of meta: tool={tool_v}, meta={meta_v}"
    if tier == "malformed":
        return f"malformed tool version (cannot compare to meta={meta_v})"
    return f"tier={tier}"


def _suggested_fix(fmt: str, target_version: str) -> str:
    script = (
        "add_frontmatter.py"
        if fmt == "yaml-frontmatter"
        else "add_comment_marker.py"
    )
    return f"run {script} <file> {target_version}"
