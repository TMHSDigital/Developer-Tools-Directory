"""Required-workflows check.

For each repo, compare the set of workflow filenames present under
``.github/workflows/`` against the per-type ``required_workflows`` list
resolved from ``standards/drift-checker.config.json``.

A workflow that is required but absent -> ``error``.
Extra or unexpected workflows are never flagged; this check is presence-
only and never emits "this workflow should not be here" findings.

Policy lives in config (``types.<repo-type>.required_workflows``), merged
via the additive-strictness tier logic in ``DriftConfig.resolve``.

The one hardcoded exception: ``publish.yml`` is dropped from the required
set when ``repo_type == "mcp-server"`` and ``archetype == "deployed-service"``
(declared in repo-local ``.drift-check.json``). Do not infer that
archetype from Dockerfile, ``private: true``, or an absent npm name.
Unknown archetypes are errors; a missing ``.drift-check.json`` is the
library default (``publish.yml`` still required).

Edge cases:
* ``repo_type == "unknown"`` -> silent for presence checks; archetype
  load errors still emit.
* ``required_workflows`` empty (absent from config) -> silent; permissive
  by default, same posture as ``required-refs``.
* ``skip_checks`` contains this check's name -> silent for that repo.
* No per-file pragma support; suppression is via ``skip_checks`` in
  config, because the check operates at repo level (no file to annotate
  when the workflow is absent).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Set

from ..types import Finding, RepoSnapshot


NAME = "required-workflows"
PUBLISH_WORKFLOW = "publish.yml"
DEPLOYED_SERVICE = "deployed-service"


class RequiredWorkflowsCheck:
    name: str = NAME

    def run(self, snapshot: RepoSnapshot) -> Iterable[Finding]:
        if NAME in snapshot.config.skip_checks:
            return ()

        out: List[Finding] = []

        if snapshot.archetype_error:
            out.append(
                Finding(
                    repo=snapshot.slug,
                    file=Path(".drift-check.json"),
                    check=NAME,
                    severity="error",
                    message=snapshot.archetype_error,
                    suggested_fix=(
                        "set {\"archetype\": \"deployed-service\"} or "
                        "remove .drift-check.json for the library default"
                    ),
                )
            )

        if (
            snapshot.archetype == DEPLOYED_SERVICE
            and snapshot.repo_type != "mcp-server"
        ):
            out.append(
                Finding(
                    repo=snapshot.slug,
                    file=Path(".drift-check.json"),
                    check=NAME,
                    severity="error",
                    message=(
                        "archetype 'deployed-service' is only valid for "
                        "mcp-server repos"
                    ),
                    suggested_fix="remove .drift-check.json or change repo type",
                )
            )

        # Cannot determine workflow requirements for unknown repo types.
        if snapshot.repo_type == "unknown":
            return out

        required: Set[str] = set(snapshot.config.required_workflows)
        if (
            snapshot.repo_type == "mcp-server"
            and snapshot.archetype == DEPLOYED_SERVICE
        ):
            required.discard(PUBLISH_WORKFLOW)

        if not required:
            return out

        for workflow in sorted(required):
            if workflow not in snapshot.present_workflows:
                out.append(
                    Finding(
                        repo=snapshot.slug,
                        file=None,
                        check=NAME,
                        severity="error",
                        message=(
                            f"required workflow '{workflow}' is absent"
                            f" (required for {snapshot.repo_type} repos)"
                        ),
                        suggested_fix=(
                            f"add .github/workflows/{workflow} following"
                            f" the scaffold template or ci-cd.md"
                        ),
                    )
                )
        return out
