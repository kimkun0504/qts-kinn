"""The risk model: how risky each stock is and how stocks move together.

Version 1 is the single-index model (Sharpe, 1963): each stock's return is its beta times the
market's return plus its own noise, so covariance = beta beta' * market variance + a diagonal.
It is the simplest model that lets an optimizer control market exposure; sector exposure is
controlled by limits. A multi-factor model replaces this class when a book needs one.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from kinn.data.daily import DailyView


@dataclass(frozen=True)
class RiskEstimate:
    """Daily units. NaN where a company has too little history."""

    beta: np.ndarray
    specific_var: np.ndarray
    total_var: np.ndarray
    market_var: float
    sector: np.ndarray


@dataclass(frozen=True)
class SingleIndexRisk:
    window: int = 252
    min_obs: int = 126
    beta_shrink: float = 1 / 3  # toward 1 (Blume, 1971)

    @property
    def lookback(self) -> int:
        return self.window

    def estimate(self, view: DailyView) -> RiskEstimate:
        r = view.history("ret", self.window).astype(np.float64)
        cap = np.where(view.eligible, np.nan_to_num(view.today("marketcap_prev")), 0.0)
        ok = np.isfinite(r)
        weight = ok * cap
        total = weight.sum(axis=1)
        with np.errstate(invalid="ignore", divide="ignore"):
            market = (np.where(ok, r, 0.0) * cap).sum(axis=1) / np.where(total > 0, total, np.nan)
            valid = ok & np.isfinite(market)[:, None]
            n = valid.sum(axis=0).astype(np.float64)
            m = np.where(np.isfinite(market), market, 0.0)[:, None]
            mean_r = np.where(valid, r, 0.0).sum(axis=0) / n
            mean_m = (valid * m).sum(axis=0) / n
            dr = np.where(valid, r - mean_r, 0.0)
            dm = np.where(valid, m - mean_m, 0.0)
            var_m = (dm**2).sum(axis=0) / (n - 1)
            raw = (dr * dm).sum(axis=0) / (n - 1) / var_m
            specific = ((dr - raw * dm) ** 2).sum(axis=0) / (n - 2)
            total_var = (dr**2).sum(axis=0) / (n - 1)
        thin = (n < self.min_obs) | ~np.isfinite(raw) | ~(specific > 0)
        beta = np.where(thin, np.nan, (1 - self.beta_shrink) * raw + self.beta_shrink)
        specific = np.where(thin, np.nan, specific)
        if np.isfinite(specific).any():
            specific = np.maximum(specific, np.nanpercentile(specific, 5))
        market_var = float(np.nanvar(market, ddof=1)) if np.isfinite(market).sum() > 1 else np.nan
        return RiskEstimate(
            beta=beta, specific_var=specific, total_var=np.where(thin, np.nan, total_var),
            market_var=market_var, sector=view.sector,
        )  # fmt: skip
