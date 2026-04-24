"""Aggregate-number warning check (Q3 resolution: pure warn, no sync).

Flags any occurrence of aggregate-count narrative like "177 skills" or
"71 rules" in markdown files. The design doc says: do not try to keep
these in sync with the registry; the correct remediation is removal, so
the check is a warn-and-suggest-removal only.

This check is regex-based and intentionally over-warns — a human reviewing
the warnings decides which are genuine stale narrative (e.g.,
``25 MCP tools``) and which are coincidental (e.g., ``UFW is active with
12 rules`` in a firewall skill). False positives here cost less than
missing a genuine stale count.

We do NOT scan inside YAML frontmatter blocks — those carry structured
data like ``globs:`` and never contain aggregate narrative. We DO still
scan inside fenced code blocks, by design: even in an example block, a
stale count is stale information that will confuse readers once the real
numbers drift.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

from ..types import Finding, RepoSnapshot


NAME = "stale-counts"

# The word boundaries here matter: ``rules`` inside ``ruleset`` or
# ``validates`` should NOT match. Using ``\b`` on both sides.
_COUNT_RE = re.compile(
    rb"\b(\d+)\s+(skills?|rules?|MCP\s+tools?|tools?|commands?|hooks?)\b",
    re.IGNORECASE,
)

# Classify which matches are "strong" signals (very likely stale narrative)
# vs "weak" (plausibly a genuine count). We still warn on both, but the
# suggested fix copy differs.
_STRONG_UNITS = ("skill", "rule", "mcp tool", "command")
_YAML_FENCE_RE = re.compile(rb"^---\s*$", re.MULTILINE)


def _strip_frontmatter(content: bytes) -> bytes:
    """If the file starts with a YAML frontmatter block, strip it and
    return the body only. Otherwise return content unchanged."""
    if not content.startswith(b"---"):
        return content
    # Find the closing fence starting from line 2.
    lines = content.split(b"\n")
    if not lines or lines[0].rstrip(b"\r").strip() != b"---":
        return content
    for i in range(1, len(lines)):
        if lines[i].rstrip(b"\r").strip() == b"---":
            return b"\n".join(lines[i + 1:])
    return content


def _iter_counts(content: bytes) -> Iterable[Tuple[int, str, int]]:
    """Yield ``(count, unit, line_number)`` for each aggregate hit.

    ``content`` is the post-frontmatter body. ``line_number`` is 1-indexed
    against the full original file; callers pass the stripped content and
    the line offset separately.
    """
    for m in _COUNT_RE.finditer(content):
        count = int(m.group(1))
        unit = m.group(2).decode("utf-8", errors="replace").lower()
        line = content.count(b"\n", 0, m.start()) + 1
        yield count, unit, line


def _unit_is_strong(unit: str) -> bool:
    norm = unit.rstrip("s").replace(" ", " ").strip()
    return norm in _STRONG_UNITS or norm + "s" in _STRONG_UNITS


def _frontmatter_line_offset(content: bytes, body: bytes) -> int:
    """Number of lines consumed by the stripped frontmatter, so we can add
    it to body-relative line numbers."""
    if content is body:
        return 0
    consumed = len(content) - len(body)
    return content.count(b"\n", 0, consumed)


class StaleCountsCheck:
    name: str = NAME

    def run(self, snapshot: RepoSnapshot) -> Iterable[Finding]:
        if NAME in snapshot.config.skip_checks:
            return ()

        out: List[Finding] = []
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

            body = _strip_frontmatter(file.content)
            offset = _frontmatter_line_offset(file.content, body)
            for count, unit, line in _iter_counts(body):
                actual_line = line + offset
                strong = _unit_is_strong(unit)
                message = (
                    f"aggregate count at line {actual_line}: "
                    f"{count!r} {unit!r}"
                )
                if strong:
                    fix = (
                        "remove this aggregate or replace with a note "
                        "pointing at the meta-repo registry"
                    )
                else:
                    fix = (
                        "verify this is narrative about the plugin and "
                        "not a domain count (e.g., firewall rules)"
                    )
                out.append(
                    Finding(
                        repo=snapshot.slug,
                        file=rel_path,
                        check=NAME,
                        severity="warn",
                        message=message,
                        suggested_fix=fix,
                    )
                )
        return out
