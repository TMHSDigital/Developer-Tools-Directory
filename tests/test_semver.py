from scripts.drift_check.semver import compare_policy, parse_version
from scripts.drift_check.types import Version


def v(s: str) -> Version:
    out = parse_version(s)
    assert out is not None, s
    return out


def test_parse_basic():
    assert parse_version("1.6.3").as_tuple() == (1, 6, 3)


def test_parse_v_prefix():
    assert parse_version("v1.6.3").as_tuple() == (1, 6, 3)


def test_parse_prerelease_suffix_ignored():
    assert parse_version("1.6.3-rc1").as_tuple() == (1, 6, 3)


def test_parse_rejects_garbage():
    assert parse_version("not-a-version") is None
    assert parse_version("") is None
    assert parse_version("1.6") is None


def test_exact_match():
    assert compare_policy(v("1.6.3"), v("1.6.3")) == "exact_match"


def test_patch_differs():
    assert compare_policy(v("1.6.1"), v("1.6.3")) == "patch_differs"
    assert compare_policy(v("1.6.0"), v("1.6.3")) == "patch_differs"


def test_major_minor_differs_minor():
    assert compare_policy(v("1.5.3"), v("1.6.3")) == "major_minor_differs"


def test_major_minor_differs_major():
    assert compare_policy(v("0.6.3"), v("1.6.3")) == "major_minor_differs"


def test_tool_newer_patch():
    assert compare_policy(v("1.6.4"), v("1.6.3")) == "tool_newer"


def test_tool_newer_minor():
    assert compare_policy(v("1.7.0"), v("1.6.3")) == "tool_newer"


def test_tool_newer_major():
    assert compare_policy(v("2.0.0"), v("1.6.3")) == "tool_newer"


def test_malformed_none():
    assert compare_policy(None, v("1.6.3")) == "malformed"


def test_malformed_unparsed():
    unparsed = Version(0, 0, 0, "nope", parsed=False)
    assert compare_policy(unparsed, v("1.6.3")) == "malformed"
