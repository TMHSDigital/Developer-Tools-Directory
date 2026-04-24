"""Required standards-references check (Q2 resolution: start permissive).

For each repo, look up the per-type requirements from
``standards/required-refs.json``. For each ``(file, required_ref)`` pair:

* file missing in the repo -> ``error``
* file present but lacks a link to the required standards doc -> ``error``
* otherwise: silent

Today the requirements block is empty (zero tool repos link to
``standards/*.md``), so this check is silent in practice. The plumbing is
ready for the moment that changes — at that point, add entries to
``required-refs.json`` and the check immediately starts enforcing them
without any code change.

The loader is in this module rather than ``config.py`` to keep the data
colocated with its consumer; it is only used here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

from ..types import Finding, RepoSnapshot


NAME = "required-refs"


class RequiredRefsError(Exception):
    """Raised when required-refs.json is present but malformed."""


def load_required_refs(path: Path | None) -> Mapping[str, Mapping[str, Sequence[str]]]:
    """Load and validate ``standards/required-refs.json``.

    Returns a mapping ``{repo_type: {filename: [required_ref, ...]}}``.
    Missing file -> empty mapping. Malformed JSON or wrong schema ->
    ``RequiredRefsError``.
    """
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RequiredRefsError(f"malformed JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RequiredRefsError(f"{path}: expected object at root")
    reqs = data.get("requirements", {})
    if not isinstance(reqs, dict):
        raise RequiredRefsError(f"{path}: 'requirements' must be an object")

    out: dict[str, dict[str, list[str]]] = {}
    for repo_type, file_map in reqs.items():
        if not isinstance(file_map, dict):
            raise RequiredRefsError(
                f"{path}: requirements[{repo_type!r}] must be an object"
            )
        out[repo_type] = {}
        for fname, refs in file_map.items():
            if not isinstance(refs, list):
                raise RequiredRefsError(
                    f"{path}: requirements[{repo_type!r}][{fname!r}] must be a list"
                )
            out[repo_type][fname] = [str(r) for r in refs]
    return out


def _file_links_to(content: bytes, required_ref: str) -> bool:
    """Return True if ``content`` contains any markdown link whose target
    resolves to ``required_ref`` (matched by trailing basename)."""
    basename = required_ref.split("/")[-1]
    if not basename:
        return False
    # Match both inline and reference-style link targets that end with
    # the required basename (optionally followed by #fragment or whitespace).
    pattern = re.compile(
        rb"standards/" + re.escape(basename.encode("utf-8")) + rb"(?:#[^\s)]*)?",
    )
    return pattern.search(content) is not None


class RequiredRefsCheck:
    name: str = NAME

    def run(self, snapshot: RepoSnapshot) -> Iterable[Finding]:
        if NAME in snapshot.config.skip_checks:
            return ()

        requirements = snapshot.meta_required_refs.get(snapshot.repo_type, {})
        if not requirements:
            return ()

        out: List[Finding] = []
        for file_name, required_refs in requirements.items():
            if not required_refs:
                continue
            rel = Path(file_name)
            file = snapshot.files.get(rel)

            pragma = None
            if file is not None:
                pragma = next(
                    (p for p in file.pragmas if p.check_name == NAME), None
                )
            if pragma is not None:
                out.append(
                    Finding(
                        repo=snapshot.slug,
                        file=rel,
                        check=NAME,
                        severity="info",
                        message=(
                            "skipped by drift-ignore pragma"
                            + (f" (reason: {pragma.reason})" if pragma.reason else "")
                        ),
                    )
                )
                continue

            if file is None:
                out.append(
                    Finding(
                        repo=snapshot.slug,
                        file=rel,
                        check=NAME,
                        severity="error",
                        message=(
                            f"{file_name} is required for {snapshot.repo_type} "
                            f"repos but is not present"
                        ),
                        suggested_fix=(
                            f"create {file_name} and link to "
                            f"{', '.join(required_refs)}"
                        ),
                    )
                )
                continue

            for ref in required_refs:
                if not _file_links_to(file.content, ref):
                    out.append(
                        Finding(
                            repo=snapshot.slug,
                            file=rel,
                            check=NAME,
                            severity="error",
                            message=(
                                f"{file_name} must link to {ref} "
                                f"(required for {snapshot.repo_type})"
                            ),
                            suggested_fix=f"add a link to {ref} in {file_name}",
                        )
                    )
        return out
