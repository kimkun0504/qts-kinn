"""Portfolio construction. The only place where alphas, risk and costs meet.

Weights are fractions of account equity; shorts are negative. Three kinds of company:

- **investable**: in the universe, tradable, with a score and a risk estimate. Free to hold.
- **held but no longer investable**: the target is zero (the position is closed).
- **held but not tradable** (no recent bar): the weight stays as it is and counts against
  every limit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import cvxpy as cp
import numpy as np

from kinn.costs.model import CostModel
from kinn.risk.model import RiskEstimate


@dataclass(frozen=True)
class Limits:
    gross: float = 1.5  # sum of |weights|
    net: float = 0.0  # target sum of weights (0 = dollar neutral)
    net_band: float = 0.02
    max_weight: float = 0.05  # per company, either side
    min_weight: float = 0.01  # smaller targets are dropped
    beta: float | None = 0.05  # |portfolio beta|; None = no limit
    sector: float | None = 0.10  # |net weight| per sector; None = no limit
    long_only: bool = False


@dataclass(frozen=True)
class Inputs:
    """Everything a constructor may use, one entry per company."""

    z: np.ndarray  # combined alpha score; NaN = no view
    risk: RiskEstimate
    current: np.ndarray  # weights held now
    eligible: np.ndarray
    tradable: np.ndarray
    shortable: np.ndarray
    cost: np.ndarray  # one-way cost of trading, as a fraction of the amount traded

    @property
    def investable(self) -> np.ndarray:
        return (
            self.eligible & self.tradable & np.isfinite(self.z)
            & np.isfinite(self.risk.beta) & np.isfinite(self.risk.specific_var)
        )  # fmt: skip

    @property
    def stuck(self) -> np.ndarray:
        return (self.current != 0) & ~self.tradable


class Constructor(Protocol):
    def weights(self, inputs: Inputs, limits: Limits) -> np.ndarray | None:
        """Target weights, or None when no valid portfolio was found (hold what you have)."""


def one_way_cost(costs: CostModel, prices: np.ndarray, trade_value: float) -> np.ndarray:
    """Fees plus auction slippage for a trade of ``trade_value`` dollars, as a fraction."""
    out = np.full(prices.shape, np.nan)
    for j in np.flatnonzero(np.isfinite(prices) & (prices > 0)):
        shares = max(1, int(trade_value / prices[j]))
        value = shares * float(prices[j])
        commission, fees = costs.order_fees(
            side="sell", value=value, marketable=0, passive=0, auction=shares
        )
        slip = costs.auction_slippage(price=float(prices[j]), shares=shares)
        out[j] = (commission + fees + slip) / value
    return out


def _drop_small(target: np.ndarray, inputs: Inputs, limits: Limits) -> np.ndarray:
    small = (np.abs(target) < limits.min_weight) & ~inputs.stuck
    return np.where(small, 0.0, target)


@dataclass(frozen=True)
class MeanVariance:
    """Maximise expected return less a risk penalty less trading costs, under the limits.

    Expected return over the horizon is ``ic * volatility * z`` (Grinold, 1994). Risk is the
    single-index variance over the same horizon. Costs are charged once per rebalance on the
    change in weights, so a small edge does not justify a trade.
    """

    ic: float = 0.03
    risk_aversion: float = 10.0
    horizon_days: int = 21
    cost_multiplier: float = 1.0
    solver: str = "CLARABEL"

    def weights(self, inputs: Inputs, limits: Limits) -> np.ndarray | None:
        investable, stuck = inputs.investable, inputs.stuck
        free = investable | ((inputs.current != 0) & inputs.tradable)
        idx = np.flatnonzero(free)
        target = np.where(stuck, inputs.current, 0.0)
        if idx.size == 0:
            return target
        risk, h = inputs.risk, self.horizon_days
        ok = investable[idx]
        beta = np.where(ok, np.nan_to_num(risk.beta[idx], nan=1.0), 1.0)
        spec = np.nan_to_num(risk.specific_var[idx], nan=float(np.nanmedian(risk.specific_var))) * h
        vol = np.sqrt(np.nan_to_num(risk.total_var[idx]) * h)
        alpha = np.where(ok, self.ic * vol * np.nan_to_num(inputs.z[idx]), 0.0)
        cost = np.nan_to_num(inputs.cost[idx], nan=0.01) * self.cost_multiplier
        upper = np.where(ok, limits.max_weight, 0.0)
        can_short = ok & inputs.shortable[idx] & (not limits.long_only)
        lower = np.where(can_short, -limits.max_weight, 0.0)
        fixed = inputs.current[stuck]
        fixed_beta = float(np.nan_to_num(risk.beta[stuck], nan=1.0) @ fixed)

        w = cp.Variable(idx.size)
        exposure = beta @ w + fixed_beta
        variance = h * risk.market_var * cp.square(exposure) + cp.sum(
            cp.multiply(spec, cp.square(w))
        )
        objective = (
            alpha @ w - 0.5 * self.risk_aversion * variance - cost @ cp.abs(w - inputs.current[idx])
        )
        constraints = [
            w <= upper,
            w >= lower,
            cp.norm1(w) + float(np.abs(fixed).sum()) <= limits.gross,
            cp.abs(cp.sum(w) + float(fixed.sum()) - limits.net) <= limits.net_band,
        ]
        if limits.beta is not None:
            constraints.append(cp.abs(exposure) <= limits.beta)
        if limits.sector is not None:
            sectors = risk.sector[idx]
            for code in np.unique(sectors):
                held = float(inputs.current[stuck & (risk.sector == code)].sum())
                constraints.append(cp.abs(cp.sum(w[sectors == code]) + held) <= limits.sector)
        problem = cp.Problem(cp.Maximize(objective), constraints)
        try:
            problem.solve(solver=self.solver)
        except cp.SolverError:
            return None
        if problem.status not in ("optimal", "optimal_inaccurate") or w.value is None:
            return None
        target[idx] = np.clip(w.value, lower, upper)
        return _drop_small(target, inputs, limits)


@dataclass(frozen=True)
class RankedBook:
    """The textbook construction: equal weights in the best and the worst ``count`` names."""

    count: int = 20

    def weights(self, inputs: Inputs, limits: Limits) -> np.ndarray | None:
        target = np.where(inputs.stuck, inputs.current, 0.0)
        pool = inputs.investable
        order = np.argsort(np.where(pool, inputs.z, np.nan))  # NaN sorts last
        ranked = order[: int(pool.sum())]
        longs = ranked[::-1][: self.count]
        if limits.long_only:
            if longs.size:
                target[longs] = min(limits.gross / longs.size, limits.max_weight)
            return target
        shorts = [j for j in ranked if inputs.shortable[j]][: self.count]
        shorts = [j for j in shorts if j not in set(longs.tolist())]
        if not longs.size or not shorts:
            return target
        side = limits.gross / 2
        target[longs] = min(side / longs.size, limits.max_weight)
        target[shorts] = -min(side / len(shorts), limits.max_weight)
        return target
