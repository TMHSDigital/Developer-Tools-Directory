"""Unit tests for ``scripts/release_doc_sync/sync.py``.

Coverage targets:

* CHANGELOG.md insertion at the right position (before first ``## [`` section)
* CHANGELOG.md idempotency (``## [X.Y.Z]`` already present)
* CHANGELOG.md with no existing release sections (append at end)
* CLAUDE.md updates Docker-style ``**Version:** X.Y.Z`` line, preserves
  v-prefix presence
* CLAUDE.md updates Steam-style ``vOLD`` and ``(vOLD)`` mentions in prose
* CLAUDE.md leaves ``<!-- standards-version: ... -->`` markers alone (DTD#1
  ownership boundary)
* CLAUDE.md does not mangle bare ``OLD`` substrings (regression guard)
* ROADMAP.md updates ``**Current:** vX.Y.Z`` line, preserves table content
* ROADMAP.md leaves Docker-style files (no ``**Current:**`` label) alone
* ROADMAP.md does not move or rewrite ``(current)`` markers
* End-to-end: running sync_repo twice is a no-op the second time
* Missing files do not crash, return ``missing`` action
* CLI: exit code 0 when nothing changed, 1 when something changed, 2 on
  bad args
* Composite action shape: action.yml parses, declares the documented
  inputs/outputs, follows the drift-check pattern
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from tests.conftest import REPO_ROOT  # noqa: E402

from scripts.release_doc_sync.sync import (  # noqa: E402
    SyncResult,
    main,
    sync_changelog,
    sync_claude,
    sync_repo,
    sync_roadmap,
)


# ---------------------------------------------------------------------------
# Fixtures: real-world doc shapes from Docker and Steam plugin repos
# ---------------------------------------------------------------------------


DOCKER_CHANGELOG = """\
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-29

### Changed

#### MCP Server - Enhanced Error Messages
- errorResponse now includes error type prefix.

## [0.12.0] - 2026-03-29

### Added

- niche tools.
"""


STEAM_CHANGELOG = """\
# Changelog

All notable changes to Steam Developer Tools will be documented in this file.

## [1.0.0] - 2026-03-29

### Added

- 5 new MCP tools.
"""


CHANGELOG_NO_SECTIONS = """\
# Changelog

All notable changes will go here once we cut our first release.
"""


DOCKER_CLAUDE = """\
<!-- standards-version: 1.7.0 -->

# CLAUDE.md

Project documentation for Claude Code.

**Version:** 1.0.0
**License:** CC-BY-NC-ND-4.0
**Author:** TMHSDigital
"""


STEAM_CLAUDE = """\
<!-- standards-version: 1.7.0 -->

# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Steam Developer Tools is a Cursor IDE plugin (v1.0.0) that integrates Steam APIs.

The current release is v1.0.0 "Stable" - the production release.
"""


CLAUDE_NO_VERSION_AT_ALL = """\
# CLAUDE.md

Some text without a version reference at all.
"""


DOCKER_ROADMAP = """\
# Roadmap

> Docker Developer Tools plugin roadmap.

## Current Status

**v0.12.0** - Niche, Scout, and Extras release.

## Release Plan

| Version | Theme | Status |
| --- | --- | --- |
| v0.12.0 | Niche, Scout, and Extras | Released |
| v1.0.0 | Stable | (current) |
"""


STEAM_ROADMAP = """\
# Roadmap

Themed release plan toward v1.0.0.

**Current:** v1.0.0 - 30 skills, 9 rules.

**Status:** v1.0.0 "Stable" released.

| Version | Theme | Total Skills |
| --- | --- | --- |
| v0.1.0 | - | 14 |
| v1.0.0 (current) | Stable | 30 |
"""


# ---------------------------------------------------------------------------
# CHANGELOG tests
# ---------------------------------------------------------------------------


class TestChangelog:
    def test_inserts_stub_before_first_release(self, tmp_path: Path):
        path = tmp_path / "CHANGELOG.md"
        path.write_text(DOCKER_CHANGELOG, encoding="utf-8")

        result = sync_changelog(
            path,
            plugin_version="1.2.1",
            repository="TMHSDigital/Docker-Developer-Tools",
            release_date="2026-04-25",
        )

        assert result.action == "inserted"
        assert result.changed is True
        text = path.read_text(encoding="utf-8")

        # New stub appears
        assert "## [1.2.1] - 2026-04-25" in text
        assert (
            "See [release notes]"
            "(https://github.com/TMHSDigital/Docker-Developer-Tools/releases/tag/v1.2.1)"
            " for details." in text
        )

        # Inserted before the prior latest release
        idx_new = text.index("## [1.2.1]")
        idx_old = text.index("## [1.0.0]")
        assert idx_new < idx_old

        # Pre-existing entries preserved verbatim
        assert "errorResponse now includes error type prefix." in text
        assert "## [0.12.0] - 2026-03-29" in text

    def test_steam_bracketed_substring_satisfied(self, tmp_path: Path):
        path = tmp_path / "CHANGELOG.md"
        path.write_text(STEAM_CHANGELOG, encoding="utf-8")

        sync_changelog(
            path,
            plugin_version="1.2.1",
            repository="TMHSDigital/Steam-Cursor-Plugin",
            release_date="2026-04-25",
        )

        text = path.read_text(encoding="utf-8")
        assert "[1.2.1]" in text

    def test_idempotent_when_version_already_present(self, tmp_path: Path):
        path = tmp_path / "CHANGELOG.md"
        path.write_text(DOCKER_CHANGELOG, encoding="utf-8")

        first = sync_changelog(
            path,
            plugin_version="1.0.0",
            repository="TMHSDigital/Docker-Developer-Tools",
            release_date="2026-04-25",
        )

        assert first.action == "idempotent"
        assert path.read_text(encoding="utf-8") == DOCKER_CHANGELOG

    def test_appends_when_no_release_sections_exist(self, tmp_path: Path):
        path = tmp_path / "CHANGELOG.md"
        path.write_text(CHANGELOG_NO_SECTIONS, encoding="utf-8")

        result = sync_changelog(
            path,
            plugin_version="0.1.0",
            repository="TMHSDigital/New-Plugin",
            release_date="2026-04-25",
        )

        assert result.action == "inserted"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("# Changelog")
        assert "## [0.1.0] - 2026-04-25" in text
        # The original preamble survives.
        assert "Some text without a version reference" not in text  # never was there
        assert "All notable changes will go here" in text

    def test_missing_file_returns_missing(self, tmp_path: Path):
        path = tmp_path / "CHANGELOG.md"  # not created
        result = sync_changelog(
            path,
            plugin_version="1.2.1",
            repository="TMHSDigital/Docker-Developer-Tools",
            release_date="2026-04-25",
        )
        assert result.action == "missing"
        assert result.changed is False
        assert not path.exists()


# ---------------------------------------------------------------------------
# CLAUDE tests
# ---------------------------------------------------------------------------


class TestClaude:
    def test_updates_docker_version_line_preserves_no_v_prefix(self, tmp_path: Path):
        path = tmp_path / "CLAUDE.md"
        path.write_text(DOCKER_CLAUDE, encoding="utf-8")

        result = sync_claude(
            path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
        )

        assert result.action == "updated"
        text = path.read_text(encoding="utf-8")
        assert "**Version:** 1.2.1" in text
        assert "**Version:** 1.0.0" not in text

    def test_updates_steam_prose_v_prefix_form(self, tmp_path: Path):
        path = tmp_path / "CLAUDE.md"
        path.write_text(STEAM_CLAUDE, encoding="utf-8")

        result = sync_claude(
            path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
        )

        assert result.action == "updated"
        text = path.read_text(encoding="utf-8")
        assert "(v1.2.1)" in text
        assert "(v1.0.0)" not in text
        # Steam test asserts: f"v{version}" in claude_text or version in claude_text
        assert "v1.2.1" in text

    def test_does_not_touch_standards_version_marker(self, tmp_path: Path):
        """Regression guard: the HTML comment marker is owned by the drift
        checker (DTD#1) and uses a different concept (ecosystem standards
        version, not plugin version). It must never be rewritten by this
        action."""
        path = tmp_path / "CLAUDE.md"
        path.write_text(DOCKER_CLAUDE, encoding="utf-8")

        sync_claude(
            path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
        )

        text = path.read_text(encoding="utf-8")
        assert "<!-- standards-version: 1.7.0 -->" in text

    def test_does_not_mangle_bare_old_substring(self, tmp_path: Path):
        """If CLAUDE.md happens to contain a bare ``1.0.0`` substring inside
        a code block or quoted output, it must NOT be rewritten. Only
        ``vOLD`` and ``**Version:** OLD`` patterns are in scope."""
        path = tmp_path / "CLAUDE.md"
        content = (
            "# CLAUDE.md\n\n"
            "**Version:** 1.0.0\n\n"
            "Quoted from an upstream changelog: 'Released 1.0.0 in March 2024.'\n"
        )
        path.write_text(content, encoding="utf-8")

        sync_claude(
            path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
        )

        text = path.read_text(encoding="utf-8")
        assert "**Version:** 1.2.1" in text
        # Bare '1.0.0' in the prose quote is preserved.
        assert "Released 1.0.0 in March 2024" in text

    def test_idempotent_when_already_aligned(self, tmp_path: Path):
        path = tmp_path / "CLAUDE.md"
        already_aligned = DOCKER_CLAUDE.replace("**Version:** 1.0.0", "**Version:** 1.2.1")
        path.write_text(already_aligned, encoding="utf-8")

        result = sync_claude(
            path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
        )

        assert result.action == "idempotent"
        assert path.read_text(encoding="utf-8") == already_aligned

    def test_no_pattern_present_is_idempotent(self, tmp_path: Path):
        path = tmp_path / "CLAUDE.md"
        path.write_text(CLAUDE_NO_VERSION_AT_ALL, encoding="utf-8")

        result = sync_claude(
            path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
        )

        assert result.action == "idempotent"
        assert path.read_text(encoding="utf-8") == CLAUDE_NO_VERSION_AT_ALL

    def test_missing_file_returns_missing(self, tmp_path: Path):
        result = sync_claude(
            tmp_path / "CLAUDE.md",
            plugin_version="1.2.1",
            previous_version="1.0.0",
        )
        assert result.action == "missing"

    def test_word_boundary_protects_longer_version_strings(self, tmp_path: Path):
        """``v1.0.0`` must not match inside ``v1.0.0-beta`` or ``v1.0.01``.
        Defends the \\b anchor in the rewrite regex."""
        path = tmp_path / "CLAUDE.md"
        content = (
            "# CLAUDE.md\n\n"
            "**Version:** 1.0.0\n\n"
            "Forward-references: v1.0.0-beta exists in the dev branch.\n"
        )
        path.write_text(content, encoding="utf-8")

        sync_claude(
            path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
        )

        text = path.read_text(encoding="utf-8")
        assert "**Version:** 1.2.1" in text
        # v1.0.0-beta is left alone because \b stops the match before the dash.
        assert "v1.0.0-beta" in text


# ---------------------------------------------------------------------------
# ROADMAP tests
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_updates_steam_current_line(self, tmp_path: Path):
        path = tmp_path / "ROADMAP.md"
        path.write_text(STEAM_ROADMAP, encoding="utf-8")

        result = sync_roadmap(path, plugin_version="1.2.1")

        assert result.action == "updated"
        text = path.read_text(encoding="utf-8")
        assert "**Current:** v1.2.1" in text
        assert "**Current:** v1.0.0" not in text

    def test_table_and_current_marker_untouched(self, tmp_path: Path):
        path = tmp_path / "ROADMAP.md"
        path.write_text(STEAM_ROADMAP, encoding="utf-8")

        sync_roadmap(path, plugin_version="1.2.1")

        text = path.read_text(encoding="utf-8")
        # Table row is preserved verbatim, including the (current) marker
        # on v1.0.0 -- the action does NOT move the marker.
        assert "| v1.0.0 (current) | Stable | 30 |" in text
        assert "| v0.1.0 | - | 14 |" in text

    def test_docker_style_no_current_label_is_idempotent(self, tmp_path: Path):
        path = tmp_path / "ROADMAP.md"
        path.write_text(DOCKER_ROADMAP, encoding="utf-8")

        result = sync_roadmap(path, plugin_version="1.2.1")

        assert result.action == "idempotent"
        assert path.read_text(encoding="utf-8") == DOCKER_ROADMAP

    def test_idempotent_when_already_aligned(self, tmp_path: Path):
        aligned = STEAM_ROADMAP.replace("**Current:** v1.0.0", "**Current:** v1.2.1")
        path = tmp_path / "ROADMAP.md"
        path.write_text(aligned, encoding="utf-8")

        result = sync_roadmap(path, plugin_version="1.2.1")

        assert result.action == "idempotent"
        assert path.read_text(encoding="utf-8") == aligned

    def test_missing_file_returns_missing(self, tmp_path: Path):
        result = sync_roadmap(tmp_path / "ROADMAP.md", plugin_version="1.2.1")
        assert result.action == "missing"


# ---------------------------------------------------------------------------
# End-to-end: sync_repo
# ---------------------------------------------------------------------------


class TestSyncRepo:
    def test_full_steam_run(self, tmp_path: Path):
        (tmp_path / "CHANGELOG.md").write_text(STEAM_CHANGELOG, encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text(STEAM_CLAUDE, encoding="utf-8")
        (tmp_path / "ROADMAP.md").write_text(STEAM_ROADMAP, encoding="utf-8")

        result = sync_repo(
            tmp_path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
            repository="TMHSDigital/Steam-Cursor-Plugin",
            release_date="2026-04-25",
        )

        assert result.changed is True
        assert result.changelog.action == "inserted"
        assert result.claude.action == "updated"
        assert result.roadmap.action == "updated"
        assert len(result.files_changed) == 3

    def test_full_docker_run(self, tmp_path: Path):
        (tmp_path / "CHANGELOG.md").write_text(DOCKER_CHANGELOG, encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text(DOCKER_CLAUDE, encoding="utf-8")
        (tmp_path / "ROADMAP.md").write_text(DOCKER_ROADMAP, encoding="utf-8")

        result = sync_repo(
            tmp_path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
            repository="TMHSDigital/Docker-Developer-Tools",
            release_date="2026-04-25",
        )

        # Docker has no **Current:** label so ROADMAP is idempotent.
        assert result.changelog.action == "inserted"
        assert result.claude.action == "updated"
        assert result.roadmap.action == "idempotent"
        assert result.changed is True

    def test_second_run_is_pure_noop(self, tmp_path: Path):
        """Idempotency end-to-end. Run sync_repo twice and assert that the
        second invocation makes zero file edits."""
        (tmp_path / "CHANGELOG.md").write_text(STEAM_CHANGELOG, encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text(STEAM_CLAUDE, encoding="utf-8")
        (tmp_path / "ROADMAP.md").write_text(STEAM_ROADMAP, encoding="utf-8")

        sync_repo(
            tmp_path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
            repository="TMHSDigital/Steam-Cursor-Plugin",
            release_date="2026-04-25",
        )

        snapshot = {
            p.name: p.read_text(encoding="utf-8")
            for p in tmp_path.iterdir()
        }

        second = sync_repo(
            tmp_path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
            repository="TMHSDigital/Steam-Cursor-Plugin",
            release_date="2026-04-25",
        )

        assert second.changed is False
        assert second.changelog.action == "idempotent"
        assert second.claude.action == "idempotent"
        assert second.roadmap.action == "idempotent"

        for p in tmp_path.iterdir():
            assert p.read_text(encoding="utf-8") == snapshot[p.name], (
                f"second run mutated {p.name}"
            )

    def test_all_three_files_missing_does_not_crash(self, tmp_path: Path):
        result = sync_repo(
            tmp_path,
            plugin_version="1.2.1",
            previous_version="1.0.0",
            repository="TMHSDigital/Empty",
            release_date="2026-04-25",
        )
        assert result.changed is False
        assert result.changelog.action == "missing"
        assert result.claude.action == "missing"
        assert result.roadmap.action == "missing"


# ---------------------------------------------------------------------------
# CLI exit codes & output
# ---------------------------------------------------------------------------


class TestCliExitCodes:
    def _run(self, repo: Path, *extra: str) -> int:
        """Run the script as a subprocess so we exercise the real entry."""
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "release_doc_sync" / "sync.py"),
            "--repo-path", str(repo),
            "--plugin-version", "1.2.1",
            "--previous-version", "1.0.0",
            "--repository", "TMHSDigital/Docker-Developer-Tools",
            "--date", "2026-04-25",
            *extra,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode

    def test_rc_0_when_nothing_changed(self, tmp_path: Path):
        # No files at all => everything missing => no changes.
        rc = self._run(tmp_path)
        assert rc == 0

    def test_rc_1_when_something_changed(self, tmp_path: Path):
        (tmp_path / "CLAUDE.md").write_text(DOCKER_CLAUDE, encoding="utf-8")
        rc = self._run(tmp_path)
        assert rc == 1

    def test_rc_0_on_second_run(self, tmp_path: Path):
        (tmp_path / "CLAUDE.md").write_text(DOCKER_CLAUDE, encoding="utf-8")
        first = self._run(tmp_path)
        second = self._run(tmp_path)
        assert first == 1
        assert second == 0

    def test_rejects_garbage_plugin_version(self, tmp_path: Path):
        with pytest.raises(SystemExit) as exc:
            main([
                "--repo-path", str(tmp_path),
                "--plugin-version", "v1.2.1",  # 'v' prefix forbidden
                "--previous-version", "1.0.0",
                "--repository", "TMHSDigital/X",
            ])
        assert "must be MAJOR.MINOR.PATCH" in str(exc.value)

    def test_rejects_bad_repository(self, tmp_path: Path):
        with pytest.raises(SystemExit) as exc:
            main([
                "--repo-path", str(tmp_path),
                "--plugin-version", "1.2.1",
                "--previous-version", "1.0.0",
                "--repository", "no-slash",
            ])
        assert "owner/name" in str(exc.value)

    def test_github_output_emitted(self, tmp_path: Path, monkeypatch):
        (tmp_path / "CLAUDE.md").write_text(DOCKER_CLAUDE, encoding="utf-8")
        out_file = tmp_path / "github_output"
        monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))

        rc = main([
            "--repo-path", str(tmp_path),
            "--plugin-version", "1.2.1",
            "--previous-version", "1.0.0",
            "--repository", "TMHSDigital/Docker-Developer-Tools",
            "--date", "2026-04-25",
            "--github-output",
        ])

        assert rc == 1
        body = out_file.read_text(encoding="utf-8")
        assert "changed=true" in body
        assert "files-changed=CLAUDE.md" in body
        assert "claude-action=updated" in body
        assert "changelog-action=missing" in body
        assert "roadmap-action=missing" in body


# ---------------------------------------------------------------------------
# Composite action shape
# ---------------------------------------------------------------------------


ACTION_YML = REPO_ROOT / ".github" / "actions" / "release-doc-sync" / "action.yml"


@pytest.fixture(scope="module")
def action_doc():
    return yaml.safe_load(ACTION_YML.read_text(encoding="utf-8"))


class TestCompositeAction:
    def test_action_yaml_parses(self, action_doc):
        assert action_doc["name"]
        assert action_doc["runs"]["using"] == "composite"

    def test_required_inputs_present(self, action_doc):
        inputs = action_doc["inputs"]
        for key in (
            "plugin-version",
            "previous-version",
            "repository",
            "release-date",
            "python-version",
            "meta-repo-ref",
            "caller-path",
        ):
            assert key in inputs, f"missing input: {key}"

    def test_required_inputs_marked_required(self, action_doc):
        inputs = action_doc["inputs"]
        assert inputs["plugin-version"].get("required") is True
        assert inputs["previous-version"].get("required") is True

    def test_outputs_present(self, action_doc):
        outputs = action_doc["outputs"]
        for key in (
            "changed",
            "files-changed",
            "changelog-action",
            "claude-action",
            "roadmap-action",
        ):
            assert key in outputs, f"missing output: {key}"

    def test_meta_repo_ref_default_is_v1_0(self, action_doc):
        """The pinning convention from DTD#5 is that tool repos consume
        @v1.0 (matching drift-check@v1.7's pattern of major-floating tags).
        Defending the default keeps tool-repo PRs from accidentally
        consuming @main."""
        assert action_doc["inputs"]["meta-repo-ref"]["default"] == "v1.0"

    def test_steps_follow_drift_check_pattern(self, action_doc):
        """Composite must check out the meta-repo at the pinned ref into a
        side directory, set up Python, and invoke the sync script."""
        steps = action_doc["runs"]["steps"]
        uses = [s.get("uses", "") for s in steps]
        assert any("actions/checkout" in u for u in uses), "missing actions/checkout"
        assert any("actions/setup-python" in u for u in uses), "missing setup-python"

        checkout_step = next(s for s in steps if "actions/checkout" in s.get("uses", ""))
        assert checkout_step["with"]["repository"] == "TMHSDigital/Developer-Tools-Directory"
        assert checkout_step["with"]["path"] == ".release-doc-sync"

        shell_runs = [s.get("run", "") for s in steps if "run" in s]
        assert any("scripts/release_doc_sync/sync.py" in r for r in shell_runs), (
            "no step invokes the sync script"
        )

    def test_action_does_not_request_github_token(self, action_doc):
        """The action runs inside the caller's release.yml and edits files
        in-place; the caller's existing 'Commit and tag' step picks them
        up. No git operations and no GitHub API calls happen here, so the
        action must NOT ask for a token (would be confusing to consumers
        and create an unnecessary scope-creep surface)."""
        assert "github-token" not in action_doc["inputs"]
