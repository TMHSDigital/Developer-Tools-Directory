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
    for key in (
        "mode", "format", "github-token", "issues-token",
        "update-sticky-issue", "python-version",
    ):
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


def test_action_propagates_checker_exit_code(action_doc):
    """Final step must propagate the drift checker's rc to the caller.

    Regression guard for the rc=1 swallowing bug fixed in v1.7.4: prior
    to the fix the action exited 0 unless rc=2, so tool-repo CI passed
    green even when drift was detected.
    """
    steps = action_doc["runs"]["steps"]
    propagate = next(
        (s for s in steps if s.get("name") == "Propagate checker exit code"),
        None,
    )
    assert propagate is not None, "missing 'Propagate checker exit code' step"
    # Must run unconditionally so it always surfaces the recorded rc.
    assert propagate.get("if", "").strip().startswith("always()"), (
        f"propagate step must use if: always(); got {propagate.get('if')!r}"
    )
    body = propagate.get("run", "")
    assert "steps.run.outputs.exit-code" in body, (
        "propagate step must read exit-code from the run step output"
    )
    assert 'exit "$RC"' in body, (
        "propagate step must exit with the recorded rc, not a hard-coded value"
    )


def test_action_propagate_step_is_last(action_doc):
    """The propagate step must be the last step so it determines the
    action's exit code regardless of what happens before it."""
    steps = action_doc["runs"]["steps"]
    assert steps[-1].get("name") == "Propagate checker exit code", (
        "propagate must be the last step; otherwise its exit code can be "
        "overridden by a subsequent step"
    )


def test_action_sticky_step_does_not_swallow_rc(action_doc):
    """Sticky-step is best-effort and should always exit 0; the propagate
    step is the single source of truth for the action's rc."""
    steps = action_doc["runs"]["steps"]
    sticky = next((s for s in steps if s.get("id") == "sticky"), None)
    assert sticky is not None, "missing sticky step"
    body = sticky.get("run", "")
    # No `exit "$RC"` or `exit $RC` in sticky — those would gate the
    # action on a transient gh-API hiccup.
    assert "exit \"$RC\"" not in body and "exit $RC" not in body, (
        "sticky step must not propagate its own RC; that's the propagate step's job"
    )


def test_meta_repo_ref_default_is_floating_major(action_doc):
    """The meta-repo-ref input must default to a floating MAJOR tag
    (v1, v2, ...), never a specific MINOR (v1.7) or PATCH (v1.7.5).

    Regression guard for the bug surfaced during the v1.9.0 ecosystem
    signal rollout: the default was hardcoded to 'v1.7' and never bumped
    when 1.8/1.9 shipped. Tool repos consuming the action without an
    explicit ``meta-repo-ref`` override silently checked out the meta-repo
    at v1.7, so any tool signals past 1.7.0 produced inverse-direction
    version-signal warnings.

    Floating-major is the right granularity because DTD#14 auto-maintains
    v1 to point at the latest 1.x.y release, so future MINORs auto-flow
    through this default with zero action.yml edits.
    """
    import re

    meta_ref_default = action_doc["inputs"]["meta-repo-ref"]["default"]
    assert re.match(r"^v\d+$", meta_ref_default), (
        f"meta-repo-ref default must be a floating major tag (v1, v2, ...) "
        f"per DTD#14 to avoid stale references; got {meta_ref_default!r}"
    )
