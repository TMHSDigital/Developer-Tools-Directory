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

Two hardcoded scope rules (DTD#12 v1.9.0):

1. ``AGENTS.md`` and ``CLAUDE.md`` are skipped wholesale. By ecosystem
   convention these files carry narrative-aggregate prose ("177 skills,
   71 rules") that is descriptive, not truth-bearing. Aggregate-truth
   enforcement for those repos belongs in a CFX/Unity-style
   ``validate-counts`` job against ``README.md``. Encoding this in the
   check (rather than per-repo config) keeps the policy where it is
   structurally true: those files' role in the standard.

2. Lines inside ``## Example`` sections, and lines beginning with
   ``**User:**`` / ``**Assistant:**`` markers, are skipped (DTD#37). The
   numbers in roleplay dialogue are illustrative, not claims about the
   skill's actual surface.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Set, Tuple

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

# DTD#12 (v1.9.0): files always skipped by stale-counts regardless of
# config. Match by basename, case-insensitive, to tolerate ``Agents.md``
# or ``claude.md`` variants. The narrative-aggregate convention applies
# to the file's role in the standard, not to a particular casing.
_HARDCODED_SKIP_NAMES: frozenset[str] = frozenset({"agents.md", "claude.md"})

# DTD#37: section headings that introduce roleplay/example content. Any
# ``## Example...`` heading is treated as the start of a skipped section
# until the next ``##``-or-shallower heading. We deliberately match the
# generic ``## Example`` prefix so ``## Example Interaction``, ``## Example
# Interactions``, ``## Example Usage``, etc. all qualify.
_EXAMPLE_HEADING_RE = re.compile(rb"^##\s+Example\b", re.IGNORECASE)
_HEADING_RE = re.compile(rb"^(#{1,6})\s+\S")
# DTD#37: lines starting with these dialogue markers are skipped wherever
# they appear, including outside an example section. Markdown bold form
# wraps the colon: ``**User:**`` / ``**Assistant:**``. Tolerant of leading
# whitespace and trailing content on the same line.
_DIALOGUE_LINE_RE = re.compile(
    rb"^\s*\*\*(User|Assistant)\s*:\*\*", re.IGNORECASE
)


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


def _example_dialogue_lines(body: bytes) -> Set[int]:
    """Return the set of body-relative (1-indexed) line numbers that fall
    inside an ``## Example`` section or that themselves are a roleplay
    dialogue line (``**User:**``/``**Assistant:**``). Counts on these
    lines are illustrative, not aggregate truth claims (DTD#37).

    Section scoping: an ``## Example`` heading opens a region. The region
    closes at the next ``##``-or-shallower heading (``# `` or ``## ``),
    or end-of-file. Deeper headings (``### `` etc.) stay inside.
    """
    skipped: Set[int] = set()
    in_example = False
    for idx, raw in enumerate(body.split(b"\n"), start=1):
        line = raw.rstrip(b"\r")
        if _EXAMPLE_HEADING_RE.match(line):
            in_example = True
            skipped.add(idx)
            continue
        heading_match = _HEADING_RE.match(line)
        if heading_match and len(heading_match.group(1)) <= 2:
            in_example = False
        if in_example:
            skipped.add(idx)
        elif _DIALOGUE_LINE_RE.match(line):
            skipped.add(idx)
    return skipped


class StaleCountsCheck:
    name: str = NAME

    def run(self, snapshot: RepoSnapshot) -> Iterable[Finding]:
        if NAME in snapshot.config.skip_checks:
            return ()

        out: List[Finding] = []
        for rel_path, file in snapshot.files.items():
            # DTD#12 (v1.9.0): hardcoded narrative-aggregate skip.
            # AGENTS.md and CLAUDE.md describe the plugin in prose;
            # aggregate-truth lives in README.md per ecosystem convention.
            if Path(rel_path).name.lower() in _HARDCODED_SKIP_NAMES:
                continue

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
            example_lines = _example_dialogue_lines(body)
            for count, unit, line in _iter_counts(body):
                if line in example_lines:
                    continue
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
