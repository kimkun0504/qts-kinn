"""Train/test splits over sessions: walk-forward and purged, embargoed K-fold."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date


def walk_forward(
    sessions: Sequence[date], *, train: int, test: int, step: int | None = None
) -> list[tuple[list[date], list[date]]]:
    """Rolling windows: ``train`` sessions, then the next ``test`` sessions, moved by ``step``."""
    step = step or test
    out = []
    start = 0
    while start + train + test <= len(sessions):
        out.append(
            (list(sessions[start : start + train]),
             list(sessions[start + train : start + train + test]))
        )  # fmt: skip
        start += step
    return out


def purged_kfold(
    sessions: Sequence[date], *, folds: int, purge: int = 0, embargo: int = 0
) -> list[tuple[list[date], list[date]]]:
    """K contiguous test folds. Training drops ``purge`` sessions before each test fold (labels
    that overlap it) and ``embargo`` sessions after it (serial correlation)."""
    n = len(sessions)
    bounds = [round(n * k / folds) for k in range(folds + 1)]
    out = []
    for k in range(folds):
        a, b = bounds[k], bounds[k + 1]
        train = [sessions[i] for i in range(n) if i < a - purge or i >= b + embargo]
        out.append((train, list(sessions[a:b])))
    return out
