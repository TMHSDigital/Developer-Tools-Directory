"""Tests for the --fix helpers (add_frontmatter.py, add_comment_marker.py)
and the drift-check path that invokes them."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from scripts.drift_check import cli
from scripts.drift_check.semver import parse_version
from scripts.drift_check.types import Finding, RepoConfig, RepoSnapshot

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fm = _load("add_frontmatter")
cm = _load("add_comment_marker")


# ------------------------------- frontmatter --------------------------------


def test_frontmatter_replaces_existing_value():
    text = "---\nname: x\nstandards-version: 1.0.0\n---\nbody\n"
    assert fm._update(text, "1.10.1") == "---\nname: x\nstandards-version: 1.10.1\n---\nbody\n"


def test_frontmatter_inserts_key_into_existing_block():
    text = "---\nname: x\n---\nbody\n"
    assert fm._update(text, "1.10.1") == "---\nstandards-version: 1.10.1\nname: x\n---\nbody\n"


def test_frontmatter_prepends_block_when_absent():
    text = "# Title\n"
    assert fm._update(text, "1.10.1") == "---\nstandards-version: 1.10.1\n---\n# Title\n"


def test_frontmatter_ignores_key_outside_block():
    text = "---\nname: x\n---\nstandards-version: 0.0.1\n"
    out = fm._update(text, "2.0.0")
    assert out.startswith("---\nstandards-version: 2.0.0\nname: x\n---\n")
    assert out.endswith("standards-version: 0.0.1\n")


def test_frontmatter_main_writes_file(tmp_path: Path):
    path = tmp_path / "SKILL.md"
    path.write_text("---\nname: x\n---\n", encoding="utf-8")
    assert fm.main(["add_frontmatter.py", str(path), "1.2.3"]) == 0
    assert "standards-version: 1.2.3" in path.read_text(encoding="utf-8")


# ------------------------------- comment marker -----------------------------


def test_marker_replaces_existing():
    text = "<!-- standards-version: 1.0.0 -->\n# Agents\n"
    assert cm._update(text, "1.10.1") == "<!-- standards-version: 1.10.1 -->\n# Agents\n"


def test_marker_inserted_when_missing():
    assert cm._update("# Agents\n", "1.10.1") == "<!-- standards-version: 1.10.1 -->\n# Agents\n"


def test_marker_main_on_missing_file_fails(tmp_path: Path):
    assert cm.main(["add_comment_marker.py", str(tmp_path / "nope.md"), "1.0.0"]) == 1


# ------------------------------- --fix wiring -------------------------------


def test_apply_fixes_live_inserts_missing_signal(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "skills" / "a").mkdir(parents=True)
    skill = repo / "skills" / "a" / "SKILL.md"
    skill.write_text("---\nname: a\n---\nbody\n", encoding="utf-8")
    agents = repo / "AGENTS.md"
    agents.write_text("# Agents\n", encoding="utf-8")

    meta = parse_version("1.10.1")
    snap = RepoSnapshot(
        slug="repo",
        repo_type="cursor-plugin",
        files={},
        meta_version=meta,
        meta_commit="sha",
        config=RepoConfig(slug="repo", repo_type="cursor-plugin"),
    )
    findings = [
        Finding(repo="repo", file=Path("skills/a/SKILL.md"), check="version-signal",
                severity="error", message="missing standards-version"),
        Finding(repo="repo", file=Path("AGENTS.md"), check="version-signal",
                severity="error", message="missing standards-version"),
    ]
    touched = cli._apply_fixes_live([snap], [repo], findings, SCRIPTS_DIR, meta)
    assert touched == 2
    assert "standards-version: 1.10.1" in skill.read_text(encoding="utf-8")
    assert agents.read_text(encoding="utf-8").startswith("<!-- standards-version: 1.10.1 -->")
