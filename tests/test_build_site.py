"""Smoke tests for site-template/build_site.py: a minimal cursor-plugin
repo and a minimal mcp-server repo must both render, and repo-supplied text
must be HTML-escaped."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_SITE = REPO_ROOT / "site-template" / "build_site.py"

pytest.importorskip("jinja2")

HOSTILE = '<script>alert(1)</script> & "quotes"'


def _site(**extra) -> str:
    """Minimal site.json matching what the scaffold emits."""
    site = {
        "accent": "#7c3aed",
        "accentLight": "#a78bfa",
        "heroGradientFrom": "#0d1117",
        "heroGradientTo": "#161b22",
        "links": {"github": "https://github.com/TMHSDigital/Sample"},
        "installSteps": ["Install it"],
    }
    site.update(extra)
    return json.dumps(site)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build(repo: Path, out: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(BUILD_SITE), "--repo-root", str(repo), "--out", str(out)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return (out / "index.html").read_text(encoding="utf-8")


def test_cursor_plugin_site_renders_and_escapes(tmp_path: Path):
    repo = tmp_path / "plugin"
    _write(repo / "site.json", _site(title="Sample Plugin", description=HOSTILE))
    _write(
        repo / ".cursor-plugin" / "plugin.json",
        json.dumps({
            "name": "sample-plugin",
            "displayName": "Sample Plugin",
            "description": HOSTILE,
            "version": "1.2.3",
            "repository": "https://github.com/TMHSDigital/Sample-Plugin",
            "license": "CC-BY-NC-ND-4.0",
        }),
    )
    _write(
        repo / "skills" / "first-skill" / "SKILL.md",
        "---\nname: first-skill\ndescription: Does the first thing\n---\n# First\n",
    )
    _write(repo / "rules" / "style.mdc", "---\ndescription: Style rule\n---\nBody\n")
    _write(
        repo / "mcp-tools.json",
        json.dumps([{"name": "sample_tool", "description": HOSTILE, "category": "General"}]),
    )
    _write(
        repo / "CHANGELOG.md",
        "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] - 2026-01-01\n\n### Fixed\n\n- A fix\n",
    )

    html = _build(repo, tmp_path / "out")
    assert "Sample Plugin" in html
    assert "Does the first thing" in html
    assert "sample_tool" in html
    assert "1.2.3" in html
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_mcp_server_site_renders_from_package_json(tmp_path: Path):
    repo = tmp_path / "server"
    _write(repo / "site.json", _site(description="A sample server"))
    _write(
        repo / "package.json",
        json.dumps({
            "name": "@tmhs/sample-mcp",
            "version": "0.4.0",
            "description": "A sample server",
            "repository": {"url": "git+https://github.com/TMHSDigital/sample-mcp.git"},
            "license": "CC-BY-NC-ND-4.0",
        }),
    )
    _write(repo / "mcp-tools.json", json.dumps([{"name": "do_thing", "description": "x"}]))

    html = _build(repo, tmp_path / "out")
    assert "Sample MCP" in html
    assert "do_thing" in html
    assert "0.4.0" in html
