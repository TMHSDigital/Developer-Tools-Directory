"""Smoke-tests for the composite action's structure. Cheap, no Actions
runtime needed."""
from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from tests.conftest import REPO_ROOT


ACTION_YML = REPO_ROOT / ".github" / "actions" / "drift-check" / "action.yml"
WORKFLOW_YML = REPO_ROOT / ".github" / "workflows" / "drift-check.yml"


@pytest.fixture(scope="module")
def action_doc():
    return yaml.safe_load(ACTION_YML.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def workflow_doc():
    return yaml.safe_load(WORKFLOW_YML.read_text(encoding="utf-8"))


def test_action_yaml_parses(action_doc):
    assert action_doc["name"]
    assert action_doc["runs"]["using"] == "composite"


def test_action_inputs_present(action_doc):
    inputs = action_doc["inputs"]
    for key in ("mode", "format", "github-token", "update-sticky-issue", "python-version"):
        assert key in inputs, f"missing input: {key}"


def test_action_outputs_present(action_doc):
    outputs = action_doc["outputs"]
    for key in ("exit-code", "error-count", "warning-count"):
        assert key in outputs, f"missing output: {key}"


def test_action_steps_have_required_actions(action_doc):
    """Composite action must check out the meta-repo, set up Python,
    install deps, and run the checker."""
    steps = action_doc["runs"]["steps"]
    uses = [s.get("uses", "") for s in steps]
    assert any("actions/checkout" in u for u in uses), "missing actions/checkout"
    assert any("actions/setup-python" in u for u in uses), "missing setup-python"
    # At least one shell step running the cli
    shell_runs = [s.get("run", "") for s in steps if "run" in s]
    assert any("scripts/drift_check/cli.py" in r for r in shell_runs)


def test_workflow_has_all_four_triggers(workflow_doc):
    """Decision 5: push (path-gated) + schedule + workflow_dispatch + PR."""
    # PyYAML parses the YAML key 'on:' as the boolean True. Accept either.
    on = workflow_doc.get("on") or workflow_doc.get(True)
    assert on is not None
    assert "push" in on
    assert "schedule" in on
    assert "workflow_dispatch" in on
    assert "pull_request" in on
    # Push is path-gated to drift-relevant paths
    assert "paths" in on["push"]


def test_workflow_uses_local_composite_action(workflow_doc):
    jobs = workflow_doc["jobs"]
    check = jobs["check"]
    uses = [s.get("uses", "") for s in check["steps"] if "uses" in s]
    assert any(u == "./.github/actions/drift-check" for u in uses)


def test_workflow_has_issues_write_permission(workflow_doc):
    """Required for sticky-issue upsert."""
    perms = workflow_doc["jobs"]["check"]["permissions"]
    assert perms.get("issues") == "write"


def test_workflow_token_has_fallback(workflow_doc):
    """github-token input uses ${{ secrets.DRIFT_CHECK_TOKEN || ... }}"""
    check_step = next(
        s for s in workflow_doc["jobs"]["check"]["steps"]
        if s.get("uses", "").endswith("drift-check")
    )
    token = check_step["with"]["github-token"]
    assert "DRIFT_CHECK_TOKEN" in token
    assert "GITHUB_TOKEN" in token
