"""Release-doc-sync: keep CHANGELOG.md, CLAUDE.md, and ROADMAP.md aligned with
the new plugin.json version after an auto-release.

Public surface is intentionally narrow. The action invokes ``sync.py`` as a
script. Tests import ``sync_repo`` and the per-file helpers directly.
"""

from .sync import (  # noqa: F401
    SyncResult,
    sync_changelog,
    sync_claude,
    sync_repo,
    sync_roadmap,
)
