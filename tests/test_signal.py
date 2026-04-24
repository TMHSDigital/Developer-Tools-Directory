from pathlib import Path

from scripts.drift_check.signals import detect_signal


def test_html_comment_valid():
    content = b"<!-- standards-version: 1.6.3 -->\n\n# body\n"
    r = detect_signal(Path("AGENTS.md"), content)
    assert r is not None
    assert not r.malformed
    assert r.version is not None and r.version.as_tuple() == (1, 6, 3)
    assert r.format == "html-comment"
    assert r.line == 1


def test_html_comment_claude():
    r = detect_signal(Path("CLAUDE.md"), b"<!-- standards-version: 1.6.3 -->\n")
    assert r is not None and r.version is not None


def test_html_comment_flexible_whitespace():
    r = detect_signal(Path("AGENTS.md"), b"<!--  standards-version:1.6.3   -->\n")
    assert r is not None and r.version is not None


def test_html_comment_at_wrong_position_is_none():
    content = b"# AGENTS.md\n\n<!-- standards-version: 1.6.3 -->\n"
    assert detect_signal(Path("AGENTS.md"), content) is None


def test_html_comment_malformed_returns_result():
    r = detect_signal(Path("AGENTS.md"), b"<!-- standards-version: nope -->\n")
    assert r is not None
    assert r.malformed is True
    assert r.version is None
    assert r.raw_value == "nope"


def test_empty_file_returns_none():
    assert detect_signal(Path("AGENTS.md"), b"") is None
    assert detect_signal(Path("skills/x/SKILL.md"), b"") is None


def test_bom_is_stripped_for_html():
    content = b"\xef\xbb\xbf<!-- standards-version: 1.6.3 -->\n"
    r = detect_signal(Path("AGENTS.md"), content)
    assert r is not None and r.version is not None


def test_yaml_frontmatter_valid():
    content = (
        b"---\n"
        b"name: x\n"
        b"standards-version: 1.6.3\n"
        b"---\n"
        b"# body\n"
    )
    r = detect_signal(Path("skills/x/SKILL.md"), content)
    assert r is not None and r.version is not None
    assert r.format == "yaml-frontmatter"
    assert r.line == 3


def test_yaml_mdc_rule():
    content = b"---\nstandards-version: 1.6.3\n---\n"
    r = detect_signal(Path("rules/y.mdc"), content)
    assert r is not None and r.version is not None


def test_yaml_frontmatter_only_body_no_fence():
    content = b"# just body\nstandards-version: 1.6.3\n"
    assert detect_signal(Path("skills/x/SKILL.md"), content) is None


def test_yaml_frontmatter_signal_outside_block_is_none():
    content = b"---\nname: x\n---\nstandards-version: 1.6.3\n"
    assert detect_signal(Path("skills/x/SKILL.md"), content) is None


def test_yaml_frontmatter_malformed():
    content = b"---\nstandards-version: nope\n---\n"
    r = detect_signal(Path("rules/y.mdc"), content)
    assert r is not None
    assert r.malformed and r.version is None


def test_yaml_frontmatter_quoted_value():
    content = b'---\nstandards-version: "1.6.3"\n---\n'
    r = detect_signal(Path("rules/y.mdc"), content)
    assert r is not None and r.version is not None


def test_frontmatter_only_no_body():
    content = b"---\nstandards-version: 1.6.3\n---\n"
    r = detect_signal(Path("skills/x/SKILL.md"), content)
    assert r is not None and r.version is not None


def test_unknown_file_is_none():
    assert detect_signal(Path("README.md"), b"<!-- standards-version: 1.6.3 -->\n") is None


def test_crlf_line_endings():
    content = b"<!-- standards-version: 1.6.3 -->\r\n\r\n# body\r\n"
    r = detect_signal(Path("AGENTS.md"), content)
    assert r is not None and r.version is not None
