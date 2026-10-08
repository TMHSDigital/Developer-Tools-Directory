"""Update the standards-version field in a YAML-frontmatter file.

Usage: python add_frontmatter.py <file_path> <new_version>

Finds the ``standards-version:`` key inside the leading ``---`` block and
replaces its value. When the key is missing it is inserted as the first key
of the existing frontmatter block, and when the file has no frontmatter at
all a minimal block is prepended. Exits 0 on success, 1 if the file cannot
be read.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def _update(text: str, new_version: str) -> str:
    """Return *text* with ``standards-version`` set to *new_version*."""
    lines = text.splitlines(keepends=True)
    has_block = bool(lines) and lines[0].strip() == "---"
    if has_block:
        for i, line in enumerate(lines[1:], start=1):
            stripped = line.lstrip()
            if stripped.rstrip() in ("---", "..."):
                break
            if re.match(r"^standards-version\s*:", stripped):
                lines[i] = re.sub(
                    r"(standards-version\s*:\s*).*",
                    lambda m: m.group(1) + new_version,
                    line,
                )
                return "".join(lines)
        # Block exists but lacks the key: insert it as the first key.
        lines.insert(1, f"standards-version: {new_version}\n")
        return "".join(lines)
    return f"---\nstandards-version: {new_version}\n---\n" + text


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
    path.write_text(updated, encoding="utf-8", newline="\n")
    print(f"updated {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
