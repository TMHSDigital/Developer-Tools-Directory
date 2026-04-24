"""Build a ``RepoSnapshot`` from a local clone or a sparse-checkout.

Session A shipped local-clone mode. Session C adds sparse-checkout for
remote tool repos (CI-mode, where the meta-repo workflow checks every
registered repo without committing 9 full clones to disk).

File discovery is restricted to the four agent-file shapes we care about:

* ``AGENTS.md`` at repo root (optional)
* ``CLAUDE.md`` at repo root (optional)
* every ``skills/<name>/SKILL.md``
* every ``rules/*.mdc``

Plus ``.cursor-plugin/plugin.json`` for repo-type detection (not parsed
into a FileSnapshot since it has no signal).

Sparse-checkout uses git directly via subprocess. The token is injected
into the clone URL ONCE and immediately scrubbed from ``.git/config``
afterwards so it cannot leak via repo state captured to logs or temp
inspection.
"""
from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterator, Optional

from .pragma import extract_pragmas
from .signals import detect_signal
from .types import (
    DriftConfig,
    FileSnapshot,
    RepoSnapshot,
    RepoType,
    Version,
)


# Sparse-checkout target paths. Adding a new path here is the seam for
# Phase 3 if/when the checker grows new file types.
SPARSE_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
    "skills",
    "rules",
    ".cursor-plugin",
)


class RemoteSnapshotError(RuntimeError):
    """Raised when sparse-checkout fails (auth, network, missing repo)."""


def list_meta_standards(meta_repo_path: Path) -> frozenset[str]:
    """Return the set of filenames (relative to ``standards/``) that exist in
    the meta-repo's ``standards/`` directory. Used by ``broken_refs`` to
    resolve ``standards/foo.md`` links.

    Session B ships the local-clone implementation. Session C will add a
    sparse-checkout variant that resolves against a specific meta-repo SHA
    for tool-repo CI runs.
    """
    std_dir = meta_repo_path / "standards"
    if not std_dir.is_dir():
        return frozenset()
    return frozenset(
        p.name for p in std_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".md"
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


def _build_snapshot_from_path(
    repo_path: Path,
    *,
    slug: str,
    meta_version: Version,
    meta_commit: str,
    config: DriftConfig,
    warn_stream,
    meta_standards: frozenset[str],
    meta_required_refs: dict[str, dict[str, list[str]]],
) -> RepoSnapshot:
    """Shared core: turn a directory tree into a ``RepoSnapshot``. Used by
    both ``build_local_snapshot`` and ``build_remote_snapshot`` so both
    callers produce byte-identical snapshots given identical content."""
    repo_type = _detect_repo_type(repo_path)
    if repo_type == "unknown":
        warn_stream.write(
            f"warning: repo {slug} at {repo_path} has no cursor-plugin "
            f"manifest and does not match the mcp-server shape; "
            f"classifying as 'unknown'.\n"
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

    return RepoSnapshot(
        slug=slug,
        repo_type=repo_type,
        files=files,
        meta_version=meta_version,
        meta_commit=meta_commit,
        config=config.resolve(slug, repo_type),
        meta_standards=meta_standards,
        meta_required_refs=meta_required_refs,
    )


def build_local_snapshot(
    repo_path: Path,
    meta_version: Version,
    meta_commit: str,
    config: DriftConfig,
    slug: Optional[str] = None,
    warn_stream=sys.stderr,
    meta_standards: frozenset[str] | None = None,
    meta_required_refs: dict[str, dict[str, list[str]]] | None = None,
) -> RepoSnapshot:
    """Construct a RepoSnapshot by walking the local clone tree.

    ``slug`` defaults to ``repo_path.name`` if not supplied. ``warn_stream``
    is an injection seam for tests that want to capture warnings.
    """
    repo_path = repo_path.resolve()
    if not repo_path.is_dir():
        raise FileNotFoundError(f"repo path is not a directory: {repo_path}")

    return _build_snapshot_from_path(
        repo_path,
        slug=slug or repo_path.name,
        meta_version=meta_version,
        meta_commit=meta_commit,
        config=config,
        warn_stream=warn_stream,
        meta_standards=meta_standards if meta_standards is not None else frozenset(),
        meta_required_refs=meta_required_refs or {},
    )


# ---------------------------------------------------------------------------
# Remote (sparse-checkout) mode
# ---------------------------------------------------------------------------


def _run_git(
    args: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Thin wrapper around git subprocess for testability and uniform
    error handling. Uses ``GIT_TERMINAL_PROMPT=0`` to fail fast on auth
    issues instead of hanging for input."""
    full_env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    if env:
        full_env.update(env)
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        env=full_env,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RemoteSnapshotError(
            f"git {' '.join(args)} failed (rc={result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result


def _scrub_token_from_remote(repo_dir: Path, owner: str, slug: str) -> None:
    """After clone, replace the token-bearing remote URL with a clean one.
    Defense-in-depth: prevents the token from leaking via subsequent ``git
    remote -v`` calls or accidental ``.git/config`` exposure."""
    clean_url = f"https://github.com/{owner}/{slug}.git"
    _run_git(["remote", "set-url", "origin", clean_url], cwd=repo_dir, check=False)


@contextlib.contextmanager
def _sparse_clone(
    owner: str,
    slug: str,
    gh_token: str,
    *,
    branch: str | None = None,
) -> Iterator[Path]:
    """Sparse-checkout the listed ``SPARSE_PATHS`` into a tempdir, yield
    the path, clean up on exit (errors and all)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"drift-{slug}-"))
    try:
        token = gh_token.strip()
        if not token:
            raise RemoteSnapshotError(f"gh_token is empty for {owner}/{slug}")
        clone_url = f"https://x-access-token:{token}@github.com/{owner}/{slug}.git"
        clone_args = [
            "clone",
            "--filter=blob:none",
            "--sparse",
            "--depth", "1",
        ]
        if branch:
            clone_args += ["--branch", branch]
        clone_args += [clone_url, str(tmp)]
        _run_git(clone_args)
        _scrub_token_from_remote(tmp, owner, slug)
        _run_git(["sparse-checkout", "set", *SPARSE_PATHS], cwd=tmp)
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_remote_snapshot(
    repo_slug: str,
    meta_version: Version,
    meta_commit: str,
    config: DriftConfig,
    gh_token: str,
    *,
    owner: str = "TMHSDigital",
    branch: str | None = None,
    warn_stream=sys.stderr,
    meta_standards: frozenset[str] | None = None,
    meta_required_refs: dict[str, dict[str, list[str]]] | None = None,
) -> RepoSnapshot:
    """Sparse-checkout ``owner/repo_slug`` and snapshot it.

    The temp directory is cleaned up before this function returns,
    including on error. The slug embedded in the resulting snapshot is
    ``repo_slug`` exactly (not lowercased; keeps GitHub-canonical case).

    Raises ``RemoteSnapshotError`` if the clone or sparse-checkout fails
    (e.g. auth, network, repo missing). Caller decides whether to log and
    continue with other repos or treat as a tool error.
    """
    with _sparse_clone(owner, repo_slug, gh_token, branch=branch) as repo_path:
        return _build_snapshot_from_path(
            repo_path,
            slug=repo_slug,
            meta_version=meta_version,
            meta_commit=meta_commit,
            config=config,
            warn_stream=warn_stream,
            meta_standards=meta_standards if meta_standards is not None else frozenset(),
            meta_required_refs=meta_required_refs or {},
        )
