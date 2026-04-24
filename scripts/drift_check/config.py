"""Load ``standards/drift-checker.config.json`` (Decision 6).

The config has three tiers (globals, types, repos). ``DriftConfig.resolve``
in ``types.py`` merges them for a given slug/type; this module is just the
loader.

Missing file is not an error — the whole point of the config is to
override defaults, so a missing config yields a permissive empty
``DriftConfig`` with ``signal_policy=same-major-minor``. Malformed JSON
IS an error; the caller (CLI) surfaces that as exit code 2.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .types import DriftConfig


DEFAULT_CONFIG_PATH = Path("standards/drift-checker.config.json")


class ConfigError(Exception):
    """Raised when the config file is present but malformed."""


def load_config(path: Path | None = None) -> DriftConfig:
    """Load a DriftConfig from disk. Missing file -> defaults."""
    p = path if path is not None else DEFAULT_CONFIG_PATH
    if not p.is_file():
        return DriftConfig(
            repos={},
            types={},
            globals={"signal_policy": "same-major-minor"},
        )
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"malformed JSON in {p}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"expected object at root of {p}, got {type(data).__name__}")

    repos = _require_mapping(data.get("repos", {}), "repos", p)
    types_ = _require_mapping(data.get("types", {}), "types", p)
    globals_ = _require_mapping(data.get("globals", {}), "globals", p)

    if "signal_policy" not in globals_:
        globals_ = {**globals_, "signal_policy": "same-major-minor"}

    return DriftConfig(repos=repos, types=types_, globals=globals_)


def _require_mapping(value: object, key: str, path: Path) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ConfigError(f"{path}: '{key}' must be an object, got {type(value).__name__}")
    return value
