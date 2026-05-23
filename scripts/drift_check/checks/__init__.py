"""Registered checks live here.

Session A shipped ``version_signal``. Session B adds ``broken_refs``,
``required_refs``, and ``stale_counts``. ``required_workflows`` was added
in v1.10.0.
"""
from .broken_refs import BrokenRefsCheck
from .required_refs import RequiredRefsCheck
from .required_workflows import RequiredWorkflowsCheck
from .stale_counts import StaleCountsCheck
from .version_signal import VersionSignalCheck

__all__ = [
    "VersionSignalCheck",
    "BrokenRefsCheck",
    "RequiredRefsCheck",
    "RequiredWorkflowsCheck",
    "StaleCountsCheck",
]
