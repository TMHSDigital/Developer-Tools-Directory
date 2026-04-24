from pathlib import Path

from scripts.drift_check.checks import VersionSignalCheck
from scripts.drift_check.types import (
    Check,
    DriftConfig,
    FileSnapshot,
    Finding,
    Pragma,
    RepoSnapshot,
    SignalResult,
    Version,
)


def test_version_asdict():
    v = Version(1, 6, 3, "1.6.3")
    assert v.as_tuple() == (1, 6, 3)
    assert str(v) == "1.6.3"


def test_frozen_dataclasses_immutable():
    f = Finding(repo="r", file=None, check="c", severity="error", message="m")
    import pytest

    with pytest.raises(Exception):
        f.repo = "other"  # type: ignore[misc]


def test_check_protocol_satisfied_by_real_check():
    assert isinstance(VersionSignalCheck(), Check)


def test_drift_config_resolve_layering():
    cfg = DriftConfig(
        repos={"r1": {"skip_checks": ["a"]}},
        types={"cursor-plugin": {"skip_checks": ["b"]}},
        globals={"skip_checks": ["c"], "signal_policy": "same-major-minor"},
    )
    resolved = cfg.resolve("r1", "cursor-plugin")
    assert resolved.skip_checks == frozenset({"a", "b", "c"})
    assert resolved.signal_policy == "same-major-minor"


def test_signal_result_and_pragma_fields():
    s = SignalResult(version=None, format="html-comment", line=1, raw_value="x", malformed=True)
    assert s.malformed
    p = Pragma(check_name="version-signal", reason=None, format="html-comment", line=2)
    assert p.check_name == "version-signal"


def test_file_snapshot_defaults_pragmas():
    fs = FileSnapshot(path=Path("x.md"), content=b"", signal=None)
    assert fs.pragmas == ()


def test_repo_snapshot_holds_files():
    v = Version(1, 6, 3, "1.6.3")
    cfg = DriftConfig().resolve("x", "cursor-plugin")
    snap = RepoSnapshot(
        slug="x", repo_type="cursor-plugin", files={}, meta_version=v,
        meta_commit="HEAD", config=cfg,
    )
    assert snap.slug == "x"
