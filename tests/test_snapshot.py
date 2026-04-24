from pathlib import Path

from scripts.drift_check.semver import parse_version
from scripts.drift_check.snapshot import build_local_snapshot
from scripts.drift_check.types import DriftConfig

from tests.conftest import FIXTURES


META = parse_version("1.6.3")
assert META is not None
DEFAULT_CFG = DriftConfig(globals={"signal_policy": "same-major-minor"})


def test_clean_repo_full_snapshot():
    snap = build_local_snapshot(FIXTURES / "clean_repo", META, "HEAD", DEFAULT_CFG)
    assert snap.repo_type == "cursor-plugin"
    paths = {str(p).replace("\\", "/") for p in snap.files}
    assert "AGENTS.md" in paths
    assert "CLAUDE.md" in paths
    assert "skills/sample/SKILL.md" in paths
    assert "rules/sample.mdc" in paths
    for fs in snap.files.values():
        assert fs.signal is not None
        assert fs.signal.version is not None


def test_mcp_repo_only_claude():
    snap = build_local_snapshot(FIXTURES / "mcp_repo", META, "HEAD", DEFAULT_CFG)
    assert snap.repo_type == "mcp-server"
    assert len(snap.files) == 1
    (p, fs), = snap.files.items()
    assert str(p).replace("\\", "/") == "CLAUDE.md"
    assert fs.signal is not None and fs.signal.version is not None


def test_broken_repo_wrong_position_signals_not_detected():
    snap = build_local_snapshot(FIXTURES / "broken_repo", META, "HEAD", DEFAULT_CFG)
    # AGENTS.md has no signal -> None
    agents = snap.files[Path("AGENTS.md")]
    assert agents.signal is None
    # CLAUDE.md has malformed signal -> SignalResult with malformed=True
    claude = snap.files[Path("CLAUDE.md")]
    assert claude.signal is not None and claude.signal.malformed
    # wrongpos SKILL.md has the key in the body, not frontmatter -> None
    wrongpos_skill = snap.files[Path("skills/wrongpos/SKILL.md")]
    assert wrongpos_skill.signal is None
    wrongpos_rule = snap.files[Path("rules/wrongpos.mdc")]
    assert wrongpos_rule.signal is None


def test_ignored_repo_pragmas_extracted():
    snap = build_local_snapshot(FIXTURES / "ignored_repo", META, "HEAD", DEFAULT_CFG)
    agents = snap.files[Path("AGENTS.md")]
    assert any(p.check_name == "version-signal" for p in agents.pragmas)

    short = snap.files[Path("skills/shortform/SKILL.md")]
    assert any(p.format == "yaml-short" for p in short.pragmas)

    longf = snap.files[Path("skills/longform/SKILL.md")]
    assert any(p.format == "yaml-long" and p.check_name == "version-signal" for p in longf.pragmas)


def test_nonexistent_repo_raises(tmp_path: Path):
    import pytest

    with pytest.raises(FileNotFoundError):
        build_local_snapshot(tmp_path / "nope", META, "HEAD", DEFAULT_CFG)


def test_empty_repo_unknown_type(tmp_path: Path):
    import io

    warn = io.StringIO()
    snap = build_local_snapshot(tmp_path, META, "HEAD", DEFAULT_CFG, warn_stream=warn)
    assert snap.repo_type == "unknown"
    assert snap.files == {}
    assert "unknown" in warn.getvalue()
