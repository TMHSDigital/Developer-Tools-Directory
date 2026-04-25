from pathlib import Path

import pytest

from scripts.drift_check.checks.stale_counts import (
    StaleCountsCheck,
    _example_dialogue_lines,
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


def _run_path(path: Path):
    snap = build_local_snapshot(
        repo_path=path,
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


def test_aggregate_counts_fixture_warns_on_skill_md():
    """DTD#12 v1.9.0: AGENTS.md and CLAUDE.md are hardcoded-skipped, but
    SKILL.md aggregates are still flagged. The fixture has aggregate-count
    prose in all three files; only the SKILL.md hits should appear."""
    findings = _run("repo_with_aggregate_counts")
    assert findings, "expected SKILL.md aggregate counts to warn"
    assert all(f.severity == "warn" for f in findings)
    assert all(f.check == "stale-counts" for f in findings)
    files = {Path(f.file).name for f in findings}
    assert files == {"SKILL.md"}, files


def test_agents_md_is_hardcoded_skipped(tmp_path: Path):
    """DTD#12: narrative-aggregate prose in AGENTS.md is descriptive,
    not truth-bearing. Aggregate-truth lives in README.md per ecosystem
    convention."""
    (tmp_path / "AGENTS.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n\n"
        "This plugin ships 17 skills, 10 rules, and 150 MCP tools.\n",
        encoding="utf-8",
    )
    assert _run_path(tmp_path) == []


def test_claude_md_is_hardcoded_skipped(tmp_path: Path):
    """Same policy as AGENTS.md — CLAUDE.md is the alternate agent-context
    file and shares the narrative-aggregate convention."""
    (tmp_path / "CLAUDE.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n\n"
        "Provides 17 skills, 10 rules, and 150 MCP tools.\n",
        encoding="utf-8",
    )
    assert _run_path(tmp_path) == []


def test_skill_md_off_by_one_is_flagged(tmp_path: Path):
    """Steam-Cursor-Plugin#13 regression: SKILL.md claimed `(7 tools)`
    above an 8-row table. After DTD#12, this class of drift is no longer
    silently swallowed by the type-level skip."""
    skill_dir = tmp_path / "skills" / "steam-api-reference"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Steam API reference\n\n"
        "**Requires `STEAM_API_KEY` (7 tools):**\n\n"
        "| Tool | Description |\n"
        "|------|-------------|\n"
        "| `t1` | a |\n"
        "| `t2` | b |\n"
        "| `t3` | c |\n"
        "| `t4` | d |\n"
        "| `t5` | e |\n"
        "| `t6` | f |\n"
        "| `t7` | g |\n"
        "| `t8` | h |\n",
        encoding="utf-8",
    )
    findings = _run_path(tmp_path)
    assert len(findings) == 1
    assert findings[0].severity == "warn"
    assert "7" in findings[0].message
    assert "tools" in findings[0].message


def test_skill_md_example_dialogue_is_skipped(tmp_path: Path):
    """DTD#37: counts inside ``## Example Interaction`` sections are
    illustrative roleplay, not aggregate truth. Home-Lab regression
    fixture: ``UFW is active with 12 rules`` under an Assistant turn.
    Markdown bold form wraps the colon: ``**User:**`` / ``**Assistant:**``."""
    skill_dir = tmp_path / "skills" / "secrets-management"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Secrets management\n\n"
        "## Example Interaction\n\n"
        "**User:** Audit my homelab security.\n\n"
        "**Assistant:**\n\n"
        "    UFW is active with 12 rules. Ports 22, 80, 443 are open.\n",
        encoding="utf-8",
    )
    assert _run_path(tmp_path) == []


def test_skill_md_count_outside_dialogue_is_flagged(tmp_path: Path):
    """DTD#37 negative test: a count claim in a normal section (not under
    ``## Example``) is still flagged. The dialogue-skip is scoped, not
    file-wide."""
    skill_dir = tmp_path / "skills" / "widgets"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Widgets\n\n"
        "## Available tools\n\n"
        "**Requires `KEY` (8 tools):**\n\n"
        "| Tool |\n|------|\n"
        "| a |\n| b |\n| c |\n| d |\n| e |\n| f |\n| g |\n",
        encoding="utf-8",
    )
    findings = _run_path(tmp_path)
    assert len(findings) == 1
    assert findings[0].severity == "warn"
    assert "8" in findings[0].message


def test_example_section_closes_at_next_h2(tmp_path: Path):
    """DTD#37 scoping: an ``## Example`` region ends at the next
    ``##``-or-shallower heading, not at the end of file."""
    skill_dir = tmp_path / "skills" / "x"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Title\n\n"
        "## Example Interaction\n\n"
        "**Assistant:** UFW shows 12 rules.\n\n"
        "## Reference\n\n"
        "This skill provides 25 tools.\n",
        encoding="utf-8",
    )
    findings = _run_path(tmp_path)
    assert len(findings) == 1
    assert "25" in findings[0].message
    assert "tools" in findings[0].message


def test_example_dialogue_lines_marks_section_and_markers():
    body = (
        b"# Title\n"                      # 1
        b"\n"                              # 2
        b"## Example Interaction\n"       # 3
        b"\n"                              # 4
        b"**User:** hi\n"                 # 5
        b"some content 17 skills\n"       # 6
        b"\n"                              # 7
        b"## Reference\n"                  # 8
        b"normal 10 rules line\n"         # 9
        b"**Assistant:** trailing dialogue\n"  # 10
    )
    skipped = _example_dialogue_lines(body)
    # Lines 3-7 are inside the example section.
    assert {3, 4, 5, 6, 7}.issubset(skipped)
    # Line 8 closes the example region; it is the new heading itself.
    assert 8 not in skipped
    # Line 9 is normal content; not skipped.
    assert 9 not in skipped
    # Line 10 is a stray dialogue marker; skipped wherever it appears.
    assert 10 in skipped


def test_code_block_still_warns(tmp_path: Path):
    """Counts inside fenced code blocks are still flagged — stale narrative
    in examples is still stale information. Uses SKILL.md because AGENTS.md
    is now hardcoded-skipped."""
    skill_dir = tmp_path / "skills" / "sample"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Sample\n\n"
        "```\n"
        "skills/    # 17 skill directories\n"
        "```\n",
        encoding="utf-8",
    )
    findings = _run_path(tmp_path)
    assert findings
    assert findings[0].severity == "warn"


def test_pragma_suppresses(tmp_path: Path):
    """``drift-ignore: stale-counts`` pragma turns warnings into a single
    info finding. SKILL.md uses the YAML-frontmatter pragma form per
    pragma.py's file-format classifier."""
    skill_dir = tmp_path / "skills" / "sample"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "drift-ignore: [stale-counts]\n"
        "---\n"
        "\n"
        "17 skills and 10 rules in our plugin.\n",
        encoding="utf-8",
    )
    findings = _run_path(tmp_path)
    assert len(findings) == 1
    assert findings[0].severity == "info"


def test_skip_checks_disables(tmp_path: Path):
    """Global ``skip_checks`` still suppresses the entire check — the
    emergency hatch is preserved even after the v1.9.0 policy refactor."""
    skill_dir = tmp_path / "skills" / "sample"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "17 skills and 10 rules.\n",
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


def test_mcp_server_repo_no_findings_via_hardcoded_skip(tmp_path: Path):
    """DTD#12 v1.9.0: mcp-server repos no longer skip stale-counts at the
    type level. CLAUDE.md is hardcoded-skipped instead, which still yields
    zero findings on a typical mcp-server repo (no skills/, narrative
    aggregates only in CLAUDE.md)."""
    (tmp_path / "CLAUDE.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n\n"
        "This MCP server has 25 tools.\n",
        encoding="utf-8",
    )
    from tests.conftest import REPO_ROOT
    cfg = load_config(REPO_ROOT / "standards" / "drift-checker.config.json")
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=cfg,
    )
    assert list(StaleCountsCheck().run(snap)) == []
