from pathlib import Path

import pytest

from scripts.drift_check.checks.broken_refs import (
    BrokenRefsCheck,
    _extract_standard_filename,
    _iter_standards_links,
)
from scripts.drift_check.config import load_config
from scripts.drift_check.snapshot import build_local_snapshot
from scripts.drift_check.semver import parse_version
from tests.conftest import FIXTURES


META = parse_version("1.6.3")
META_COMMIT = "fixtureSHA"


def _cfg():
    return load_config(FIXTURES / "does_not_exist.json")


def _run(repo: str, standards: frozenset[str]):
    snap = build_local_snapshot(
        repo_path=FIXTURES / repo,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=_cfg(),
        meta_standards=standards,
    )
    return list(BrokenRefsCheck().run(snap))


def test_extract_standard_filename_variants():
    assert _extract_standard_filename("standards/foo.md") == "foo.md"
    assert _extract_standard_filename("standards/foo.md#anchor") == "foo.md"
    assert _extract_standard_filename("../standards/foo.md") == "foo.md"
    assert _extract_standard_filename(
        "https://github.com/x/y/blob/main/standards/foo.md"
    ) == "foo.md"
    assert _extract_standard_filename("standards/") is None
    assert _extract_standard_filename("standards/foo.txt") is None
    assert _extract_standard_filename("other/path.md") is None


def test_iter_standards_links_finds_inline_and_reference():
    content = (
        b"[a](standards/foo.md)\n"
        b"[b](standards/bar.md#frag)\n"
        b"[label]: standards/baz.md\n"
        b"[unrelated](docs/other.md)\n"
    )
    results = list(_iter_standards_links(content))
    targets = [t for t, _ in results]
    assert "standards/foo.md" in targets
    assert "standards/bar.md#frag" in targets
    assert "standards/baz.md" in targets
    assert not any("docs/other.md" in t for t in targets)


def test_valid_refs_yields_no_findings():
    findings = _run(
        "repo_with_valid_refs",
        frozenset({"agents-template.md", "versioning.md"}),
    )
    assert findings == []


def test_broken_refs_yield_errors():
    findings = _run(
        "repo_with_broken_refs",
        frozenset({"agents-template.md"}),
    )
    # Two distinct missing files + one fragment-link to same missing file =
    # 3 error findings. Reference-style link to another-missing-standard.md
    # adds a 4th.
    assert len(findings) >= 3
    assert all(f.check == "broken-refs" for f in findings)
    assert all(f.severity == "error" for f in findings)
    # The valid reference to agents-template.md must NOT produce a finding.
    msgs = " ".join(f.message for f in findings)
    assert "agents-template.md" not in msgs


def test_no_findings_when_no_standards_links():
    findings = _run("clean_repo", frozenset({"agents-template.md"}))
    assert findings == []


def test_pragma_suppresses_broken_refs(tmp_path: Path):
    """Manufacture an ignored broken-ref by constructing a repo inline."""
    (tmp_path / "AGENTS.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n"
        "<!-- drift-ignore: broken-refs -->\n"
        "\n"
        "See [missing](standards/does-not-exist.md).\n",
        encoding="utf-8",
    )
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=_cfg(),
        meta_standards=frozenset(),
    )
    findings = list(BrokenRefsCheck().run(snap))
    assert len(findings) == 1
    assert findings[0].severity == "info"
    assert "pragma" in findings[0].message


def test_skip_checks_suppresses_entirely(tmp_path: Path):
    """If config says skip broken-refs, zero findings — even for real
    broken references."""
    (tmp_path / "AGENTS.md").write_text(
        "<!-- standards-version: 1.6.3 -->\n"
        "[x](standards/nope.md)\n",
        encoding="utf-8",
    )
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(
        '{"globals": {"skip_checks": ["broken-refs"]}}',
        encoding="utf-8",
    )
    cfg = load_config(cfg_path)
    snap = build_local_snapshot(
        repo_path=tmp_path,
        meta_version=META,
        meta_commit=META_COMMIT,
        config=cfg,
        meta_standards=frozenset(),
    )
    assert list(BrokenRefsCheck().run(snap)) == []
