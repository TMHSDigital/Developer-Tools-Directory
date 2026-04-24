"""Type contracts for the drift checker (Decision 7 from phase2-design.md).

Everything here is a frozen dataclass or a Protocol. No logic. This is the
boundary the rest of Session A and every future ``Check`` (Phase 3) builds
against. Changing anything in this file is a breaking change for plugin
authors; treat it like an API.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Iterable,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    runtime_checkable,
)


Severity = Literal["error", "warn", "info"]
RepoType = Literal["cursor-plugin", "mcp-server", "unknown"]
SignalFormat = Literal["html-comment", "yaml-frontmatter"]
PragmaFormat = Literal["html-comment", "yaml-short", "yaml-long"]


@dataclass(frozen=True)
class Version:
    """Parsed MAJOR.MINOR.PATCH. ``raw`` is the original string (may include
    leading ``v``). ``parsed`` is True only when all three components were
    valid non-negative integers.
    """

    major: int
    minor: int
    patch: int
    raw: str
    parsed: bool = True

    def as_tuple(self) -> Tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class SignalResult:
    """A standards-version marker located in a file.

    ``version`` is None when the marker was present at the correct position
    but did not parse (malformed). The ``format`` and position fields are
    populated even for malformed signals, so the caller can report *where*
    the problem lives.
    """

    version: Optional[Version]
    format: SignalFormat
    line: int
    raw_value: str
    malformed: bool = False


@dataclass(frozen=True)
class Pragma:
    """A ``drift-ignore`` directive found in a file."""

    check_name: str
    reason: Optional[str]
    format: PragmaFormat
    line: int


@dataclass(frozen=True)
class FileSnapshot:
    path: Path
    content: bytes
    signal: Optional[SignalResult]
    pragmas: Sequence[Pragma] = field(default_factory=tuple)


@dataclass(frozen=True)
class RepoConfig:
    """Resolved per-repo config view (globals merged with type then repo).

    ``skip_checks`` is the union of all three tiers' skip lists. Other
    fields come from the effective ``globals`` tier.
    """

    slug: str
    repo_type: RepoType
    skip_checks: frozenset[str] = frozenset()
    signal_policy: str = "same-major-minor"


@dataclass(frozen=True)
class DriftConfig:
    """The full loaded drift-checker config. Use ``resolve()`` to get the
    effective view for one repo. Kept separate from RepoConfig so one load
    can serve N repos.
    """

    repos: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    types: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    globals: Mapping[str, object] = field(default_factory=dict)

    def resolve(self, slug: str, repo_type: RepoType) -> RepoConfig:
        """Merge globals -> type -> repo. Later layers override scalars and
        extend ``skip_checks``."""
        skip: set[str] = set()
        signal_policy = str(self.globals.get("signal_policy", "same-major-minor"))

        for tier in (self.globals, self.types.get(repo_type, {}), self.repos.get(slug, {})):
            if not isinstance(tier, Mapping):
                continue
            tier_skips = tier.get("skip_checks", [])
            if isinstance(tier_skips, list):
                skip.update(str(x) for x in tier_skips)
            if "signal_policy" in tier:
                signal_policy = str(tier["signal_policy"])

        return RepoConfig(
            slug=slug,
            repo_type=repo_type,
            skip_checks=frozenset(skip),
            signal_policy=signal_policy,
        )


@dataclass(frozen=True)
class RepoSnapshot:
    slug: str
    repo_type: RepoType
    files: Mapping[Path, FileSnapshot]
    meta_version: Version
    meta_commit: str
    config: RepoConfig
    # Meta-repo facts captured at snapshot time. ``meta_standards`` is the
    # set of filenames under ``standards/`` (relative, no leading path) as
    # observed by the snapshot builder. Consumed by ``broken_refs`` and
    # ``required_refs``. Empty means "unknown" — Session C will populate
    # this in remote mode via sparse-checkout.
    meta_standards: frozenset[str] = frozenset()
    meta_required_refs: Mapping[str, Mapping[str, Sequence[str]]] = field(default_factory=dict)


@dataclass(frozen=True)
class Finding:
    repo: str
    file: Optional[Path]
    check: str
    severity: Severity
    message: str
    suggested_fix: Optional[str] = None


@runtime_checkable
class Check(Protocol):
    """Every check registers a stable ``name`` (used in pragmas and skip
    lists) and yields Findings from ``run``. Must be side-effect free."""

    name: str

    def run(self, snapshot: RepoSnapshot) -> Iterable[Finding]: ...
