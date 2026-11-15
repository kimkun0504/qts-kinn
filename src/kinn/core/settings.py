"""Where Kinn reads and writes. Every path comes from here; no other module hard-codes one.

Environment variables (prefix ``KINN_``):

- ``KINN_RAW_DIR``   vendor data, read-only.
- ``KINN_DATA_DIR``  derived data that Kinn builds.
- ``KINN_RUNS_DIR``  run outputs, one folder per run.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path

# Fixed by decision 0002. Not configurable: there is deliberately no environment variable for it.
HOLDOUT_START = date(2023, 11, 9)

ENV_PREFIX = "KINN_"

# src/kinn/core/settings.py -> repository (or worktree) root.
_REPO_ROOT = Path(__file__).resolve().parents[3]

_DEFAULT_RAW_DIR = "~/Desktop/QTS/MarketData/raw"
_DEFAULT_DATA_DIR = "~/Desktop/QTS/MarketData/processed/kinn"


class SettingsError(ValueError):
    """A configured path breaks a ground rule."""


@dataclass(frozen=True)
class Settings:
    raw_dir: Path
    data_dir: Path
    runs_dir: Path


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _is_within(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Read settings from ``env`` (default: the process environment) and check the ground rules."""
    env = os.environ if env is None else env

    raw_dir = _path(env.get("KINN_RAW_DIR") or _DEFAULT_RAW_DIR)
    data_dir = _path(env.get("KINN_DATA_DIR") or _DEFAULT_DATA_DIR)
    # The repo and its worktrees share one parent folder, so they share one run store.
    runs_dir = _path(env.get("KINN_RUNS_DIR") or str(_REPO_ROOT.parent / "runs"))

    for name, path in (
        ("KINN_RAW_DIR", raw_dir),
        ("KINN_DATA_DIR", data_dir),
        ("KINN_RUNS_DIR", runs_dir),
    ):
        if "sealed" in path.parts:
            raise SettingsError(f"{name} points into a sealed (holdout) folder: {path}")

    for name, path in (("KINN_DATA_DIR", data_dir), ("KINN_RUNS_DIR", runs_dir)):
        if _is_within(path, raw_dir):
            raise SettingsError(f"{name} is inside the read-only raw folder: {path}")

    return Settings(raw_dir=raw_dir, data_dir=data_dir, runs_dir=runs_dir)
