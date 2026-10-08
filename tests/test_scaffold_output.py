"""Born-green clause C7 and related scaffold guarantees: generated files are
well-formed and escape user text, input is validated, runtimes never mix,
deployed services never mention npm publishing, action pins come from one
table, and a failed registration leaves nothing behind."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

pytest.importorskip("jinja2")
yaml = pytest.importorskip("yaml")

from scaffold import generator  # noqa: E402
from scaffold.generator import ScaffoldError, generate_repo  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = REPO_ROOT / "scaffold" / "templates"

HOSTILE_DESC = 'Tools for "Foo" & <bar> engines, C:\\path\\to and {braces}'


def _gen(tmp_path: Path, **kw) -> Path:
    kw.setdefault("description", HOSTILE_DESC)
    kw.setdefault("register", False)
    kw.setdefault("verbose", False)
    return generate_repo(output=str(tmp_path), **kw)


def _parse_all(root: Path) -> None:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            json.loads(text)
        elif path.suffix in (".yml", ".yaml"):
            yaml.safe_load(text)
        elif path.suffix == ".py":
            ast.parse(text)


@pytest.mark.parametrize(
    "kw",
    [
        {"name": "Hostile Plugin", "repo_type": "cursor-plugin", "mcp_server": True, "skills": 1, "rules": 1},
        {"name": "Hostile Server", "repo_type": "mcp-server"},
        {"name": "Hostile Hosted", "repo_type": "mcp-server", "deployed_service": True},
    ],
    ids=["plugin+py-mcp", "mcp-server", "deployed-service"],
)
def test_hostile_text_yields_well_formed_output(tmp_path: Path, kw: dict):
    repo = _gen(tmp_path, **kw)
    _parse_all(repo)
    if (repo / "package.json").exists():
        assert json.loads((repo / "package.json").read_text(encoding="utf-8"))["description"] == HOSTILE_DESC
    if (repo / ".cursor-plugin" / "plugin.json").exists():
        manifest = json.loads((repo / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))
        assert manifest["description"] == HOSTILE_DESC
    html = repo / "docs" / "index.html"
    if html.exists():
        page = html.read_text(encoding="utf-8")
        assert "<bar>" not in page
        assert "&lt;bar&gt;" in page


def test_mcp_server_gets_buildable_typescript_skeleton(tmp_path: Path):
    repo = _gen(tmp_path, name="Skeleton Server", repo_type="mcp-server")
    for rel in ("tsconfig.json", "src/index.ts", "src/server.ts", "src/__tests__/server.test.ts"):
        assert (repo / rel).is_file(), rel
    pkg = json.loads((repo / "package.json").read_text(encoding="utf-8"))
    assert pkg["scripts"]["build"].startswith("tsc")
    assert pkg["scripts"]["test"] == "vitest run"
    assert "@modelcontextprotocol/sdk" in pkg["dependencies"]
    ci = (repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    # No lockfile yet: CI must not hard-require npm ci or the npm cache.
    assert "npm ci; else npm install" in ci
    assert "cache: npm\n" not in ci


def test_mcp_server_flag_cannot_mix_runtimes(tmp_path: Path):
    with pytest.raises(ScaffoldError, match="cannot be combined"):
        _gen(tmp_path, name="Mixed", repo_type="mcp-server", mcp_server=True)
    assert not any(tmp_path.iterdir())


def test_deployed_service_docs_never_mention_npm_publishing(tmp_path: Path):
    repo = _gen(tmp_path, name="Hosted Only", repo_type="mcp-server", deployed_service=True)
    for doc in ("AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", ".cursorrules"):
        text = (repo / doc).read_text(encoding="utf-8")
        assert "publishes" not in text, doc
        assert "Publishes the package to npm" not in text, doc


@pytest.mark.parametrize(
    "kw, message",
    [
        ({"name": 'Bad "Name"'}, "must not contain"),
        ({"name": "Line\nBreak"}, "control characters"),
        ({"name": "x", "description": "multi\nline"}, "control characters"),
        ({"name": "x", "description": "   "}, "description must not be empty"),
        ({"name": "x", "skills": -1}, "zero or greater"),
        ({"name": "N" * 81}, "at most"),
    ],
)
def test_invalid_input_rejected_before_writing(tmp_path: Path, kw: dict, message: str):
    with pytest.raises(ScaffoldError, match=message):
        _gen(tmp_path, **kw)
    assert not any(tmp_path.iterdir())


def test_duplicate_registration_leaves_no_partial_repo(tmp_path: Path):
    catalog = tmp_path / "catalog"
    catalog.mkdir()
    (catalog / "registry.json").write_text(
        json.dumps([{"slug": "taken-name", "repo": "TMHSDigital/taken-name"}]), encoding="utf-8"
    )
    out = tmp_path / "out"
    with pytest.raises(ScaffoldError, match="already contains slug"):
        generate_repo(
            name="Taken Name", description="d", output=str(out),
            register=True, registry_root=catalog, verbose=False,
        )
    assert not (out / "taken-name").exists()


def test_template_action_pins_match_the_single_pin_table():
    """Every `uses: actions/<x>@vN` literal in the templates agrees with
    ACTION_PINS, so templates cannot drift from the meta-repo (DTD#122)."""
    uses = re.compile(r"uses:\s*(actions/[A-Za-z0-9_.-]+)@(v\d+)")
    mismatches = []
    for tmpl in TEMPLATES.rglob("*.j2"):
        for action, ver in uses.findall(tmpl.read_text(encoding="utf-8")):
            pinned = generator.ACTION_PINS.get(action)
            if pinned is None:
                mismatches.append(f"{tmpl.name}: {action} missing from ACTION_PINS")
            elif ver != pinned:
                mismatches.append(f"{tmpl.name}: {action}@{ver} != {pinned}")
    assert not mismatches, mismatches


def test_rendered_workflows_use_pinned_majors(tmp_path: Path):
    repo = _gen(tmp_path, name="Pin Check", repo_type="mcp-server")
    for wf in (repo / ".github" / "workflows").glob("*.yml"):
        for action, ver in re.findall(r"uses:\s*(actions/[A-Za-z0-9_.-]+)@(v\d+)", wf.read_text(encoding="utf-8")):
            assert generator.ACTION_PINS[action] == ver, f"{wf.name}: {action}@{ver}"
    ci = (repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "node-version: [22, 24]" in ci
    assert json.loads((repo / "package.json").read_text(encoding="utf-8"))["engines"]["node"] == ">=22.0.0"


def test_registry_entry_has_a_valid_category():
    from scripts.validate_registry import CATEGORIES

    entry = generator.build_registry_entry(
        name="X", slug="x", description="d", repo_type="mcp-server",
        skill_count=0, rule_count=0, license_key="cc-by-nc-nd-4.0",
    )
    assert entry["category"] in CATEGORIES
