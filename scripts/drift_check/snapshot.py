"""Build a ``RepoSnapshot`` from a local clone path.

Session A is local-clone only. Sparse-checkout / ``gh api`` remote mode is
Session C. The function signature here is already shaped so that a remote
mode can be a sibling builder (``build_sparse_snapshot``) producing the
same type.

File discovery is restricted to the four agent-file shapes we care about:

* ``AGENTS.md`` at repo root (optional)
* ``CLAUDE.md`` at repo root (optional)
* every ``skills/<name>/SKILL.md``
* every ``rules/*.mdc``

Plus ``.cursor-plugin/plugin.json`` for repo-type detection (not parsed
into a FileSnapshot since it has no signal).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Optional

from .pragma import extract_pragmas
from .signals import detect_signal
from .types import (
    DriftConfig,
    FileSnapshot,
    RepoSnapshot,
    RepoType,
    Version,
)


def _detect_repo_type(repo_path: Path) -> RepoType:
    """Per the design doc's detection rules:

    * ``.cursor-plugin/plugin.json`` present -> ``cursor-plugin``
    * no skills/ or rules/ directories but CLAUDE.md present -> ``mcp-server``
    * otherwise -> ``unknown``
    """
    if (repo_path / ".cursor-plugin" / "plugin.json").is_file():
        return "cursor-plugin"
    has_skills = (repo_path / "skills").is_dir()
    has_rules = (repo_path / "rules").is_dir()
    has_claude = (repo_path / "CLAUDE.md").is_file()
    if not has_skills and not has_rules and has_claude:
        return "mcp-server"
    return "unknown"


def _collect_paths(repo_path: Path) -> list[Path]:
    out: list[Path] = []
    for name in ("AGENTS.md", "CLAUDE.md"):
        p = repo_path / name
        if p.is_file():
            out.append(p)
    skills_dir = repo_path / "skills"
    if skills_dir.is_dir():
        for skill in sorted(skills_dir.iterdir()):
            if not skill.is_dir():
                continue
            sk = skill / "SKILL.md"
            if sk.is_file():
                out.append(sk)
    rules_dir = repo_path / "rules"
    if rules_dir.is_dir():
        for rule in sorted(rules_dir.iterdir()):
            if rule.is_file() and rule.suffix.lower() == ".mdc":
                out.append(rule)
    return out


def build_local_snapshot(
    repo_path: Path,
    meta_version: Version,
    meta_commit: str,
    config: DriftConfig,
    slug: Optional[str] = None,
    warn_stream=sys.stderr,
) -> RepoSnapshot:
    """Construct a RepoSnapshot by walking the local clone tree.

    ``slug`` defaults to ``repo_path.name`` if not supplied. ``warn_stream``
    is an injection seam for tests that want to capture warnings.
    """
    repo_path = repo_path.resolve()
    if not repo_path.is_dir():
        raise FileNotFoundError(f"repo path is not a directory: {repo_path}")

    resolved_slug = slug or repo_path.name
    repo_type = _detect_repo_type(repo_path)

    if repo_type == "unknown":
        warn_stream.write(
            f"warning: repo {resolved_slug} at {repo_path} has no "
            f"cursor-plugin manifest and does not match the mcp-server "
            f"shape; classifying as 'unknown'.\n"
        )

    files: Dict[Path, FileSnapshot] = {}
    for path in _collect_paths(repo_path):
        try:
            content = path.read_bytes()
        except OSError as exc:
            warn_stream.write(f"warning: could not read {path}: {exc}\n")
            continue
        rel = path.relative_to(repo_path)
        files[rel] = FileSnapshot(
            path=rel,
            content=content,
            signal=detect_signal(rel, content),
            pragmas=extract_pragmas(rel, content),
        )

    repo_config = config.resolve(resolved_slug, repo_type)

    return RepoSnapshot(
        slug=resolved_slug,
        repo_type=repo_type,
        files=files,
        meta_version=meta_version,
        meta_commit=meta_commit,
        config=repo_config,
    )
