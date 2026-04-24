from pathlib import Path

from scripts.drift_check.pragma import extract_pragmas


def test_no_pragma_html():
    content = b"<!-- standards-version: 1.6.3 -->\n\n# body\n"
    assert extract_pragmas(Path("AGENTS.md"), content) == ()


def test_no_pragma_yaml():
    content = b"---\nname: x\nstandards-version: 1.6.3\n---\n"
    assert extract_pragmas(Path("skills/x/SKILL.md"), content) == ()


def test_html_short_form_bare():
    content = b"<!-- drift-ignore: version-signal -->\n"
    p = extract_pragmas(Path("AGENTS.md"), content)
    assert len(p) == 1
    assert p[0].check_name == "version-signal"
    assert p[0].reason is None
    assert p[0].format == "html-comment"


def test_html_with_reason():
    content = b'<!-- drift-ignore: version-signal reason="tracking v1.5" -->\n'
    p = extract_pragmas(Path("AGENTS.md"), content)
    assert len(p) == 1
    assert p[0].check_name == "version-signal"
    assert p[0].reason == "tracking v1.5"


def test_html_comma_list():
    content = b"<!-- drift-ignore: version-signal, required-refs -->\n"
    p = extract_pragmas(Path("CLAUDE.md"), content)
    assert [x.check_name for x in p] == ["version-signal", "required-refs"]


def test_html_bracket_list():
    content = b"<!-- drift-ignore: [version-signal, required-refs] -->\n"
    p = extract_pragmas(Path("CLAUDE.md"), content)
    assert {x.check_name for x in p} == {"version-signal", "required-refs"}


def test_multiple_html_pragmas():
    content = (
        b"<!-- standards-version: 1.6.3 -->\n"
        b"<!-- drift-ignore: version-signal -->\n"
        b"<!-- drift-ignore: required-refs -->\n"
    )
    p = extract_pragmas(Path("AGENTS.md"), content)
    assert len(p) == 2


def test_malformed_html_pragma_is_graceful():
    content = b"<!-- drift-ignore: ???!!! -->\n"
    p = extract_pragmas(Path("AGENTS.md"), content)
    assert p == ()


def test_yaml_short_form():
    content = (
        b"---\n"
        b"name: x\n"
        b"standards-version: 1.5.0\n"
        b"drift-ignore: [version-signal]\n"
        b"---\n"
    )
    p = extract_pragmas(Path("skills/x/SKILL.md"), content)
    assert len(p) == 1
    assert p[0].check_name == "version-signal"
    assert p[0].format == "yaml-short"


def test_yaml_short_form_multi():
    content = (
        b"---\n"
        b"drift-ignore: [version-signal, required-refs]\n"
        b"---\n"
    )
    p = extract_pragmas(Path("rules/y.mdc"), content)
    assert {x.check_name for x in p} == {"version-signal", "required-refs"}


def test_yaml_long_form_with_reasons():
    content = (
        b"---\n"
        b"name: x\n"
        b"drift-ignore:\n"
        b"  - check: version-signal\n"
        b"    reason: tracking 1.5\n"
        b"  - check: required-refs\n"
        b"---\n"
    )
    p = extract_pragmas(Path("skills/x/SKILL.md"), content)
    names = {x.check_name: x.reason for x in p}
    assert names == {"version-signal": "tracking 1.5", "required-refs": None}
    for x in p:
        assert x.format == "yaml-long"


def test_yaml_pragma_outside_frontmatter_is_ignored():
    content = (
        b"---\n"
        b"name: x\n"
        b"---\n"
        b"drift-ignore: [version-signal]\n"
    )
    assert extract_pragmas(Path("skills/x/SKILL.md"), content) == ()


def test_unknown_file_returns_empty():
    assert extract_pragmas(Path("README.md"), b"<!-- drift-ignore: version-signal -->") == ()
