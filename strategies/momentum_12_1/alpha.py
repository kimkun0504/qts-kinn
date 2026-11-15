"""12-month momentum, skipping the latest month (Jegadeesh and Titman, 1993)."""

from __future__ import annotations

import numpy as np

from kinn.data.daily import DailyView


class Momentum:
    name = "momentum_12_1"

    def __init__(self, formation: int = 252, skip: int = 21, min_obs: int = 200):
        self.formation, self.skip, self.min_obs = formation, skip, min_obs
        self.lookback = formation

    def scores(self, view: DailyView) -> np.ndarray:
        """Total log return over sessions t-formation .. t-skip-1. NaN with too little history."""
        r = view.history("ret", self.formation).astype(np.float64)
        if len(r) < self.formation:
            return np.full(r.shape[1], np.nan)
        window = r[: self.formation - self.skip]
        ok = np.isfinite(window)
        total = np.where(ok, np.log1p(np.clip(window, -0.99, None)), 0.0).sum(axis=0)
        return np.where(ok.sum(axis=0) >= self.min_obs, total, np.nan)


def build(params: dict) -> Momentum:
    return Momentum(**params)
