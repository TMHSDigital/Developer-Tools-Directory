"""Registered checks live here. Session A ships ``version_signal`` only.

Session B will add ``broken_refs``, ``required_refs``, ``stale_counts``.
"""
from .version_signal import VersionSignalCheck

__all__ = ["VersionSignalCheck"]
