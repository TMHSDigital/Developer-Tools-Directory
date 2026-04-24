"""Position-strict detection of ``standards-version`` signals (Q6).

Two file formats, two position rules:

* prose files (``AGENTS.md``, ``CLAUDE.md``) — first non-BOM line must be
  an HTML comment of the form ``<!-- standards-version: X.Y.Z -->``.
  Internal whitespace is flexible; canonical form has single spaces.
* metadata files (``SKILL.md``, ``.mdc``) — the ``standards-version`` key
  must live inside the first ``---``-fenced YAML block.

Return semantics:

* ``None`` — no signal at the strict position. The file may still contain
  the literal string ``standards-version`` somewhere else, but we do not
  consider that a signal. That distinction is important for the check:
  "no signal" is error, "signal found but malformed" is also error but
  with a different message and a location.
* ``SignalResult(malformed=True, version=None)`` — something at the right
  position that looks like our marker but does not parse as a version.

We deliberately do not import ``yaml`` here. The first-field ``key: value``
parse we need is too constrained to justify a dependency; a proper YAML
loader is invoked in ``pragma.py`` only when the field shape (array vs.
list-of-objects) demands it.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .semver import parse_version
from .types import SignalFormat, SignalResult


BOM = b"\xef\xbb\xbf"
_HTML_MARKER_RE = re.compile(
    rb"^<!--\s*standards-version\s*:\s*(\S+?)\s*-->\s*$"
)
_YAML_FENCE_RE = re.compile(rb"^---\s*$")
_YAML_KEY_RE = re.compile(
    rb"^standards-version\s*:\s*(.+?)\s*$"
)


def _classify_by_name(path: Path) -> Optional[SignalFormat]:
    """Map a path to its expected signal format. Returns None for files we
    do not check."""
    name = path.name.lower()
    if name in ("agents.md", "claude.md"):
        return "html-comment"
    if name == "skill.md":
        return "yaml-frontmatter"
    if path.suffix.lower() == ".mdc":
        return "yaml-frontmatter"
    return None


def _strip_bom(data: bytes) -> bytes:
    return data[len(BOM):] if data.startswith(BOM) else data


def _split_lines_keep_eol(data: bytes) -> list[bytes]:
    """Split on LF, preserving any trailing CR from a CRLF pair in the
    returned line by stripping it in-place (we do not need to round-trip;
    signal detection only cares about content)."""
    # Normalize CRLF to LF for line-matching purposes without mutating the
    # caller's bytes.
    normalized = data.replace(b"\r\n", b"\n")
    parts = normalized.split(b"\n")
    # split() produces a trailing empty element when data ends with \n;
    # preserve the real line count.
    return parts


def detect_signal(path: Path, content: bytes) -> Optional[SignalResult]:
    """Detect a ``standards-version`` signal at the strict position for the
    file's format. Returns None when no signal is found at the expected
    location (including when the marker is present elsewhere in the file)."""
    fmt = _classify_by_name(path)
    if fmt is None:
        return None

    body = _strip_bom(content)
    if not body:
        return None

    if fmt == "html-comment":
        return _detect_html_comment(body)
    return _detect_yaml_frontmatter(body)


def _detect_html_comment(body: bytes) -> Optional[SignalResult]:
    lines = _split_lines_keep_eol(body)
    if not lines:
        return None
    first = lines[0].rstrip(b"\r")
    m = _HTML_MARKER_RE.match(first)
    if not m:
        return None
    raw_value = m.group(1).decode("utf-8", errors="replace")
    version = parse_version(raw_value)
    return SignalResult(
        version=version,
        format="html-comment",
        line=1,
        raw_value=raw_value,
        malformed=version is None,
    )


def _detect_yaml_frontmatter(body: bytes) -> Optional[SignalResult]:
    lines = _split_lines_keep_eol(body)
    if not lines:
        return None
    # First line must be the opening fence.
    if not _YAML_FENCE_RE.match(lines[0].rstrip(b"\r")):
        return None
    # Find the closing fence on or after line 2.
    close_idx: Optional[int] = None
    for i in range(1, len(lines)):
        if _YAML_FENCE_RE.match(lines[i].rstrip(b"\r")):
            close_idx = i
            break
    if close_idx is None:
        # Unclosed frontmatter — still scan; treat up to EOF as the block.
        close_idx = len(lines)
    for i in range(1, close_idx):
        line = lines[i].rstrip(b"\r")
        m = _YAML_KEY_RE.match(line)
        if not m:
            continue
        raw_value = m.group(1).decode("utf-8", errors="replace").strip()
        # Strip surrounding quotes if a value was quoted in YAML.
        if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] and raw_value[0] in ("'", '"'):
            raw_value = raw_value[1:-1]
        version = parse_version(raw_value)
        return SignalResult(
            version=version,
            format="yaml-frontmatter",
            line=i + 1,
            raw_value=raw_value,
            malformed=version is None,
        )
    return None
