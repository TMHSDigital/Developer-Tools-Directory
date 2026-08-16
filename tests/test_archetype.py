"""Snapshot loading of `.drift-check.json` archetypes."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.drift_check.config import load_config
from scripts.drift_check.semver import parse_version
from scripts.drift_check.snapshot import KNOWN_ARCHETYPES, _load_archetype, build_local_snapshot


META = parse_version("1.11.0")
CONFIG = Path(__file__).resolve().parents[1] / "standards" / "drift-checker.config.json"


def _mcp_tree(tmp_path: Path, *, workflows: set[str], manifest: object | None) -> Path:
    repo = tmp_path / "svc"
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / "package.json").write_text("{}", encoding="utf-8")
    for name in workflows:
        (repo / ".github" / "workflows" / name).write_text("name: x\n", encoding="utf-8")
    if manifest is not None:
        (repo / ".drift-check.json").write_text(
            json.dumps(manifest) if not isinstance(manifest, str) else manifest,
            encoding="utf-8",
        )
    return repo


def test_missing_manifest_is_library_default(tmp_path: Path) -> None:
    repo = _mcp_tree(
        tmp_path,
        workflows={"drift-check.yml", "stale.yml", "publish.yml"},
        manifest=None,
    )
    archetype, err = _load_archetype(repo)
    assert archetype is None
    assert err is None


def test_deployed_service_manifest_loads(tmp_path: Path) -> None:
    repo = _mcp_tree(
        tmp_path,
        workflows={"drift-check.yml", "stale.yml"},
        manifest={"archetype": "deployed-service"},
    )
    snap = build_local_snapshot(
        repo_path=repo,
        meta_version=META,
        meta_commit="test",
        config=load_config(CONFIG),
        slug="svc",
    )
    assert snap.repo_type == "mcp-server"
    assert snap.archetype == "deployed-service"
    assert snap.archetype_error is None
    assert "publish.yml" not in snap.present_workflows


def test_unknown_archetype_is_load_error(tmp_path: Path) -> None:
    repo = _mcp_tree(
        tmp_path,
        workflows={"drift-check.yml"},
        manifest={"archetype": "hosted"},
    )
    archetype, err = _load_archetype(repo)
    assert archetype is None
    assert err is not None
    assert "unknown archetype" in err
    assert "deployed-service" in err
    assert KNOWN_ARCHETYPES == frozenset({"deployed-service"})


def test_invalid_json_is_load_error(tmp_path: Path) -> None:
    repo = _mcp_tree(tmp_path, workflows=set(), manifest="{not json")
    archetype, err = _load_archetype(repo)
    assert archetype is None
    assert err is not None
    assert err.startswith("invalid .drift-check.json:")


def test_does_not_infer_from_private_package_json(tmp_path: Path) -> None:
    repo = _mcp_tree(
        tmp_path,
        workflows={"drift-check.yml", "stale.yml"},
        manifest=None,
    )
    (repo / "package.json").write_text(
        '{"name": "svc", "private": true}', encoding="utf-8"
    )
    (repo / "Dockerfile").write_text("FROM node:22\n", encoding="utf-8")
    snap = build_local_snapshot(
        repo_path=repo,
        meta_version=META,
        meta_commit="test",
        config=load_config(CONFIG),
        slug="svc",
    )
    assert snap.archetype is None
    assert snap.archetype_error is None
