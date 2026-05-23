"""Required-workflows check.

For each repo, compare the set of workflow filenames present under
``.github/workflows/`` against the per-type ``required_workflows`` list
resolved from ``standards/drift-checker.config.json``.

A workflow that is required but absent -> ``error``.
Extra or unexpected workflows are never flagged; this check is presence-
only and never emits "this workflow should not be here" findings.

Policy lives entirely in config (``types.<repo-type>.required_workflows``),
merged via the additive-strictness tier logic in ``DriftConfig.resolve``.
No workflow names are hardcoded here.

Edge cases:
* ``repo_type == "unknown"`` -> silent; we cannot know what is required.
* ``required_workflows`` empty (absent from config) -> silent; permissive
  by default, same posture as ``required-refs``.
* ``skip_checks`` contains this check's name -> silent for that repo.
* No per-file pragma support; suppression is via ``skip_checks`` in
  config, because the check operates at repo level (no file to annotate
  when the workflow is absent).
"""
from __future__ import annotations

from typing import Iterable, List

from ..types import Finding, RepoSnapshot


NAME = "required-workflows"


class RequiredWorkflowsCheck:
    name: str = NAME

    def run(self, snapshot: RepoSnapshot) -> Iterable[Finding]:
        if NAME in snapshot.config.skip_checks:
            return ()

        # Cannot determine requirements for unknown repo types.
        if snapshot.repo_type == "unknown":
            return ()

        required = snapshot.config.required_workflows
        if not required:
            return ()

        out: List[Finding] = []
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
