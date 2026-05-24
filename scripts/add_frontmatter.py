"""Update the standards-version field in a YAML-frontmatter file.

Usage: python add_frontmatter.py <file_path> <new_version>

Finds the ``standards-version:`` key inside the leading ``---`` block and
replaces its value.  Exits 0 on success, 1 if the marker is absent or the
file cannot be parsed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


_FRONTMATTER_RE = re.compile(r"\Astandardsversion:", re.I)  # loose sentinel


def _update(text: str, new_version: str) -> str | None:
    """Return updated text, or None if the standards-version key is absent."""
    lines = text.splitlines(keepends=True)
    in_block = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if i == 0 and stripped.rstrip() == "---":
            in_block = True
            continue
        if in_block and stripped.rstrip() in ("---", "..."):
            break
        if in_block and re.match(r"^standards-version\s*:", stripped):
            lines[i] = re.sub(
                r"(standards-version\s*:\s*).*",
                rf"\g<1>{new_version}",
                line,
            )
            return "".join(lines)
    return None


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
        print(f"error: standards-version not found in frontmatter of {path}", file=sys.stderr)
        return 1

    path.write_text(updated, encoding="utf-8")
    print(f"updated {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
