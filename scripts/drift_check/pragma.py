"""Parse ``drift-ignore`` directives (Decision 6, Q4 resolution).

Two locations, three accepted shapes:

* prose files (AGENTS.md, CLAUDE.md): free-floating HTML comment anywhere
  in the file.

  ``<!-- drift-ignore: version-signal -->``
  ``<!-- drift-ignore: version-signal reason="intentionally tracks 1.5" -->``
  ``<!-- drift-ignore: [version-signal, required-refs] -->`` (comma list)

* metadata files (SKILL.md, .mdc): a ``drift-ignore`` field *inside* the
  first ``---``-fenced YAML block. Two accepted YAML shapes:

  short form (array of strings)::

      drift-ignore: [version-signal, required-refs]

  long form (list of objects)::

      drift-ignore:
        - check: version-signal
          reason: tracking 1.5 for compatibility
        - check: required-refs

Malformed pragmas degrade gracefully: we skip the offending directive and
return whatever we could parse. The parser never raises.

We intentionally avoid a full YAML dependency. The shapes we accept are
constrained enough that a small hand-written block parser is cheaper to
audit than pulling in pyyaml.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Sequence

from .signals import _classify_by_name  # reuse path -> format classifier
from .types import Pragma, PragmaFormat


_HTML_PRAGMA_RE = re.compile(
    rb"<!--\s*drift-ignore\s*:\s*(?P<body>.+?)\s*-->", re.DOTALL
)
_REASON_RE = re.compile(r'reason\s*=\s*"([^"]*)"')
_YAML_FENCE_RE = re.compile(rb"^---\s*$")


def extract_pragmas(path: Path, content: bytes) -> Sequence[Pragma]:
    """Return all drift-ignore pragmas in the file. Never raises.

    File format is inferred from path: prose files use HTML-comment
    pragmas; metadata files use a YAML field inside their frontmatter
    block. Unknown file types return ().
    """
    fmt = _classify_by_name(path)
    if fmt == "html-comment":
        return _extract_html_pragmas(content)
    if fmt == "yaml-frontmatter":
        return _extract_yaml_pragmas(content)
    return ()


def _extract_html_pragmas(content: bytes) -> Sequence[Pragma]:
    out: List[Pragma] = []
    for m in _HTML_PRAGMA_RE.finditer(content):
        line = content.count(b"\n", 0, m.start()) + 1
        body = m.group("body").decode("utf-8", errors="replace")
        for p in _parse_html_pragma_body(body, line):
            out.append(p)
    return tuple(out)


def _parse_html_pragma_body(body: str, line: int) -> List[Pragma]:
    """Body is the text between ``drift-ignore:`` and ``-->``.

    Accepted shapes:

    * ``version-signal`` (bare name)
    * ``version-signal reason="..."``
    * ``[version-signal, required-refs]`` (no reasons when using list form)
    * ``version-signal, required-refs`` (comma list, no brackets)
    """
    reason_match = _REASON_RE.search(body)
    reason = reason_match.group(1) if reason_match else None
    # Strip the reason= clause so we are left with just the check names.
    if reason_match:
        body = body[: reason_match.start()] + body[reason_match.end():]
    body = body.strip().strip("[]").strip()
    if not body:
        return []
    names = [n.strip() for n in body.split(",") if n.strip()]
    return [
        Pragma(
            check_name=name,
            reason=reason if len(names) == 1 else None,
            format="html-comment",
            line=line,
        )
        for name in names
        if _looks_like_check_name(name)
    ]


def _looks_like_check_name(s: str) -> bool:
    """Cheap sanity filter so a garbled pragma body does not produce
    bogus entries like ``Pragma(check_name='reason="x')``. Check names in
    this ecosystem are short kebab-case identifiers."""
    return bool(re.fullmatch(r"[a-z][a-z0-9-]*", s))


def _extract_yaml_pragmas(content: bytes) -> Sequence[Pragma]:
    """Parse the ``drift-ignore:`` field inside the first YAML frontmatter
    block. Accepts short and long forms. Degrades to ``()`` on anything
    unexpected."""
    lines = content.replace(b"\r\n", b"\n").split(b"\n")
    if not lines or not _YAML_FENCE_RE.match(lines[0]):
        return ()
    close_idx = None
    for i in range(1, len(lines)):
        if _YAML_FENCE_RE.match(lines[i]):
            close_idx = i
            break
    if close_idx is None:
        close_idx = len(lines)

    i = 1
    while i < close_idx:
        raw = lines[i].decode("utf-8", errors="replace")
        stripped = raw.strip()
        if stripped.startswith("drift-ignore:"):
            return _parse_yaml_pragma_field(lines, close_idx, i)
        i += 1
    return ()


def _parse_yaml_pragma_field(
    lines: List[bytes], close_idx: int, start: int
) -> Sequence[Pragma]:
    first = lines[start].decode("utf-8", errors="replace")
    after_colon = first.split(":", 1)[1].strip()
    pragma_line = start + 1

    # Short form: drift-ignore: [a, b]
    if after_colon.startswith("[") and after_colon.endswith("]"):
        inner = after_colon[1:-1]
        names = [n.strip().strip("'\"") for n in inner.split(",") if n.strip()]
        return tuple(
            Pragma(check_name=n, reason=None, format="yaml-short", line=pragma_line)
            for n in names
            if _looks_like_check_name(n)
        )

    # Short form inline bare (no brackets): uncommon but tolerated.
    if after_colon and not after_colon.startswith("-"):
        names = [n.strip().strip("'\"") for n in after_colon.split(",") if n.strip()]
        return tuple(
            Pragma(check_name=n, reason=None, format="yaml-short", line=pragma_line)
            for n in names
            if _looks_like_check_name(n)
        )

    # Long form: consume indented ``- check: name`` / ``reason: ...`` blocks.
    out: List[Pragma] = []
    i = start + 1
    current_check: Optional[str] = None
    current_reason: Optional[str] = None
    current_line = pragma_line
    while i < close_idx:
        raw = lines[i].decode("utf-8", errors="replace")
        # A non-indented line ends the block.
        if raw and not raw.startswith((" ", "\t", "-")):
            # Could be a dash at col 0 for list items; handled above.
            if not raw.lstrip().startswith("-"):
                break
        stripped = raw.strip()
        if stripped.startswith("- "):
            if current_check is not None:
                out.append(
                    Pragma(
                        check_name=current_check,
                        reason=current_reason,
                        format="yaml-long",
                        line=current_line,
                    )
                )
            current_check = None
            current_reason = None
            current_line = i + 1
            item = stripped[2:].strip()
            if item.startswith("check:"):
                current_check = item.split(":", 1)[1].strip().strip("'\"")
        elif stripped.startswith("check:"):
            current_check = stripped.split(":", 1)[1].strip().strip("'\"")
        elif stripped.startswith("reason:"):
            current_reason = stripped.split(":", 1)[1].strip().strip("'\"")
        elif not stripped:
            pass
        else:
            break
        i += 1

    if current_check is not None:
        out.append(
            Pragma(
                check_name=current_check,
                reason=current_reason,
                format="yaml-long",
                line=current_line,
            )
        )

    return tuple(p for p in out if _looks_like_check_name(p.check_name))
