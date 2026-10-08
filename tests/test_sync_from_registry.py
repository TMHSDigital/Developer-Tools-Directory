"""Unit tests for scripts/sync_from_registry.py against a minimal catalog
in a temp directory, so edge cases are exercised without touching the real
README, CLAUDE.md or docs site."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import sync_from_registry as sync


def _entry(**overrides) -> dict:
    entry = {
        "name": "Sample Tools",
        "repo": "TMHSDigital/Sample-Tools",
        "slug": "sample-tools",
        "description": "Sample description",
        "type": "cursor-plugin",
        "homepage": "https://tmhsdigital.github.io/Sample-Tools/",
        "skills": 2,
        "rules": 1,
        "mcpTools": 3,
        "extras": {},
        "topics": ["sample"],
        "status": "active",
        "language": "TypeScript",
        "license": "CC-BY-NC-ND-4.0",
        "pagesType": "static",
        "hasCI": True,
    }
    entry.update(overrides)
    return entry


README = """# Catalog

<!-- registry:stats:start -->
<!-- registry:stats:end -->

<!-- registry:tools:start -->
<!-- registry:tools:end -->

<!-- registry:descriptions:start -->
<!-- registry:descriptions:end -->
"""

CLAUDE = """# CLAUDE

<!-- registry:tools:start -->
<!-- registry:tools:end -->

<!-- registry:stats:start -->
<!-- registry:stats:end -->
"""

INDEX = """<!doctype html>
<html><body>
<script id="registry-data" type="application/json">
[]
</script>
</body></html>
"""


@pytest.fixture
def catalog(tmp_path: Path):
    def make(entries: list[dict]) -> Path:
        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "registry.json").write_text(json.dumps(entries), encoding="utf-8")
        (tmp_path / "README.md").write_text(README, encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text(CLAUDE, encoding="utf-8")
        (tmp_path / "docs" / "index.html").write_text(INDEX, encoding="utf-8")
        return tmp_path

    return make


def _embedded(root: Path) -> list[dict]:
    html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    start = html.index('type="application/json">') + len('type="application/json">')
    end = html.index("</script>", start)
    return json.loads(html[start:end])


def test_write_then_check_is_clean(catalog):
    root = catalog([_entry()])
    assert sync.sync_all(root=root, check=False) is True
    assert sync.sync_all(root=root, check=True) is False
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "Sample Tools" in readme
    assert "2 skills" in readme


def test_check_detects_drift(catalog):
    root = catalog([_entry()])
    sync.sync_all(root=root, check=False)
    registry = json.loads((root / "registry.json").read_text(encoding="utf-8"))
    registry[0]["skills"] = 9
    (root / "registry.json").write_text(json.dumps(registry), encoding="utf-8")
    assert sync.sync_all(root=root, check=True) is True


def test_backslashes_in_registry_text_stay_literal(catalog):
    desc = "Paths like C:\\dev\\x and group refs \\1 stay literal"
    root = catalog([_entry(description=desc)])
    sync.sync_all(root=root, check=False)
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert desc in readme
    assert sync.sync_all(root=root, check=True) is False


def test_script_breakout_is_escaped(catalog):
    hostile = "x </script><img src=x> & <!-- y"
    root = catalog([_entry(description=hostile)])
    sync.sync_all(root=root, check=False)
    html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    assert "</script><img" not in html
    assert "<!-- y" not in html
    assert _embedded(root)[0]["description"] == hostile
    # And the next run still finds and rewrites the block cleanly.
    assert sync.sync_all(root=root, check=True) is False


def test_script_safe_json_round_trips():
    data = {"a": "</script>", "b": "&amp;", "c": "<!--"}
    out = sync.script_safe_json(data)
    assert "<" not in out and ">" not in out and "&" not in out
    assert json.loads(out) == data


def test_missing_markers_fail_loudly(catalog):
    root = catalog([_entry()])
    (root / "README.md").write_text("# no markers\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        sync.sync_all(root=root, check=True)


def test_writes_lf_only(catalog):
    root = catalog([_entry()])
    sync.sync_all(root=root, check=False)
    for name in ("README.md", "CLAUDE.md", "docs/index.html"):
        assert b"\r\n" not in (root / name).read_bytes()
