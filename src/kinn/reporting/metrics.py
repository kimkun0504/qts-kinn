"""Standard metrics for any run, at 1x and 2x slippage."""

from __future__ import annotations

import math
from collections import Counter
from datetime import date

import numpy as np

from kinn.core.types import Trade

TRADING_DAYS = 252


def daily_table(trades: list[Trade], sessions: list[date]) -> dict[str, list]:
    """One row per session (also sessions without trades)."""
    by_day: dict[date, list[Trade]] = {d: [] for d in sessions}
    for trade in trades:
        by_day[trade.day].append(trade)
    days = sorted(by_day)
    table = {
        "date": days,
        "trades": [len(by_day[d]) for d in days],
        "notional": [sum(t.notional for t in by_day[d]) for d in days],
        "gross": [sum(t.gross for t in by_day[d]) for d in days],
        "net": [sum(t.net for t in by_day[d]) for d in days],
        "net_2x": [sum(t.net_2x for t in by_day[d]) for d in days],
    }
    table["cum_net"] = list(np.cumsum(table["net"]))
    table["cum_net_2x"] = list(np.cumsum(table["net_2x"]))
    return table


def _side(returns: np.ndarray, daily: np.ndarray, equity: float) -> dict:
    n_days = len(daily)
    out = {
        "mean_return": float(returns.mean()) if len(returns) else None,
        "median_return": float(np.median(returns)) if len(returns) else None,
        "win_rate": float((returns > 0).mean()) if len(returns) else None,
        "total_net": float(daily.sum()),
        "t_stat_daily": None,
        "sharpe": None,
        "annual_return_on_equity": None,
        "max_drawdown": None,
    }
    if n_days > 1 and daily.std(ddof=1) > 0:
        out["t_stat_daily"] = float(daily.mean() / (daily.std(ddof=1) / math.sqrt(n_days)))
        out["sharpe"] = float(daily.mean() / daily.std(ddof=1) * math.sqrt(TRADING_DAYS))
    if n_days:
        out["annual_return_on_equity"] = float(daily.mean() * TRADING_DAYS / equity)
        curve = np.cumsum(daily)
        out["max_drawdown"] = float((curve - np.maximum.accumulate(np.maximum(curve, 0))).min())
    return out


def summarize(trades: list[Trade], sessions: list[date], *, equity: float, counts: dict) -> dict:
    table = daily_table(trades, sessions)
    notional = np.array([t.notional for t in trades])
    total_notional = float(notional.sum()) if len(trades) else 0.0

    def bps(value: float) -> float | None:
        return float(value / total_notional * 1e4) if total_notional else None

    by_year: dict[int, dict] = {}
    for trade in trades:
        row = by_year.setdefault(trade.day.year, {"trades": 0, "r1": 0.0, "r2": 0.0, "net": 0.0})
        row["trades"] += 1
        row["r1"] += trade.net / trade.notional
        row["r2"] += trade.net_2x / trade.notional
        row["net"] += trade.net
    return {
        "sessions": len(sessions),
        "sessions_with_trades": int(sum(1 for n in table["trades"] if n)),
        "trades": len(trades),
        "trades_per_session": len(trades) / len(sessions) if sessions else None,
        "mean_notional": float(notional.mean()) if len(trades) else None,
        "gross_mean_return": float(np.mean([t.gross / t.notional for t in trades]))
        if trades
        else None,
        "slippage_1x": _side(
            np.array([t.net / t.notional for t in trades]), np.array(table["net"]), equity
        ),
        "slippage_2x": _side(
            np.array([t.net_2x / t.notional for t in trades]), np.array(table["net_2x"]), equity
        ),
        "cost_bps_of_notional": {
            "commission": bps(sum(t.commission for t in trades)),
            "fees": bps(sum(t.fees for t in trades)),
            "slippage_1x": bps(sum(t.slippage for t in trades)),
        },
        "exit_reasons": dict(Counter(t.exit_reason for t in trades)),
        "by_year": {
            str(year): {
                "trades": row["trades"],
                "mean_return_1x": row["r1"] / row["trades"],
                "mean_return_2x": row["r2"] / row["trades"],
                "net_1x": row["net"],
            }
            for year, row in sorted(by_year.items())
        },
        "counts": counts,
        "equity": equity,
    }
