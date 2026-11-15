"""The alpha contract and how several alphas become one score.

An alpha returns one number per company for a session: higher means more attractive, NaN means
no opinion. It sees only a :class:`~kinn.data.daily.DailyView`, so it cannot use that session's
prices. Scores from different alphas are put on one scale (a cross-sectional z-score) before
they are weighted and added; that is the only place alphas meet.
"""

from __future__ import annotations

from typing import Protocol

import numpy as np

from kinn.data.daily import DailyData, DailyView


class Alpha(Protocol):
    name: str
    lookback: int  # sessions of history the alpha reads

    def scores(self, view: DailyView) -> np.ndarray: ...


class LookaheadError(AssertionError):
    """An alpha's scores changed when the session's own outcomes were hidden."""


def zscore(values: np.ndarray, mask: np.ndarray, *, clip: float = 3.0) -> np.ndarray:
    """Standardise ``values`` across the companies in ``mask``; NaN elsewhere."""
    out = np.full(values.shape, np.nan)
    use = mask & np.isfinite(values)
    if use.sum() < 2:
        return out
    picked = values[use].astype(np.float64)
    spread = picked.std()
    if spread == 0:
        return out
    out[use] = np.clip((picked - picked.mean()) / spread, -clip, clip)
    return out


def combine(alphas: list[tuple[Alpha, float]], view: DailyView) -> np.ndarray:
    """The weighted sum of each alpha's z-score, re-standardised. NaN where no alpha has a view."""
    mask = view.eligible
    total = np.zeros(mask.shape)
    seen = np.zeros(mask.shape, dtype=bool)
    for alpha, weight in alphas:
        z = zscore(np.asarray(alpha.scores(view), dtype=np.float64), mask)
        has = np.isfinite(z)
        total[has] += weight * z[has]
        seen |= has
    return zscore(np.where(seen, total, np.nan), mask)


def check_no_lookahead(
    alphas: list[tuple[Alpha, float]], data: DailyData, i: int, scores: np.ndarray, lookback: int
) -> None:
    """Recompute the combined score from a copy of the data with session ``i``'s outcomes
    erased. Any difference means an alpha read something it could not have known."""
    window = data.window(i, lookback)
    replay = combine(alphas, window.view(len(window.dates) - 1))
    if not np.allclose(scores, replay, equal_nan=True, rtol=1e-9, atol=1e-12):
        raise LookaheadError(f"scores for {data.dates[i]} depend on that session's own data")
