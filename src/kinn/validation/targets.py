"""The owner's bar for paper trading (decision 0017), and the research periods.

One place for both, so the reports, the Workbench and any later gate read the same numbers.
"""

from __future__ import annotations

from datetime import date

DEVELOPMENT_END = date(2016, 12, 30)  # every search happens up to here
VALIDATION_START = date(2017, 1, 3)  # one run per chosen variant from here to the holdout
MIN_NET_PER_TRADE_2X = 0.01
MIN_SHARPE_2X = 1.0
MAX_DRAWDOWN_SHARE = 0.5  # of the account


def phase(start: date, end: date) -> str:
    """Which research period a run covers: development, validation, or both ("full")."""
    if end <= DEVELOPMENT_END:
        return "development"
    if start >= VALIDATION_START:
        return "validation"
    return "full"


def check(metrics: dict) -> list[dict]:
    """The three measured targets against a backtest's metrics (schema metrics-1), all at 2×
    slippage. The fourth target, fills confirmed against real trades, is a separate run."""
    two = metrics["slippage_2x"]
    net, sharpe, drawdown = two["mean_return"], two["sharpe"], two["max_drawdown"]
    share = None if drawdown is None else -drawdown / metrics["equity"]
    return [
        {"key": "net_per_trade", "label": "Net per trade at 2× slippage", "value": net,
         "bar": MIN_NET_PER_TRADE_2X, "met": net is not None and net >= MIN_NET_PER_TRADE_2X},
        {"key": "sharpe", "label": "Sharpe at 2× slippage", "value": sharpe,
         "bar": MIN_SHARPE_2X, "met": sharpe is not None and sharpe > MIN_SHARPE_2X},
        {"key": "drawdown", "label": "Worst drawdown at 2×, share of the account",
         "value": share, "bar": MAX_DRAWDOWN_SHARE,
         "met": share is not None and share < MAX_DRAWDOWN_SHARE},
    ]  # fmt: skip
