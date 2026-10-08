"""Tests for scripts/check_fleet_about.py (report-only About drift)."""
from __future__ import annotations

from scripts import check_fleet_about as cfa

ENTRY = {
    "repo": "TMHSDigital/Sample",
    "description": "Sample tools",
    "homepage": "https://tmhsdigital.github.io/Sample/",
    "topics": ["sample", "mcp"],
    "skills": 30,
    "rules": 9,
    "mcpTools": 26,
    "status": "active",
}


def _live(**kw):
    base = {
        "description": "Sample tools",
        "homepage": "https://tmhsdigital.github.io/Sample/",
        "topics": ["mcp", "sample"],
    }
    base.update(kw)
    return base


def test_matching_repo_reports_nothing():
    assert cfa.compare(ENTRY, _live()) == []


def test_stale_counts_in_description_are_flagged():
    diffs = cfa.compare(ENTRY, _live(description="Steam tools - 30 AI skills, 9 rules, 25 MCP tools"))
    assert len(diffs) == 1
    assert "25 MCP tools" in diffs[0] and "mcpTools=26" in diffs[0]


def test_empty_fields_and_missing_topics_are_flagged():
    diffs = cfa.compare(ENTRY, _live(description="", topics=[]))
    assert "GitHub description is empty" in diffs
    assert "GitHub topics are empty" in diffs
    diffs = cfa.compare(ENTRY, _live(topics=["sample"]))
    assert any("mcp" in d for d in diffs)


def test_wording_differences_only_with_flag():
    live = _live(description="A richer description of sample tools")
    assert cfa.compare(ENTRY, live) == []
    assert any("description differs" in d for d in cfa.compare(ENTRY, live, wording=True))


def test_unreadable_repo_and_archived_skip():
    report = cfa.check([ENTRY, {**ENTRY, "repo": "TMHSDigital/Old", "status": "archived"}], fetch=lambda repo: None)
    assert list(report) == ["TMHSDigital/Sample"]
    assert "could not read" in report["TMHSDigital/Sample"][0]
