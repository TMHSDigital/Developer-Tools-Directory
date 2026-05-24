"""Update the standards-version HTML comment marker in an agent file.

Usage: python add_comment_marker.py <file_path> <new_version>

Finds a line matching ``<!-- standards-version: X.Y.Z -->`` (anywhere in the
file, though convention is the first line) and replaces the version.  Exits 0
on success, 1 if the marker is absent.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


_MARKER_RE = re.compile(r"<!--\s*standards-version\s*:\s*[^\s>]+\s*-->")


def _update(text: str, new_version: str) -> str | None:
    """Return updated text, or None if no marker is found."""
    new_marker = f"<!-- standards-version: {new_version} -->"
    updated, count = _MARKER_RE.subn(new_marker, text, count=1)
    return updated if count else None


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"usage: {argv[0]} <file_path> <new_version>", file=sys.stderr)
        return 1

    path = Path(argv[1])
    new_version = argv[2]

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 1

    updated = _update(text, new_version)
    if updated is None:
        print(f"error: standards-version marker not found in {path}", file=sys.stderr)
        return 1

    path.write_text(updated, encoding="utf-8")
    print(f"updated {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
