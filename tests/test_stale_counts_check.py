from pathlib import Path

import pytest

from scripts.drift_check.checks.stale_counts import (
    StaleCountsCheck,
    _iter_counts,
    _strip_frontmatter,
)
from scripts.drift_check.config import load_config
from scripts.drift_check.semver import parse_version
from scripts.drift_check.snapshot import build_local_snapshot
from tests.conftest import FIXTURES


META = parse_version("1.6.3")
META_COMMIT = "sha"


def _cfg():
    return load_config(FIXTURES / "does_not_exist.json")


def _run(repo: str):
    snap = build_local_snapshot(
        repo_path=FIXTURES / repo,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=_cfg(),
    )
    return list(StaleCountsCheck().run(snap))


def test_iter_counts_basic():
    hits = list(_iter_counts(b"This plugin has 17 skills and 10 rules."))
    units = [u for _, u, _ in hits]
    assert "skills" in units
    assert "rules" in units


def test_iter_counts_case_insensitive():
    hits = list(_iter_counts(b"150 MCP Tools and 25 MCP tools"))
    assert len(hits) == 2


def test_iter_counts_avoids_non_word_boundary():
    """\\b\\d+\\s+rules\\b — 'ruleset' should NOT match."""
    assert list(_iter_counts(b"the ruleset defines 12 entries")) == []


def test_strip_frontmatter_removes_block():
    content = b"---\nkey: value\n---\n\nbody here 5 skills\n"
    body = _strip_frontmatter(content)
    assert b"body here" in body
    assert b"key: value" not in body


def test_strip_frontmatter_keeps_content_without_block():
    content = b"no frontmatter here\n5 skills"
    assert _strip_frontmatter(content) == content


def test_aggregate_counts_fixture_warns():
    findings = _run("repo_with_aggregate_counts")
    assert findings
    assert all(f.severity == "warn" for f in findings)
    assert all(f.check == "stale-counts" for f in findings)
    # Expect at least: AGENTS.md has 17 skills, 10 rules, 150 MCP tools,
    # 17 skill(s), 10 rule(s), then inside the code block 17 skill, 10 rule.
    # CLAUDE.md adds 17 skills, 10 rules, 150 MCP tools. That is a LOT.
    assert len(findings) >= 5


def test_clean_fixture_has_no_findings():
    findings = _run("clean_repo")
    assert findings == []


def test_code_block_still_warns(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n"
        "\n"
        "```\n"
        "skills/    # 17 skill directories\n"
        "```\n",
        encoding="utf-8",
    )
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=_cfg(),
    )
    findings = list(StaleCountsCheck().run(snap))
    assert findings
    assert findings[0].severity == "warn"


def test_pragma_suppresses(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n"
        "<!-- drift-ignore: stale-counts -->\n"
        "\n"
        "17 skills and 10 rules in our plugin.\n",
        encoding="utf-8",
    )
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=_cfg(),
    )
    findings = list(StaleCountsCheck().run(snap))
    assert len(findings) == 1
    assert findings[0].severity == "info"


def test_skip_checks_disables(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n\n17 skills and 10 rules.\n",
        encoding="utf-8",
    )
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(
        '{"globals": {"skip_checks": ["stale-counts"]}}',
        encoding="utf-8",
    )
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=load_config(cfg_path),
    )
    assert list(StaleCountsCheck().run(snap)) == []


def test_mcp_server_type_skips_via_config_file(tmp_path: Path):
    """Integration: the real standards/drift-checker.config.json skips
    stale-counts for mcp-server type. steam-mcp fixture has aggregate
    counts in CLAUDE.md but should produce zero findings."""
    # Use mcp_repo fixture (mimics steam-mcp).
    # Build a mcp-server-detected repo inline so we exercise the type skip.
    (tmp_path / "CLAUDE.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n\n"
        "This MCP server has 25 tools.\n",
        encoding="utf-8",
    )
    # No skills/, no .cursor-plugin -> mcp-server
    from tests.conftest import REPO_ROOT
    cfg = load_config(REPO_ROOT / "standards" / "drift-checker.config.json")
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=cfg,
    )
    assert list(StaleCountsCheck().run(snap)) == []
