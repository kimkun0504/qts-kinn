"""The daily engine. One session at a time, in this order:

1. Corporate actions: splits change share counts, dividends move cash (shorts pay them).
2. Shorts pay the borrow fee for the day.
3. Positions in companies with no bar for ``stale_sessions`` sessions are closed at their last
   price with the forced-exit cost (a delisting or a long halt).
4. On a rebalance day: alphas score, the risk model estimates, the constructor sets target
   weights, execution sizes the orders. All of it uses only what was known before the open.
5. Orders fill in the auction at that session's open or close and pay the cost model.
6. The book is marked at the close.

Slippage is charged in cash at 1x. The 2x result subtracts the same slippage again from each
day's P&L; it does not re-size the book, so it slightly understates the damage.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from kinn.alpha.base import Alpha, check_no_lookahead, combine
from kinn.core.types import BookFill
from kinn.costs.model import CostModel
from kinn.data.daily import DailyData
from kinn.execution.auction import AuctionExecution
from kinn.portfolio.construct import Constructor, Inputs, Limits, one_way_cost
from kinn.risk.model import SingleIndexRisk

SESSIONS_PER_YEAR = 252


@dataclass(frozen=True)
class BookConfig:
    account: float = 25_000.0
    rebalance: str | int = "monthly"  # "daily" | "weekly" | "monthly" | every N sessions
    borrow_rate: float = 0.01  # a year, on the market value of shorts
    short_min_marketcap: float = 1e9
    short_min_price: float = 5.0
    # Rebalance early when gross exposure at the last close is above this (a multiple of
    # equity). Prices move between rebalances; a falling book's exposure rises. None = never.
    rebalance_if_gross_above: float | None = None
    stale_sessions: int = 5
    lookahead_check_rate: float = 0.25
    seed: int = 0


@dataclass
class BookState:
    cash: float
    shares: np.ndarray
    last_price: np.ndarray
    stale: np.ndarray

    @classmethod
    def fresh(cls, account: float, n: int) -> BookState:
        return cls(account, np.zeros(n), np.full(n, np.nan), np.zeros(n, dtype=np.int64))

    def equity(self) -> float:
        held = self.shares != 0
        return self.cash + float((self.shares[held] * self.last_price[held]).sum())

    def to_dict(self, permatickers: np.ndarray) -> dict:
        held = np.flatnonzero(self.shares != 0)
        return {
            "cash": self.cash,
            "positions": {
                str(int(permatickers[j])): [
                    float(self.shares[j]), float(self.last_price[j]), int(self.stale[j])
                ]
                for j in held
            },
        }  # fmt: skip

    @classmethod
    def from_dict(cls, payload: dict, data: DailyData, i: int) -> BookState:
        """Rebuild the state as it stood before session ``i``."""
        n = len(data.permatickers)
        state = cls.fresh(payload["cash"], n)
        if i > 0:
            closes = data.close[:i]
            seen = np.isfinite(closes)
            last = np.where(seen.any(axis=0), i - 1 - np.argmax(seen[::-1], axis=0), -1)
            state.last_price = np.where(last >= 0, closes[last, np.arange(n)], np.nan)
            state.stale = np.where(last >= 0, i - 1 - last, 0).astype(np.int64)
        for key, (shares, price, stale) in payload["positions"].items():
            j = int(np.searchsorted(data.permatickers, int(key)))
            if j >= n or data.permatickers[j] != int(key):
                raise KeyError(f"held company {key} is missing from the loaded data")
            state.shares[j], state.last_price[j], state.stale[j] = shares, price, stale
        return state


@dataclass
class SessionsResult:
    daily: list[dict] = field(default_factory=list)
    fills: list[BookFill] = field(default_factory=list)
    positions: list[dict] = field(default_factory=list)
    counts: dict[str, int] = field(
        default_factory=lambda: dict.fromkeys(
            (
                "rebalances",
                "early_rebalances",
                "no_portfolio",
                "lookahead_checks",
                "forced_exits",
            ),
            0,
        )
    )


@dataclass
class DailyEngine:
    data: DailyData
    alphas: list[tuple[Alpha, float]]
    risk_model: SingleIndexRisk
    constructor: Constructor
    execution: AuctionExecution
    limits: Limits
    costs: CostModel
    config: BookConfig
    start_index: int  # first session of the run (earlier rows are history only)

    @property
    def lookback(self) -> int:
        return max([self.risk_model.lookback] + [a.lookback for a, _ in self.alphas]) + 1

    def is_rebalance(self, i: int) -> bool:
        rule, dates = self.config.rebalance, self.data.dates
        if i == self.start_index or rule == "daily":
            return True
        if rule == "monthly":
            return dates[i].month != dates[i - 1].month
        if rule == "weekly":
            return dates[i].isocalendar()[:2] != dates[i - 1].isocalendar()[:2]
        return (i - self.start_index) % int(rule) == 0

    def run(self, state: BookState, lo: int, hi: int) -> SessionsResult:
        """Simulate sessions ``[lo, hi)``, changing ``state`` in place."""
        result = SessionsResult()
        for i in range(lo, hi):
            self._session(i, state, result)
        return result

    # -- one session ---------------------------------------------------------------------
    def _session(self, i: int, state: BookState, result: SessionsResult) -> None:
        d, cfg = self.data, self.config
        day = d.dates[i]
        equity_before = state.equity()
        split = d.split[i].astype(np.float64)
        changed = (state.shares != 0) & np.isfinite(split) & (split > 0) & (split != 1)
        state.shares[changed] = np.round(state.shares[changed] * split[changed])
        with np.errstate(invalid="ignore"):
            state.last_price = np.where(
                np.isfinite(split) & (split > 0), state.last_price / split, state.last_price
            )
        start_shares, start_price = state.shares.copy(), state.last_price.copy()
        per_share = np.nan_to_num(d.dividend[i].astype(np.float64))
        dividends = float((state.shares * per_share).sum())
        short_value = float(-(np.minimum(state.shares, 0) * np.nan_to_num(state.last_price)).sum())
        borrow = short_value * cfg.borrow_rate / SESSIONS_PER_YEAR
        state.cash += dividends - borrow

        tradable = state.stale == 0  # had a bar in the previous session
        close = d.close[i]
        has_bar = np.isfinite(close)
        state.stale = np.where(has_bar, 0, state.stale + 1)
        cost = {"commission": 0.0, "fees": 0.0, "slippage": 0.0}
        traded = 0.0
        for j in np.flatnonzero((state.shares != 0) & (state.stale >= cfg.stale_sessions)):
            traded += self._fill(
                state, result, cost, day, j, -state.shares[j], state.last_price[j], "delisted"
            )
            result.counts["forced_exits"] += 1

        rebalanced = False
        over = cfg.rebalance_if_gross_above
        runaway = (
            over is not None
            and equity_before > 0
            and float(np.abs(state.shares * np.nan_to_num(state.last_price)).sum())
            > over * equity_before
        )
        if runaway:
            result.counts["early_rebalances"] += 1
        if (self.is_rebalance(i) or runaway) and equity_before > 0:
            target = self._targets(i, state, equity_before, tradable, result)
            if target is not None:
                rebalanced = True
                delta = self.execution.orders(
                    target=target, shares=state.shares, equity=equity_before,
                    ref_price=d.prev_close[i], adv=d.adv_prev[i], tradable=tradable,
                )  # fmt: skip
                price = d.open[i] if self.execution.at == "open" else close
                for j in np.flatnonzero((delta != 0) & np.isfinite(price)):
                    traded += self._fill(
                        state, result, cost, day, j, delta[j], float(price[j]), "rebalance"
                    )
        state.last_price = np.where(has_bar, close, state.last_price)

        equity = state.equity()
        move = np.nan_to_num(state.last_price - start_price)
        long_pnl = float((np.maximum(start_shares, 0) * (move + per_share)).sum())
        short_pnl = float((np.minimum(start_shares, 0) * (move + per_share)).sum())
        value = state.shares * np.nan_to_num(state.last_price)
        pnl = equity - equity_before
        result.daily.append({
            "date": day, "equity": equity, "pnl": pnl, "pnl_2x": pnl - cost["slippage"],
            "long_pnl": long_pnl, "short_pnl": short_pnl, "dividends": dividends,
            "borrow": borrow, "commission": cost["commission"], "fees": cost["fees"],
            "slippage": cost["slippage"], "long_value": float(value[value > 0].sum()),
            "short_value": float(-value[value < 0].sum()),
            "n_long": int((state.shares > 0).sum()), "n_short": int((state.shares < 0).sum()),
            "traded": traded, "rebalanced": rebalanced,
        })  # fmt: skip
        if rebalanced or i == len(d.dates) - 1:
            for j in np.flatnonzero(state.shares != 0):
                result.positions.append({
                    "date": day, "permaticker": int(d.permatickers[j]), "symbol": d.symbols[j],
                    "sector": d.sector_names[d.sector[j]], "shares": float(state.shares[j]),
                    "price": float(state.last_price[j]), "value": float(value[j]),
                    "weight": float(value[j] / equity) if equity > 0 else 0.0,
                })  # fmt: skip

    def _targets(self, i, state, equity, tradable, result) -> np.ndarray | None:
        d, cfg = self.data, self.config
        view = d.view(i)
        z = combine(self.alphas, view)
        if not np.isfinite(z).any():
            return None
        rng = random.Random(f"{cfg.seed}:{d.dates[i].isoformat()}")
        if rng.random() < cfg.lookahead_check_rate:
            check_no_lookahead(self.alphas, d, i, z, self.lookback)
            result.counts["lookahead_checks"] += 1
        prev_close = d.prev_close[i]
        shortable = (
            view.eligible
            & (np.nan_to_num(d.marketcap_prev[i]) >= cfg.short_min_marketcap)
            & (np.nan_to_num(prev_close) >= cfg.short_min_price)
        )
        current = state.shares * np.nan_to_num(state.last_price) / equity
        inputs = Inputs(
            z=z, risk=self.risk_model.estimate(view), current=current, eligible=view.eligible,
            tradable=tradable, shortable=shortable,
            cost=one_way_cost(self.costs, prev_close, self.limits.max_weight * equity),
        )  # fmt: skip
        result.counts["rebalances"] += 1
        target = self.constructor.weights(inputs, self.limits)
        if target is None:
            result.counts["no_portfolio"] += 1
        return target

    def _fill(self, state, result, cost, day, j, quantity, price, reason) -> float:
        """Trade ``quantity`` (signed) shares at ``price``. Returns the dollars traded."""
        shares = int(abs(quantity))
        value = shares * price
        side = "buy" if quantity > 0 else "sell"
        commission, fees = self.costs.order_fees(
            side=side, value=value, marketable=0, passive=0, auction=shares
        )
        slippage = self.costs.auction_slippage(
            price=price, shares=shares, forced=reason == "delisted"
        )
        state.cash -= quantity * price + commission + fees + slippage
        state.shares[j] += quantity
        cost["commission"] += commission
        cost["fees"] += fees
        cost["slippage"] += slippage
        result.fills.append(
            BookFill(
                day=day, permaticker=int(self.data.permatickers[j]), symbol=self.data.symbols[j],
                shares=float(quantity), price=price, value=value, commission=commission,
                fees=fees, slippage=slippage, reason=reason,
            )
        )  # fmt: skip
        return value
