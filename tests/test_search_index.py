"""The catalog search index must cover every cataloged tool, and the
source-scan fallback in aggregate_search.py must find tool names in repos
that ship no mcp-tools.json manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from tests.conftest import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "site-template"))
import aggregate_search  # noqa: E402


def _load(name: str):
    return json.loads((REPO_ROOT / name).read_text(encoding="utf-8"))


def test_index_has_an_entry_per_registry_tool():
    registry = {e["slug"] for e in _load("registry.json")}
    index = {e["slug"] for e in _load("docs/search-index.json")}
    assert registry == index


def test_index_lists_names_for_every_tool_with_content():
    """A tool that declares skills or MCP tools must contribute searchable
    names; an empty list means search silently misses it (DTD#101)."""
    index = {e["slug"]: e for e in _load("docs/search-index.json")}
    missing = []
    for entry in _load("registry.json"):
        idx = index[entry["slug"]]
        for field in ("skills", "rules", "mcpTools"):
            if entry[field] > 0 and not idx.get(field):
                missing.append(f"{entry['slug']}.{field}")
    assert not missing, (
        "search index has no names for: " + ", ".join(missing)
        + ". Refresh with: python site-template/aggregate_search.py --clone"
    )


def test_source_scan_python_fastmcp(tmp_path: Path):
    server = tmp_path / "mcp-server" / "server.py"
    server.parent.mkdir(parents=True)
    server.write_text(
        "from mcp.server.fastmcp import FastMCP\n"
        "mcp = FastMCP('x')\n\n"
        "@mcp.tool()\n"
        "def lookup_api(name: str) -> str:\n"
        "    return name\n\n"
        "@mcp.tool(name=\"custom_name\")\n"
        "async def something_else() -> str:\n"
        "    return ''\n",
        encoding="utf-8",
    )
    assert aggregate_search.scan_source_tool_names(tmp_path) == ["custom_name", "lookup_api"]


def test_source_scan_typescript_ignores_tests(tmp_path: Path):
    src = tmp_path / "src" / "tools"
    src.mkdir(parents=True)
    (src / "a.ts").write_text(
        'server.tool(\n  "steam_getPlayerCount",\n  "desc",\n  {},\n  async () => ({}),\n);\n'
        'server.registerTool("steam_other", {}, async () => ({}));\n',
        encoding="utf-8",
    )
    (src / "a.test.ts").write_text('server.tool("not_a_tool", "d")\n', encoding="utf-8")
    assert aggregate_search.scan_source_tool_names(tmp_path) == [
        "steam_getPlayerCount",
        "steam_other",
    ]
