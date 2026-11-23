"""The book: a fixed amount a position and at most N open at once, marked to market daily."""

from __future__ import annotations

import heapq

import numpy as np

from kinn.lab.engine import Market, Trade


def select(trades: list[Trade], cap: int) -> np.ndarray:
    """Which trades the book takes. Trades come ordered by entry day, then priority (the score
    in ranking mode, the signal day's dollar volume otherwise). A position occupies its slot
    from its entry session through its exit session. Longs and shorts have a cap each."""
    taken = np.zeros(len(trades), dtype=bool)
    open_until: dict[bool, list[int]] = {False: [], True: []}
    for i, trade in enumerate(trades):
        side = open_until[trade.short]
        while side and side[0] < trade.entry_row:
            heapq.heappop(side)
        if cap and len(side) >= cap:
            continue
        heapq.heappush(side, trade.exit_row)
        taken[i] = True
    return taken


def daily(trades: list[Trade], taken: np.ndarray, market: Market) -> dict[str, np.ndarray]:
    """Dollar profit by session (1× costs) and the number of open positions."""
    rows = len(market.close)
    pnl = np.zeros(rows)
    positions = np.zeros(rows, dtype=np.int32)
    shorts = np.zeros(rows, dtype=np.int32)
    for trade, keep in zip(trades, taken, strict=True):
        if not keep:
            continue
        e, x, n = trade.entry_row, trade.exit_row, trade.stock
        positions[e : x + 1] += 1
        if trade.short:
            shorts[e : x + 1] += 1
        entry = float(market.adjusted(market.open, e, n))
        final = trade.value * (1 + trade.gross)
        if x == e:
            pnl[e] += final - trade.value - trade.cost_entry - trade.cost_exit
            continue
        closes = market.adj_close[e:x, n].astype(np.float64)
        # A day without a price keeps the last value.
        valid = np.isfinite(closes)
        if not valid[0]:
            closes[0] = entry
            valid[0] = True
        idx = np.where(valid, np.arange(len(closes)), 0)
        np.maximum.accumulate(idx, out=idx)
        ratio = closes[idx] / entry
        value = trade.value * (2 - ratio if trade.short else ratio)
        pnl[e] += value[0] - trade.value - trade.cost_entry
        if len(value) > 1:
            pnl[e + 1 : x] += np.diff(value)
        pnl[x] += final - value[-1] - trade.cost_exit
    return {"pnl": pnl, "positions": positions, "shorts": shorts}
