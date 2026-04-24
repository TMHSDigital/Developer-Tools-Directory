from pathlib import Path

import pytest

from scripts.drift_check.checks.required_refs import (
    RequiredRefsCheck,
    RequiredRefsError,
    _file_links_to,
    load_required_refs,
)
from scripts.drift_check.config import load_config
from scripts.drift_check.semver import parse_version
from scripts.drift_check.snapshot import build_local_snapshot
from tests.conftest import FIXTURES


META = parse_version("1.6.3")
META_COMMIT = "sha"
REQS = {
    "cursor-plugin": {"AGENTS.md": ["standards/agents-template.md"]},
    "mcp-server": {},
}


def _cfg():
    return load_config(FIXTURES / "does_not_exist.json")


def _run(repo: str, reqs=REQS):
    snap = build_local_snapshot(
        repo_path=FIXTURES / repo,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=_cfg(),
        meta_required_refs=reqs,
    )
    return list(RequiredRefsCheck().run(snap))


def test_load_missing_file_returns_empty(tmp_path: Path):
    assert load_required_refs(tmp_path / "absent.json") == {}
    assert load_required_refs(None) == {}


def test_load_valid_file(tmp_path: Path):
    p = tmp_path / "required-refs.json"
    p.write_text(
        '{"version": 1, "requirements": {"cursor-plugin": {"AGENTS.md": ["standards/a.md"]}}}',
        encoding="utf-8",
    )
    out = load_required_refs(p)
    assert out == {"cursor-plugin": {"AGENTS.md": ["standards/a.md"]}}


def test_load_malformed_raises(tmp_path: Path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(RequiredRefsError):
        load_required_refs(p)


def test_load_wrong_schema_raises(tmp_path: Path):
    p = tmp_path / "wrong.json"
    p.write_text('{"requirements": ["not", "an", "object"]}', encoding="utf-8")
    with pytest.raises(RequiredRefsError):
        load_required_refs(p)


def test_file_links_to_matches_inline_and_ref():
    assert _file_links_to(b"[x](standards/foo.md)", "standards/foo.md")
    assert _file_links_to(b"[x](standards/foo.md#anchor)", "standards/foo.md")
    assert _file_links_to(b"[x][ref]\n[ref]: standards/foo.md", "standards/foo.md")
    assert not _file_links_to(b"no links here", "standards/foo.md")


def test_empty_requirements_is_silent():
    # With zero requirements, no findings anywhere — matching Q2 resolution.
    findings = _run("repo_missing_required_refs", reqs={"cursor-plugin": {}})
    assert findings == []


def test_satisfying_repo_has_no_findings():
    findings = _run("repo_satisfying_required_refs")
    assert findings == []


def test_missing_required_ref_is_error():
    findings = _run("repo_missing_required_refs")
    assert len(findings) == 1
    assert findings[0].severity == "error"
    assert "agents-template.md" in findings[0].message


def test_missing_file_is_error(tmp_path: Path):
    """Required file missing entirely."""
    # Create a minimal cursor-plugin-detected repo WITHOUT AGENTS.md.
    (tmp_path / ".cursor-plugin").mkdir()
    (tmp_path / ".cursor-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=_cfg(),
        meta_required_refs=REQS,
    )
    findings = list(RequiredRefsCheck().run(snap))
    assert len(findings) == 1
    assert findings[0].severity == "error"
    assert "not present" in findings[0].message


def test_pragma_suppresses(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n"
        "<!-- drift-ignore: required-refs -->\n"
        "\n# Agents\n",
        encoding="utf-8",
    )
    (tmp_path / ".cursor-plugin").mkdir()
    (tmp_path / ".cursor-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=_cfg(),
        meta_required_refs=REQS,
    )
    findings = list(RequiredRefsCheck().run(snap))
    assert len(findings) == 1
    assert findings[0].severity == "info"


def test_skip_checks_disables_required_refs(tmp_path: Path):
    (tmp_path / "AGENTS.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n\n# Agents (no ref)\n",
        encoding="utf-8",
    )
    (tmp_path / ".cursor-plugin").mkdir()
    (tmp_path / ".cursor-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(
        '{"globals": {"skip_checks": ["required-refs"]}}',
        encoding="utf-8",
    )
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=load_config(cfg_path),
        meta_required_refs=REQS,
    )
    assert list(RequiredRefsCheck().run(snap)) == []
