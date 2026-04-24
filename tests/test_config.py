import json
from pathlib import Path

import pytest

from scripts.drift_check.config import ConfigError, load_config


def test_missing_file_returns_defaults(tmp_path: Path):
    cfg = load_config(tmp_path / "nope.json")
    assert cfg.repos == {}
    assert cfg.types == {}
    assert cfg.globals == {"signal_policy": "same-major-minor"}


def test_malformed_raises(tmp_path: Path):
    p = tmp_path / "cfg.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(p)


def test_non_object_root_raises(tmp_path: Path):
    p = tmp_path / "cfg.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(p)


def test_resolve_repo_override_wins(tmp_path: Path):
    p = tmp_path / "cfg.json"
    p.write_text(
        json.dumps(
            {
                "repos": {
                    "steam-mcp": {"skip_checks": ["required-refs"]},
                },
                "types": {
                    "mcp-server": {"skip_checks": ["stale-counts"]},
                },
                "globals": {"signal_policy": "same-major-minor"},
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(p)
    resolved = cfg.resolve("steam-mcp", "mcp-server")
    assert "required-refs" in resolved.skip_checks
    assert "stale-counts" in resolved.skip_checks
    assert resolved.signal_policy == "same-major-minor"


def test_resolve_type_only(tmp_path: Path):
    p = tmp_path / "cfg.json"
    p.write_text(
        json.dumps(
            {
                "types": {"mcp-server": {"skip_checks": ["required-refs"]}},
                "globals": {"signal_policy": "same-major-minor"},
            }
        ),
        encoding="utf-8",
    )
    cfg = load_config(p)
    resolved = cfg.resolve("some-other-repo", "mcp-server")
    assert resolved.skip_checks == frozenset({"required-refs"})


def test_resolve_global_policy_override(tmp_path: Path):
    p = tmp_path / "cfg.json"
    p.write_text(
        json.dumps({"globals": {"signal_policy": "exact-match"}}),
        encoding="utf-8",
    )
    cfg = load_config(p)
    resolved = cfg.resolve("anything", "cursor-plugin")
    assert resolved.signal_policy == "exact-match"


def test_resolve_empty_defaults(tmp_path: Path):
    cfg = load_config(tmp_path / "missing.json")
    resolved = cfg.resolve("x", "cursor-plugin")
    assert resolved.skip_checks == frozenset()
    assert resolved.signal_policy == "same-major-minor"


def test_real_shipped_config_loads():
    from tests.conftest import REPO_ROOT
    cfg = load_config(REPO_ROOT / "standards" / "drift-checker.config.json")
    assert "steam-mcp" in cfg.repos
