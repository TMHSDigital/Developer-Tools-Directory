"""Enforce the conventions in .github/workflows/README.md on every
workflow: top-level ``permissions: {}`` with job-level grants, and no
``${{ }}`` expressions expanded inside ``run:`` shell source (DTD#117)."""
from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOWS = sorted(
    (Path(__file__).resolve().parent.parent / ".github" / "workflows").glob("*.yml")
)


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_top_level_permissions_are_empty(path: Path):
    doc = _load(path)
    assert doc.get("permissions") == {}, f"{path.name}: top-level permissions must be {{}}"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_no_expressions_inside_run(path: Path):
    doc = _load(path)
    offenders = []
    for job_name, job in (doc.get("jobs") or {}).items():
        for step in job.get("steps") or []:
            if "${{" in (step.get("run") or ""):
                offenders.append(f"{job_name}: {step.get('name') or step.get('run', '')[:40]}")
    assert not offenders, f"{path.name}: move expressions to env: {offenders}"
