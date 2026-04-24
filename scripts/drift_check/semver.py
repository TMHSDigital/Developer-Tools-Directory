"""Version parsing and policy-tier classification.

Decision 1 policy: ``same-major-minor`` — patch bumps are ignored, anything
above patch is drift. The Q7 adjustment makes ``tool_newer`` a ``warn``
rather than an ``info`` — see ``compare_policy``.

This module does NOT map tiers to Finding severity. That is the caller's
job (see ``checks/version_signal.py``). Keeping the mapping out of here
means a future policy (say, ``same-major``) does not have to know about
Finding semantics.
"""
from __future__ import annotations

import re
from typing import Literal, Optional

from .types import Version


PolicyTier = Literal[
    "exact_match",
    "patch_differs",
    "major_minor_differs",
    "tool_newer",
    "malformed",
]


_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


def parse_version(s: str) -> Optional[Version]:
    """Parse a MAJOR.MINOR.PATCH string. Returns None if the input does not
    match. Accepts an optional leading ``v`` and ignores SemVer prerelease /
    build metadata suffixes (we do not use them in this ecosystem)."""
    if not isinstance(s, str):
        return None
    m = _SEMVER_RE.match(s.strip())
    if not m:
        return None
    return Version(
        major=int(m.group(1)),
        minor=int(m.group(2)),
        patch=int(m.group(3)),
        raw=s,
        parsed=True,
    )


def compare_policy(
    tool_version: Optional[Version], meta_version: Version
) -> PolicyTier:
    """Classify the relationship between a tool-repo signal and the
    meta-repo VERSION under the ``same-major-minor`` policy.

    Order of the tests matters: a malformed tool version short-circuits
    before any numeric comparison.
    """
    if tool_version is None or not tool_version.parsed:
        return "malformed"

    if tool_version.as_tuple() == meta_version.as_tuple():
        return "exact_match"

    if tool_version.as_tuple() > meta_version.as_tuple():
        # Tool ahead of meta on any component => warn per Q7.
        return "tool_newer"

    if (tool_version.major, tool_version.minor) == (meta_version.major, meta_version.minor):
        # Same MAJOR.MINOR, tool patch is behind meta patch.
        return "patch_differs"

    return "major_minor_differs"
