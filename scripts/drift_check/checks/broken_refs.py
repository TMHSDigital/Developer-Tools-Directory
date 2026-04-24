"""Broken standards/*.md references check.

Scans every markdown file in the snapshot for links whose targets live
under ``standards/``. Resolves each target against the meta-repo's
``standards/`` directory at snapshot time. Missing target -> ``error``.

Zero surface today — the design-doc preflight found 0 ``standards/*.md``
links across 13 agent-context files in 9 repos. The check is implemented
anyway so the plumbing is in place the moment tool repos start linking
to standards.

Link shapes we care about:

* ``[text](standards/foo.md)``
* ``[text](standards/foo.md#anchor)`` — fragment checking deferred; we
  only verify the file exists for now
* ``[text](../Developer-Tools-Directory/standards/foo.md)`` — tolerated
  by stripping to the trailing ``standards/foo.md``
* reference-style ``[text][label]`` + ``[label]: standards/foo.md`` —
  the label-definition regex below catches these
* bare URLs to GitHub-hosted standards are NOT checked; contribute
  a separate check for those when/if they appear

We do NOT follow non-``standards/`` links. That is out of scope for this
check; it would duplicate a general markdown link checker.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

from ..types import Finding, RepoSnapshot


NAME = "broken-refs"

# Inline link: ``[text](target)`` where target starts with or contains
# ``standards/`` and ends with ``.md`` (with optional ``#fragment``).
_INLINE_LINK_RE = re.compile(
    rb"\[[^\]]*\]\(\s*([^)\s]*standards/[^)\s#]+\.md(?:#[^)\s]*)?)\s*\)"
)
# Reference-style definition: ``[label]: standards/foo.md``
_REF_DEF_RE = re.compile(
    rb"^\s*\[[^\]]+\]:\s*([^\s]*standards/[^\s#]+\.md(?:#[^\s]*)?)\s*$",
    re.MULTILINE,
)


def _iter_standards_links(content: bytes) -> Iterable[Tuple[str, int]]:
    """Yield ``(target, line_number)`` for every standards link in the
    file. ``target`` is a decoded string; ``line_number`` is 1-indexed."""
    for m in _INLINE_LINK_RE.finditer(content):
        yield m.group(1).decode("utf-8", errors="replace"), content.count(b"\n", 0, m.start()) + 1
    for m in _REF_DEF_RE.finditer(content):
        yield m.group(1).decode("utf-8", errors="replace"), content.count(b"\n", 0, m.start()) + 1


def _extract_standard_filename(target: str) -> str | None:
    """Given a link target, return the standards file basename or None.

    ``standards/foo.md`` -> ``foo.md``
    ``standards/foo.md#anchor`` -> ``foo.md``
    ``../standards/foo.md`` -> ``foo.md``
    ``https://github.com/.../standards/foo.md`` -> ``foo.md``
    """
    target = target.split("#", 1)[0]
    marker = "standards/"
    idx = target.rfind(marker)
    if idx == -1:
        return None
    basename = target[idx + len(marker):].strip("/")
    if not basename or not basename.endswith(".md"):
        return None
    if "/" in basename:
        # Nested path under standards/. We only ship flat files in
        # ``standards/``, so a nested path is a broken reference by
        # construction.
        return basename
    return basename


class BrokenRefsCheck:
    name: str = NAME

    def run(self, snapshot: RepoSnapshot) -> Iterable[Finding]:
        if NAME in snapshot.config.skip_checks:
            return ()

        out: List[Finding] = []
        meta_files = snapshot.meta_standards

        for rel_path, file in snapshot.files.items():
            pragma = next(
                (p for p in file.pragmas if p.check_name == NAME), None
            )
            if pragma is not None:
                out.append(
                    Finding(
                        repo=snapshot.slug,
                        file=rel_path,
                        check=NAME,
                        severity="info",
                        message=(
                            "skipped by drift-ignore pragma"
                            + (f" (reason: {pragma.reason})" if pragma.reason else "")
                        ),
                    )
                )
                continue

            for target, line in _iter_standards_links(file.content):
                basename = _extract_standard_filename(target)
                if basename is None:
                    continue
                if basename not in meta_files:
                    out.append(
                        Finding(
                            repo=snapshot.slug,
                            file=rel_path,
                            check=NAME,
                            severity="error",
                            message=(
                                f"broken standards reference at line {line}: "
                                f"{target!r} (standards/{basename} does not "
                                f"exist in meta-repo)"
                            ),
                            suggested_fix=(
                                f"check the filename; available standards: "
                                f"{', '.join(sorted(meta_files)) or '(none found)'}"
                            ),
                        )
                    )
        return out
