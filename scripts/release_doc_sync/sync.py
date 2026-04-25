"""Release-doc-sync (Phase 2 Session D-2 of DTD#5).

This script is invoked by the ``release-doc-sync`` composite action from each
tool repo's ``release.yml`` workflow, between the ``plugin.json`` version
bump and the release commit. It edits, in-place, the three doc files that
contain version references the release pipeline does not otherwise
maintain:

* ``CHANGELOG.md``  -- prepends a stub ``## [X.Y.Z] - YYYY-MM-DD`` section
* ``CLAUDE.md``     -- updates the canonical ``**Version:**`` line and any
                       ``vOLD`` / ``(vOLD)`` mentions
* ``ROADMAP.md``    -- updates only the ``**Current:** vX.Y.Z`` line; the
                       roadmap table and ``(current)`` markers are left
                       alone because per ``standards/versioning.md`` patch
                       releases do not get themed roadmap rows

Design contract:

* Every edit is idempotent. Running the script on already-aligned docs is a
  no-op and leaves files byte-identical.
* Every edit is local: a missing file logs a warning and skips, never
  fails. This keeps tool repos that lack one of the three docs from
  blocking their releases.
* The script never touches ``plugin.json`` or ``README.md`` -- those are
  owned by the existing ``release.yml`` step.
* The script never touches ``<!-- standards-version: ... -->`` markers --
  those belong to the drift-checker (DTD#1).

Exit codes (matches drift-check@v1.7 conventions adapted for "no findings"
semantics):

* ``0`` -- ran successfully, no files changed (already aligned, or all absent)
* ``1`` -- ran successfully, at least one file changed
* ``2`` -- tool error (bad args, unreadable files, malformed inputs)

The ``rc=1`` "made a change" signal is informational; the calling action
treats both ``rc=0`` and ``rc=1`` as success and only fails on ``rc>=2``.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class FileResult:
    """Outcome for a single doc file."""

    path: Path
    action: str  # one of: inserted, updated, idempotent, missing
    detail: str = ""

    @property
    def changed(self) -> bool:
        return self.action in {"inserted", "updated"}


@dataclass
class SyncResult:
    """Aggregate outcome for a sync_repo() invocation."""

    changelog: FileResult
    claude: FileResult
    roadmap: FileResult
    files_changed: List[Path] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return any(r.changed for r in (self.changelog, self.claude, self.roadmap))


# ---------------------------------------------------------------------------
# CHANGELOG.md
# ---------------------------------------------------------------------------


_CHANGELOG_VERSION_RE = re.compile(r"^##\s*\[(\d+\.\d+\.\d+)\]", re.MULTILINE)
_CHANGELOG_FIRST_RELEASE_RE = re.compile(r"^##\s*\[", re.MULTILINE)


def sync_changelog(
    path: Path,
    *,
    plugin_version: str,
    repository: str,
    release_date: str,
) -> FileResult:
    """Insert a stub release section for ``plugin_version`` if absent.

    The stub is intentionally minimal -- a header line plus a one-line
    pointer to the GitHub release notes. Curated narrative belongs in
    GitHub Releases (which ``release.yml`` already generates with
    ``--generate-notes`` / release-drafter).

    Stub shape (matches Phase 1 Q1 decision)::

        ## [X.Y.Z] - YYYY-MM-DD

        See [release notes](https://github.com/<repo>/releases/tag/vX.Y.Z) for details.

    Idempotency: if ``## [X.Y.Z]`` already appears anywhere in the file,
    the function returns ``idempotent`` without touching the file.

    Insertion point: immediately before the first existing ``## [`` release
    section. If no release sections exist yet, append after the file's
    existing content (one trailing blank line is normalized).

    Footer link refs (``[X.Y.Z]: <url>``) are intentionally NOT auto-added.
    Steam's Keep-a-Changelog format uses them, but maintaining the link
    table requires either upserting alphabetical-by-version order or
    relying on Markdown allowing duplicates -- both fragile. The Steam
    test only requires ``[X.Y.Z]`` substring, which the header alone
    satisfies.
    """
    if not path.is_file():
        return FileResult(path=path, action="missing")

    text = path.read_text(encoding="utf-8")

    if f"[{plugin_version}]" in text:
        return FileResult(
            path=path,
            action="idempotent",
            detail=f"version {plugin_version} already present",
        )

    release_url = f"https://github.com/{repository}/releases/tag/v{plugin_version}"
    stub = (
        f"## [{plugin_version}] - {release_date}\n"
        f"\n"
        f"See [release notes]({release_url}) for details.\n"
        f"\n"
    )

    insertion_match = _CHANGELOG_FIRST_RELEASE_RE.search(text)
    if insertion_match is not None:
        insertion_idx = insertion_match.start()
        new_text = text[:insertion_idx] + stub + text[insertion_idx:]
    else:
        if not text.endswith("\n"):
            text = text + "\n"
        if not text.endswith("\n\n"):
            text = text + "\n"
        new_text = text + stub

    path.write_text(new_text, encoding="utf-8")
    return FileResult(
        path=path,
        action="inserted",
        detail=f"prepended ## [{plugin_version}] section",
    )


# ---------------------------------------------------------------------------
# CLAUDE.md
# ---------------------------------------------------------------------------


# Match `**Version:** [v]X.Y.Z` (Docker convention) but capture only the
# value so we can rewrite it. The colon-space is required to avoid matching
# bold prose like `**Version:**: 1.0.0` or unrelated headings.
_CLAUDE_VERSION_LINE_RE = re.compile(r"(\*\*Version:\*\*\s+)v?(\d+\.\d+\.\d+)")


def sync_claude(
    path: Path,
    *,
    plugin_version: str,
    previous_version: str,
) -> FileResult:
    """Update CLAUDE.md version references.

    Three patterns are handled, all idempotent:

    1. ``**Version:** X.Y.Z`` line -- replaced with the new version. The
       ``v`` prefix is preserved if it was originally present (so Docker's
       ``**Version:** 1.0.0`` stays bare and a hypothetical
       ``**Version:** v1.0.0`` keeps its prefix).
    2. ``vOLD`` substring -- replaced with ``vNEW``. Scoped to the
       previous version so unrelated version mentions (e.g., a roadmap
       reference to ``v0.1.0`` in CLAUDE.md prose) are preserved.
    3. The ``vOLD`` rewrite naturally covers ``(vOLD)`` Steam-style
       parentheticals since ``v`` is part of the match.

    Explicit non-targets (regression guards):

    * ``<!-- standards-version: A.B.C -->`` markers belong to the drift
      checker (DTD#1). They are not version-prefixed with ``v`` so the
      ``vOLD`` regex cannot match them, and they do not contain
      ``**Version:**``. Defended by ``test_claude_does_not_touch_standards_version``.
    * Bare ``OLD`` substrings (e.g., the literal string ``1.0.0``) are
      NOT replaced. Doing so would mangle CHANGELOG-style references
      buried inside CLAUDE.md or quoted command output.
    """
    if not path.is_file():
        return FileResult(path=path, action="missing")

    text = path.read_text(encoding="utf-8")
    original = text

    # Pattern 1: **Version:** line. Preserves v-prefix presence.
    def _rewrite_version_line(match: re.Match) -> str:
        prefix = match.group(1)
        captured = match.group(2)
        had_v = match.group(0)[len(prefix)] == "v"
        new_value = f"v{plugin_version}" if had_v else plugin_version
        if captured == plugin_version:
            return match.group(0)
        return f"{prefix}{new_value}"

    text = _CLAUDE_VERSION_LINE_RE.sub(_rewrite_version_line, text)

    # Pattern 2 & 3: vOLD -> vNEW. Use a negative lookahead instead of \b
    # because \b matches between '0' and '-', which would incorrectly rewrite
    # 'v1.0.0-beta' when previous='1.0.0'. The lookahead refuses any further
    # version-character follower (digit, dot, dash, letter), so 'v1.0.0' only
    # matches when it stands alone as a complete version token.
    if previous_version != plugin_version:
        v_old_re = re.compile(rf"v{re.escape(previous_version)}(?![\w.\-])")
        text = v_old_re.sub(f"v{plugin_version}", text)

    if text == original:
        return FileResult(
            path=path,
            action="idempotent",
            detail="no version patterns matched or already aligned",
        )

    path.write_text(text, encoding="utf-8")
    return FileResult(
        path=path,
        action="updated",
        detail=f"rewrote version references {previous_version} -> {plugin_version}",
    )


# ---------------------------------------------------------------------------
# ROADMAP.md
# ---------------------------------------------------------------------------


# Capture `**Current:** vX.Y.Z`. Group 1 = leading prefix (preserved),
# group 2 = the v-prefixed version. Tolerates `v` being absent, but always
# emits the canonical `**Current:** vNEW` form (matches Steam's
# test_current_line_version regex).
_ROADMAP_CURRENT_LINE_RE = re.compile(r"(\*\*Current:\*\*\s+)v?(\d+\.\d+\.\d+)")


def sync_roadmap(path: Path, *, plugin_version: str) -> FileResult:
    """Update ``**Current:** vX.Y.Z`` line in ROADMAP.md.

    Explicit non-targets:

    * The roadmap table (``| vX.Y.Z | Theme | ... |``). Patch releases do
      not get themed roadmap rows -- see ``standards/versioning.md`` and
      DTD#5 for the policy. Auto-bumping a patch row would invent a fake
      theme, so the action leaves the table alone.
    * ``(current)`` markers anywhere in the file. The marker tracks the
      currently-released **theme**, which is a human-curated minor/major
      decision. The corresponding doc-consistency tests in Docker and
      Steam are being relaxed in Phase 2d.

    Idempotency: if no ``**Current:**`` line exists, returns
    ``idempotent`` (Docker-style ROADMAPs use ``**vX.Y.Z** - ...``
    without a ``**Current:**`` label). If the line already names
    ``plugin_version``, also returns ``idempotent``.
    """
    if not path.is_file():
        return FileResult(path=path, action="missing")

    text = path.read_text(encoding="utf-8")
    match = _ROADMAP_CURRENT_LINE_RE.search(text)

    if match is None:
        return FileResult(
            path=path,
            action="idempotent",
            detail="no **Current:** line present",
        )

    if match.group(2) == plugin_version:
        return FileResult(
            path=path,
            action="idempotent",
            detail=f"**Current:** already at v{plugin_version}",
        )

    new_text = (
        text[: match.start()]
        + f"{match.group(1)}v{plugin_version}"
        + text[match.end() :]
    )
    path.write_text(new_text, encoding="utf-8")
    return FileResult(
        path=path,
        action="updated",
        detail=f"**Current:** {match.group(2)} -> {plugin_version}",
    )


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def sync_repo(
    repo_path: Path,
    *,
    plugin_version: str,
    previous_version: str,
    repository: str,
    release_date: str,
) -> SyncResult:
    """Run all three syncs and aggregate results.

    Files are looked up at ``repo_path/CHANGELOG.md``, ``repo_path/CLAUDE.md``,
    ``repo_path/ROADMAP.md``. Tool repos that nest these files under a
    different layout (none in the current ecosystem) would need a different
    integration; the simple flat-root layout is the standard.
    """
    changelog = sync_changelog(
        repo_path / "CHANGELOG.md",
        plugin_version=plugin_version,
        repository=repository,
        release_date=release_date,
    )
    claude = sync_claude(
        repo_path / "CLAUDE.md",
        plugin_version=plugin_version,
        previous_version=previous_version,
    )
    roadmap = sync_roadmap(
        repo_path / "ROADMAP.md",
        plugin_version=plugin_version,
    )

    files_changed = [r.path for r in (changelog, claude, roadmap) if r.changed]
    return SyncResult(
        changelog=changelog,
        claude=claude,
        roadmap=roadmap,
        files_changed=files_changed,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="release-doc-sync",
        description=(
            "Align CHANGELOG.md, CLAUDE.md, and ROADMAP.md with the new "
            "plugin.json version after an auto-release."
        ),
    )
    p.add_argument(
        "--repo-path",
        required=True,
        type=Path,
        help="Path to the tool-repo working tree (where CHANGELOG.md etc. live).",
    )
    p.add_argument(
        "--plugin-version",
        required=True,
        help="New plugin version, semver only (no 'v' prefix). Example: 1.2.1",
    )
    p.add_argument(
        "--previous-version",
        required=True,
        help="Previous plugin version, semver only. Example: 1.2.0",
    )
    p.add_argument(
        "--repository",
        required=True,
        help="owner/repo for constructing the GitHub release URL in CHANGELOG.",
    )
    p.add_argument(
        "--date",
        default=None,
        help="YYYY-MM-DD release date for CHANGELOG header. Defaults to today UTC.",
    )
    p.add_argument(
        "--github-output",
        action="store_true",
        help="Write outputs to $GITHUB_OUTPUT in addition to stdout.",
    )
    return p.parse_args(argv)


def _validate_args(ns: argparse.Namespace) -> None:
    if not _SEMVER_RE.match(ns.plugin_version):
        raise SystemExit(
            f"::error::--plugin-version must be MAJOR.MINOR.PATCH; got {ns.plugin_version!r}"
        )
    if not _SEMVER_RE.match(ns.previous_version):
        raise SystemExit(
            f"::error::--previous-version must be MAJOR.MINOR.PATCH; got {ns.previous_version!r}"
        )
    if "/" not in ns.repository:
        raise SystemExit(
            f"::error::--repository must be owner/name; got {ns.repository!r}"
        )
    if not ns.repo_path.is_dir():
        raise SystemExit(
            f"::error::--repo-path does not exist or is not a directory: {ns.repo_path}"
        )


def _print_result(result: SyncResult) -> None:
    for fr in (result.changelog, result.claude, result.roadmap):
        rel = fr.path.name
        line = f"{fr.action:<11} {rel}"
        if fr.detail:
            line += f"  ({fr.detail})"
        print(line)
    print()
    if result.changed:
        names = " ".join(p.name for p in result.files_changed)
        print(f"changed: true ({names})")
    else:
        print("changed: false")


def _emit_github_output(result: SyncResult) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(f"changed={'true' if result.changed else 'false'}\n")
        f.write(
            "files-changed=" + " ".join(p.name for p in result.files_changed) + "\n"
        )
        f.write(f"changelog-action={result.changelog.action}\n")
        f.write(f"claude-action={result.claude.action}\n")
        f.write(f"roadmap-action={result.roadmap.action}\n")


def main(argv: Optional[List[str]] = None) -> int:
    ns = _parse_args(argv)
    _validate_args(ns)

    release_date = ns.date or _dt.datetime.now(_dt.timezone.utc).date().isoformat()

    try:
        result = sync_repo(
            ns.repo_path,
            plugin_version=ns.plugin_version,
            previous_version=ns.previous_version,
            repository=ns.repository,
            release_date=release_date,
        )
    except OSError as exc:
        print(f"::error::I/O failure during sync: {exc}", file=sys.stderr)
        return 2

    _print_result(result)
    if ns.github_output:
        _emit_github_output(result)

    return 1 if result.changed else 0


if __name__ == "__main__":
    sys.exit(main())
