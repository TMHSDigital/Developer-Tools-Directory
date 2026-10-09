"""Regression guards for documentation drift (DTD#109, #110, #111):
the writing-style rule (no em dashes, en dashes, or emoji), no references
to catalog files that do not exist, no registry examples with the removed
per-tool ``version`` field, and a ROADMAP whose current version matches
VERSION."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

TEXT_SUFFIXES = {".md", ".py", ".yml", ".yaml", ".j2", ".html", ".json", ".txt", ".toml", ".cfg"}
# gh_summary renders status icons into the Actions step summary; they are
# functional output, not prose.
EMOJI_ALLOWLIST = {"scripts/drift_check/report/gh_summary.py"}
# Built from code points so this file stays pure ASCII and passes its own check.
EM_DASH, EN_DASH = chr(0x2014), chr(0x2013)
EMOJI_RE = re.compile("[%s-%s%s-%s]" % (chr(0x1F300), chr(0x1FAFF), chr(0x2600), chr(0x27BF)))


def _tracked_text_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git not available")
    files = [REPO_ROOT / f for f in out.splitlines()]
    return [
        f for f in files
        if f.is_file() and (f.suffix in TEXT_SUFFIXES or f.name in (".cursorrules", "VERSION"))
    ]


def test_no_em_or_en_dashes_or_emoji():
    offenders = []
    for path in _tracked_text_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if EM_DASH in line or EN_DASH in line:
                offenders.append(f"{rel}:{lineno}: dash")
            if rel not in EMOJI_ALLOWLIST and EMOJI_RE.search(line):
                offenders.append(f"{rel}:{lineno}: emoji")
    assert not offenders, "standards/writing-style.md violations:\n" + "\n".join(offenders[:50])


DOC_FILES = ["README.md", "CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md", ".cursorrules"]


@pytest.mark.parametrize("name", ["docs/style.css", "docs/script.js"])
def test_docs_do_not_reference_missing_catalog_files(name: str):
    if (REPO_ROOT / name).exists():
        pytest.skip(f"{name} exists")
    hits = [d for d in DOC_FILES if name in (REPO_ROOT / d).read_text(encoding="utf-8")]
    assert not hits, f"{name} does not exist but is referenced in {hits}"


def test_registry_examples_have_no_version_field():
    """CLAUDE.md forbids a per-tool version field; contributor examples
    must not teach it."""
    block_re = re.compile(r"```json\n(.*?)```", re.DOTALL)
    offenders = []
    for doc in ["CONTRIBUTING.md", "docs/contributors/adding-a-tool.md", "AGENTS.md"]:
        text = (REPO_ROOT / doc).read_text(encoding="utf-8")
        for block in block_re.findall(text):
            if '"slug"' in block and '"repo"' in block and '"version"' in block:
                offenders.append(doc)
    assert not offenders, offenders


def test_registry_has_no_version_field():
    entries = json.loads((REPO_ROOT / "registry.json").read_text(encoding="utf-8"))
    assert not [e["slug"] for e in entries if "version" in e]


def test_roadmap_current_version_matches_version_file():
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
    match = re.search(r"^\*\*Current:\*\* v(\S+)", roadmap, re.MULTILINE)
    assert match, "ROADMAP.md needs a '**Current:** vX.Y.Z' line"
    assert match.group(1) == version, (
        f"ROADMAP.md says v{match.group(1)} but VERSION is {version}; update the Current Status section"
    )
