"""Signals to trades, under one set of rules for every algorithm (decision 0023).

- A signal on row *t* buys at the open of *t+1*, if the stock is eligible that morning (the
  universe test uses only the previous close's figures) and trades. One position per stock.
- Exits, first come: at an open, the owner's exit signal from the day before or a gap through
  the stop or the target (filled at the open); during the day the stop, then the target (filled
  at their price; both touched counts as the stop); the close of the hold-th session; the last
  close if the stock stops trading.
- Prices are compared in split-adjusted terms, so a split in the hold is not a loss.
- Costs from the platform's cost model on the real share count: commission and fees both ways,
  the auction allowance at the open and close, the half-spread on stop and target fills; 1× and
  2× slippage.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from kinn.costs.model import CostModel
from kinn.lab.settings import Settings

REASONS = ("hold", "stop", "target", "exit signal", "stopped trading", "data end")
HOLD, STOP, TARGET, EXIT_SIGNAL, STOPPED, DATA_END = range(6)


@dataclass
class Market:
    """The arrays the simulator needs, all sessions × stocks."""

    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    adj_close: np.ndarray
    eligible: np.ndarray
    adv: np.ndarray
    dollar_volume: np.ndarray
    universe_return: np.ndarray  # one value per session: close to close
    universe_intraday: np.ndarray  # one value per session: open to close

    def __post_init__(self) -> None:
        log = np.log1p(np.nan_to_num(self.universe_return.astype(np.float64), nan=0.0))
        self.universe_cum = np.cumsum(log)

    # Split adjustment is worked out where it is needed, one stock and a few rows at a time,
    # rather than held as more full-size arrays.
    def factor(self, rows: slice | int, n: int):
        """adj_close ÷ close: turns a price as traded into split-adjusted terms."""
        close = self.close[rows, n]
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(close > 0, self.adj_close[rows, n] / close, np.nan)

    def adjusted(self, field: np.ndarray, rows: slice | int, n: int):
        return field[rows, n] * self.factor(rows, n)

    def enterable(self, row: int) -> np.ndarray:
        """Stocks a position can open in at this row's open."""
        with np.errstate(invalid="ignore"):
            return (
                self.eligible[row] & (self.open[row] > 0) & (self.close[row] > 0)
                & np.isfinite(self.adj_close[row])
            )  # fmt: skip


@dataclass
class Trade:
    stock: int
    signal_row: int
    entry_row: int
    exit_row: int
    reason: int
    entry_price: float  # as traded that day
    exit_price: float  # as traded that day
    shares: int
    value: float  # dollars bought
    gross: float
    net: float
    net_2x: float
    cost_entry: float  # dollars, 1x
    cost_exit: float
    benchmark: float  # the universe's equal-weight return over the same sessions
    priority: float


def _first_exit(m: Market, n: int, e: int, hold: int, stop: float | None, target: float | None,
                exits: np.ndarray | None) -> tuple[int, float, int, bool, bool]:  # fmt: skip
    """(exit row, split-adjusted exit price, reason, filled in an auction?, at the open?) for a
    position in stock ``n`` bought at the open of row ``e``."""
    rows = len(m.close)
    end = min(e + hold, rows)
    span = slice(e, end)
    f = m.factor(span, n)
    o = m.open[span, n] * f
    h = m.high[span, n] * f
    lo = m.low[span, n] * f
    c = m.adj_close[span, n]
    entry = float(o[0])
    stop_level = entry * (1 - stop) if stop else -math.inf
    target_level = entry * (1 + target) if target else math.inf
    valid = np.isfinite(c)
    k = np.arange(end - e)
    at_open = np.zeros(end - e, dtype=bool)
    if exits is not None:
        at_open[1:] = exits[e : end - 1, n]
    gap_stop = (k > 0) & (o <= stop_level)
    gap_target = (k > 0) & (o >= target_level)
    open_exit = valid & np.isfinite(o) & (at_open | gap_stop | gap_target)
    stop_hit = valid & (lo <= stop_level)
    target_hit = valid & (h >= target_level)
    any_exit = open_exit | stop_hit | target_hit
    if any_exit.any():
        i = int(np.argmax(any_exit))
        if open_exit[i]:
            reason = EXIT_SIGNAL if at_open[i] else STOP if gap_stop[i] else TARGET
            return e + i, float(o[i]), reason, True, True
        if stop_hit[i]:
            return e + i, float(stop_level), STOP, False, False
        return e + i, float(target_level), TARGET, False, False
    if end == e + hold:
        last = e + hold - 1
        if np.isfinite(m.adj_close[last, n]):
            return last, float(m.adj_close[last, n]), HOLD, True, False
    # The window is cut short (the data ends) or the stock has no price at the end of the hold.
    later = np.flatnonzero(np.isfinite(m.adj_close[e:, n]))
    after_hold = later[later >= hold - 1] if end == e + hold else np.array([], dtype=int)
    if after_hold.size:  # it trades again later: sell at the first close after the hold
        x = e + int(after_hold[0])
        return x, float(m.adj_close[x, n]), HOLD, True, False
    x = e + int(later[-1]) if later.size else e
    price = float(m.adj_close[x, n]) if later.size else entry
    reason = DATA_END if end < e + hold and later.size and e + later[-1] >= rows - 1 else STOPPED
    return x, price, reason, True, False


class Costs:
    """Per-trade costs from the platform's cost model, in dollars."""

    def __init__(self, model: CostModel) -> None:
        self.model = model

    def side(self, *, side: str, price: float, value: float, adv: float, auction: bool,
             forced: bool = False) -> tuple[float, float]:  # fmt: skip
        """(fees and commission, slippage at 1×) for one order."""
        shares = max(int(round(value / price)), 1) if price > 0 else 1
        if auction:
            commission, fees = self.model.order_fees(side=side, value=value, marketable=0,
                                                     passive=0, auction=shares)  # fmt: skip
            slippage = self.model.auction_slippage(price=price, shares=shares, forced=forced)
        else:
            commission, fees = self.model.order_fees(side=side, value=value, marketable=shares,
                                                     passive=0, auction=0)  # fmt: skip
            slippage = self.model.half_spread_bps(price, adv) / 1e4 * value
        return commission + fees, slippage


def _trade(m: Market, costs: Costs, n: int, t: int, hold: int, stop, target, exits,
           size: float, priority: float) -> Trade:  # fmt: skip
    e = t + 1
    x, exit_adj, reason, auction, at_open = _first_exit(m, n, e, hold, stop, target, exits)
    entry_price = float(m.open[e, n])
    entry_adj = float(m.adjusted(m.open, e, n))
    shares = max(int(size // entry_price), 1)
    value = shares * entry_price
    gross = exit_adj / entry_adj - 1
    factor = float(m.factor(x, n))
    exit_price = exit_adj / factor if math.isfinite(factor) and factor > 0 else exit_adj
    exit_value = value * (1 + gross)
    adv = float(m.adv[e, n]) if np.isfinite(m.adv[e, n]) else float("nan")
    fee_in, slip_in = costs.side(side="buy", price=entry_price, value=value, adv=adv, auction=True)
    fee_out, slip_out = costs.side(side="sell", price=exit_price, value=max(exit_value, 0.01),
                                   adv=adv, auction=auction, forced=reason == STOPPED)  # fmt: skip
    cost_1x = fee_in + slip_in + fee_out + slip_out
    cost_2x = cost_1x + slip_in + slip_out
    # The universe over the same span: from the entry open to the exit (the open or the close).
    intraday = float(m.universe_intraday[e]) if np.isfinite(m.universe_intraday[e]) else 0.0
    end = x - 1 if at_open else x
    benchmark = (1 + intraday) * math.exp(m.universe_cum[max(end, e)] - m.universe_cum[e]) - 1
    return Trade(n, t, e, x, reason, entry_price, exit_price, shares, value, gross,
                 gross - cost_1x / value, gross - cost_2x / value, fee_in + slip_in,
                 fee_out + slip_out, benchmark, priority)  # fmt: skip


def _can_enter(m: Market, n: int, e: int) -> bool:
    if not m.eligible[e, n]:
        return False
    price, close = float(m.open[e, n]), float(m.close[e, n])
    return price > 0 and close > 0 and math.isfinite(float(m.adj_close[e, n]))


def simulate(m: Market, entries: np.ndarray, exits: np.ndarray | None, settings: Settings,
             costs: Costs, first_row: int, last_signal_row: int,
             progress=None) -> list[Trade]:  # fmt: skip
    """Every trade the signals make, one position per stock at a time."""
    hold, stop, target = settings.exit.hold_days, settings.exit.stop_loss, settings.exit.take_profit
    size = settings.book.position_size
    rows, stocks = entries.shape
    last = min(last_signal_row, rows - 2)
    trades: list[Trade] = []
    if settings.entry.mode == "rank":
        busy = np.full(stocks, -1)
        sign = -1.0 if settings.entry.rank_order == "highest" else 1.0
        top = settings.entry.top_n
        for t in range(first_row, last + 1):
            if progress and (t - first_row) % 100 == 0:
                progress((t - first_row) / max(last - first_row, 1))
            score = entries[t]
            ok = np.isfinite(score) & m.enterable(t + 1) & (busy < t + 1)
            candidates = np.flatnonzero(ok)
            if not candidates.size:
                continue
            order = np.argsort(sign * score[candidates], kind="stable")[:top]
            for n in candidates[order]:
                trade = _trade(m, costs, int(n), t, hold, stop, target, exits, size,
                               float(score[n]) * -sign)  # fmt: skip
                busy[n] = trade.exit_row
                trades.append(trade)
        return trades
    window = entries[first_row : last + 1]
    columns = np.flatnonzero(window.any(axis=0))
    for count, n in enumerate(columns):
        if progress and count % 200 == 0:
            progress(count / max(len(columns), 1))
        fired = np.flatnonzero(window[:, n]) + first_row
        free = 0  # the first row a new position may open
        i = 0
        while i < len(fired):
            t = int(fired[i])
            e = t + 1
            if e < free:
                i = int(np.searchsorted(fired, free - 1))
                continue
            if _can_enter(m, n, e):
                traded = m.dollar_volume[t, n]
                priority = float(traded) if np.isfinite(traded) else 0.0
                trade = _trade(m, costs, int(n), t, hold, stop, target, exits, size, priority)
                trades.append(trade)
                free = trade.exit_row + 1
            i += 1
    trades.sort(key=lambda tr: (tr.entry_row, -tr.priority, tr.stock))
    return trades
