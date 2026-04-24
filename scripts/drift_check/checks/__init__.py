"""Registered checks live here.

Session A shipped ``version_signal``. Session B adds ``broken_refs``,
``required_refs``, and ``stale_counts``. Phase 3 will add more via the
same ``Check`` Protocol from ``types.py``.
"""
from .broken_refs import BrokenRefsCheck
from .required_refs import RequiredRefsCheck
from .stale_counts import StaleCountsCheck
from .version_signal import VersionSignalCheck

__all__ = [
    "VersionSignalCheck",
    "BrokenRefsCheck",
    "RequiredRefsCheck",
    "StaleCountsCheck",
]
