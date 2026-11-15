"""Summary numbers for a multi-day book, from its daily series."""

from __future__ import annotations

import math

import numpy as np

TRADING_DAYS = 252


def _side(pnl: np.ndarray, account: float) -> dict:
    equity = account + np.cumsum(pnl)
    before = np.concatenate([[account], equity[:-1]])
    returns = np.where(before > 0, pnl / before, 0.0)
    spread = returns.std(ddof=1) if len(returns) > 1 else 0.0
    years = len(pnl) / TRADING_DAYS
    peak = np.maximum.accumulate(np.concatenate([[account], equity]))[1:]
    worst = int(np.argmin(equity - peak)) if len(equity) else 0
    final = float(equity[-1]) if len(equity) else account
    grew = final > 0 and years > 0
    return {
        "total_net": final - account,
        "total_return": final / account - 1,
        "annual_return": (final / account) ** (1 / years) - 1 if grew else -1.0,
        "annual_volatility": float(spread * math.sqrt(TRADING_DAYS)),
        "sharpe": float(returns.mean() / spread * math.sqrt(TRADING_DAYS)) if spread > 0 else 0.0,
        "t_stat_daily": float(returns.mean() / spread * math.sqrt(len(returns)))
        if spread > 0
        else 0.0,
        "max_drawdown": float((equity - peak)[worst]) if len(equity) else 0.0,
        "max_drawdown_pct": float((equity / peak - 1).min()) if len(equity) else 0.0,
    }


def summarize(daily: dict[str, list], *, account: float, counts: dict) -> dict:
    col = {k: np.asarray(v) for k, v in daily.items() if k != "date"}
    dates = daily["date"]
    n = len(dates)
    pnl, pnl_2x = col["pnl"].astype(float), col["pnl_2x"].astype(float)
    equity = col["equity"].astype(float)
    before = np.concatenate([[account], equity[:-1]])
    by_year: dict[str, dict] = {}
    for year in sorted({d.year for d in dates}):
        rows = np.array([d.year == year for d in dates])
        start = before[rows][0]
        by_year[str(year)] = {
            "return_1x": float(pnl[rows].sum() / start) if start > 0 else 0.0,
            "return_2x": float(pnl_2x[rows].sum() / start) if start > 0 else 0.0,
            "net_1x": float(pnl[rows].sum()),
        }
    safe = np.where(equity > 0, equity, np.nan)
    gross = (col["long_value"] + col["short_value"]) / safe
    net = (col["long_value"] - col["short_value"]) / safe
    traded = float(col["traded"].sum())
    years = n / TRADING_DAYS if n else 1.0
    costs = {k: float(col[k].sum()) for k in ("commission", "fees", "slippage", "borrow")}
    trading = costs["commission"] + costs["fees"] + costs["slippage"]
    return {
        "sessions": n,
        "account": account,
        "slippage_1x": _side(pnl, account),
        "slippage_2x": _side(pnl_2x, account),
        "by_year": by_year,
        "exposure": {
            "gross_mean": float(np.nanmean(gross)) if n else 0.0,
            "gross_max": float(np.nanmax(gross)) if n else 0.0,
            "net_mean": float(np.nanmean(net)) if n else 0.0,
            "long_names_mean": float(col["n_long"].mean()) if n else 0.0,
            "short_names_mean": float(col["n_short"].mean()) if n else 0.0,
        },
        "turnover_annual": traded / float(np.nanmean(safe)) / years if n and traded else 0.0,
        "costs": {**costs, "trading_bps_of_traded": trading / traded * 1e4 if traded else 0.0},
        "attribution": {
            # Price moves and dividends of the positions held, by side; then what was paid.
            "long_pnl": float(col["long_pnl"].sum()),
            "short_pnl": float(col["short_pnl"].sum()),
            "trading_costs": -trading,
            "borrow": -costs["borrow"],
        },
        "dividends_net": float(col["dividends"].sum()),  # already inside long_pnl and short_pnl
        "counts": counts,
    }
