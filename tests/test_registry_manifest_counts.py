"""Guard against the registry's ``mcpTools`` count drifting from a tool repo's
actual ``mcp-tools.json`` manifest (finding D4: screencast-mcp was recorded as
10 in the registry while its manifest and server registered 25).

The registry is the catalog's source of truth, but the manifest is the tool's
shipped contract; when both are present they must agree. This test compares the
two for every tool repo that is checked out as a sibling of the meta-repo. It
skips when no sibling checkouts exist - in the meta-repo's own CI the tool
repos are not cloned, so full-fleet validation is expected to run CI-side where
the repos can be cloned (e.g. a fleet job that checks out each repo).
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# Tool repos are checked out as siblings of the meta-repo (C:\Dev\<repo-name>).
DEV_ROOT = REPO_ROOT.parent


def _load_registry() -> list[dict]:
    return json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))


def _sibling_checkout(repo_field: str) -> Path | None:
    name = repo_field.split("/")[-1]
    candidate = DEV_ROOT / name
    return candidate if candidate.is_dir() else None


def test_registry_mcptools_matches_local_manifests():
    mismatches = []
    checked = []
    for entry in _load_registry():
        repo_dir = _sibling_checkout(entry.get("repo", ""))
        if repo_dir is None:
            continue
        manifest = repo_dir / "mcp-tools.json"
        if not manifest.is_file():
            continue
        try:
            tools = json.loads(manifest.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(tools, list):
            continue
        checked.append(entry["slug"])
        declared = int(entry.get("mcpTools") or 0)
        if len(tools) != declared:
            mismatches.append((entry["slug"], declared, len(tools)))

    if not checked:
        pytest.skip(
            "no sibling tool checkouts with mcp-tools.json found; full-fleet "
            "validation runs CI-side where repos can be cloned"
        )

    assert not mismatches, "registry mcpTools != manifest length: " + ", ".join(
        f"{slug}: registry={declared} manifest={actual}"
        for slug, declared, actual in mismatches
    )
