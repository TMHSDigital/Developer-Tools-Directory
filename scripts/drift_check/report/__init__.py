"""Renderers. Consume ``Iterable[Finding]`` and know nothing about the
internals of specific checks (Decision 7 boundary).

Session A ships ``markdown`` and ``json_out``. Session C adds
``gh_summary`` (writes to ``$GITHUB_STEP_SUMMARY``) and ``issue`` (upsert
sticky issue).
"""
