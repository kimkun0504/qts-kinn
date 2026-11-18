"""What a run made: the summary, years, stocks, the spread of trades and the book's curve."""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import pandas as pd

from kinn.lab.engine import REASONS, Trade

EPOCH = np.datetime64("2003-12-29")  # a Monday: weeks are counted from it


def _t(values: np.ndarray, groups: np.ndarray) -> float | None:
    """The t of the mean of group means (the research's weekly t)."""
    if len(values) < 3:
        return None
    frame = pd.DataFrame({"v": values, "g": groups})
    means = frame.groupby("g")["v"].mean().to_numpy()
    if len(means) < 3 or means.std(ddof=1) == 0:
        return None
    return float(means.mean() / (means.std(ddof=1) / math.sqrt(len(means))))


def _clean(value):
    if isinstance(value, float | np.floating):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, np.integer):
        return int(value)
    return value


def _row(values: dict) -> dict:
    return {key: _clean(value) for key, value in values.items()}


def trades_table(trades: list[Trade], taken: np.ndarray, dates: np.ndarray, tickers: list[str],
                 static: dict[str, list]) -> pd.DataFrame:  # fmt: skip
    if not trades:
        return pd.DataFrame(columns=["ticker", "signal_date", "entry_date", "exit_date", "reason"])
    get = lambda name: np.array([getattr(t, name) for t in trades])  # noqa: E731
    stock = get("stock")
    return pd.DataFrame({
        "ticker": [tickers[i] for i in stock],
        "name": [static["name"][i] for i in stock],
        "sector": [static["sector"][i] for i in stock],
        "signal_date": dates[get("signal_row")].astype("datetime64[D]"),
        "entry_date": dates[get("entry_row")].astype("datetime64[D]"),
        "exit_date": dates[get("exit_row")].astype("datetime64[D]"),
        "sessions": get("exit_row") - get("entry_row") + 1,
        "reason": [REASONS[r] for r in get("reason")],
        "entry_price": get("entry_price"), "exit_price": get("exit_price"),
        "shares": get("shares"), "value": get("value"),
        "gross": get("gross"), "net": get("net"), "net_2x": get("net_2x"),
        "profit": get("value") * get("net"),
        "benchmark": get("benchmark"), "over": get("net") - get("benchmark"),
        "taken": taken, "priority": get("priority"),
    })  # fmt: skip


def summary(table: pd.DataFrame, book: dict, dates: np.ndarray, first_row: int, settings,
            spy: np.ndarray, lookahead: dict) -> dict:  # fmt: skip
    n = len(table)
    out: dict = {"trades": n, "lookahead": lookahead}
    if not n:
        out["headline"] = "No trades"
        return out
    net, net2 = table["net"].to_numpy(), table["net_2x"].to_numpy()
    entry_days = table["entry_date"].to_numpy().astype("datetime64[D]")
    weeks = ((entry_days - EPOCH).astype(int) // 7).astype(int)
    years = pd.DatetimeIndex(entry_days).year.to_numpy()
    yearly = pd.Series(net).groupby(years).mean()
    taken = table["taken"].to_numpy()
    pnl = book["pnl"]
    cum = np.cumsum(pnl)
    peak = np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
    drawdown = cum - peak
    cap = settings.book.max_positions
    capital = settings.book.position_size * (cap or max(int(book["positions"].max()), 1))
    active = np.flatnonzero(book["positions"] > 0)
    span_rows = (active[-1] - first_row + 1) if active.size else 1
    years_span = max(span_rows / 252, 1 / 252)
    daily_ret = pnl[first_row : first_row + span_rows] / capital
    sharpe = (daily_ret.mean() / daily_ret.std() * math.sqrt(252)) if daily_ret.std() > 0 else None
    spy_first = spy[first_row] if first_row < len(spy) else np.nan
    spy_last_row = min(first_row + span_rows - 1, len(spy) - 1)
    reasons = table["reason"].value_counts().to_dict()
    out.update(_row({
        "win_rate": float((net > 0).mean()), "mean_net": float(net.mean()),
        "median_net": float(np.median(net)), "mean_gross": float(table["gross"].mean()),
        "mean_net_2x": float(net2.mean()), "mean_over": float(table["over"].mean()),
        "t_weekly": _t(net, weeks), "t_weekly_over": _t(table["over"].to_numpy(), weeks),
        "t_weekly_2x": _t(net2, weeks),
        "years_positive": int((yearly > 0).sum()), "years": int(len(yearly)),
        "best": float(net.max()), "worst": float(net.min()),
        "p05": float(np.percentile(net, 5)), "p95": float(np.percentile(net, 95)),
        "mean_sessions": float(table["sessions"].mean()),
        "stocks": int(table["ticker"].nunique()),
        "taken": int(taken.sum()), "skipped": int((~taken).sum()),
        "book_profit": float(cum[-1]),
        "book_profit_2x": float((table["value"] * net2)[taken].sum()),
        "max_drawdown": float(drawdown.min()), "capital": float(capital),
        "annual_return": float(cum[-1] / capital / years_span),
        "max_drawdown_pct": float(drawdown.min() / capital), "sharpe": sharpe,
        "average_positions": float(book["positions"][first_row : first_row + span_rows].mean()),
        "spy_return": float(spy[spy_last_row] / spy_first - 1) if np.isfinite(spy_first) else None,
        "first_entry": str(entry_days.min()), "last_exit": str(table["exit_date"].max())[:10],
    }))  # fmt: skip
    out["exits"] = {reason: int(count) for reason, count in reasons.items()}
    out["fragile"] = bool(out["mean_net"] > 0 and out["mean_net_2x"] <= 0)
    edges = np.linspace(-0.5, 0.5, 41)
    counts, _ = np.histogram(np.clip(net, -0.5 + 1e-9, 0.5 - 1e-9), bins=edges)
    out["histogram"] = {"edges": edges.tolist(), "counts": counts.tolist()}
    sign = "+" if out["mean_net"] >= 0 else ""
    out["headline"] = f"{n:,} trades, {sign}{100 * out['mean_net']:.2f}% a trade after costs"
    return out


def by_year(table: pd.DataFrame, book: dict, dates: np.ndarray) -> list[dict]:
    if table.empty:
        return []
    years = pd.DatetimeIndex(table["entry_date"]).year
    profit_by_year = (
        pd.Series(book["pnl"], index=pd.DatetimeIndex(dates).year).groupby(level=0).sum()
    )
    rows = []
    for year, group in table.groupby(years):
        net = group["net"].to_numpy()
        rows.append(_row({
            "year": int(year), "trades": len(group), "mean_net": float(net.mean()),
            "median_net": float(np.median(net)), "win_rate": float((net > 0).mean()),
            "mean_over": float(group["over"].mean()), "mean_net_2x": float(group["net_2x"].mean()),
            "book_profit": float(profit_by_year.get(year, 0.0)),
        }))  # fmt: skip
    return rows


def by_stock(table: pd.DataFrame) -> list[dict]:
    """Every stock that traded: what all its trades made at the position size (``profit``)
    and what the trades the book took made (``book_profit``)."""
    if table.empty:
        return []
    grouped = defaultdict(list)
    for i, ticker in enumerate(table["ticker"].to_numpy()):
        grouped[ticker].append(i)
    net = table["net"].to_numpy()
    profit = table["profit"].to_numpy()
    over = table["over"].to_numpy()
    taken = table["taken"].to_numpy().astype(bool)
    rows = []
    for ticker, idx in grouped.items():
        idx = np.array(idx)
        first = table.iloc[idx[0]]
        rows.append(_row({
            "ticker": ticker, "name": first["name"], "sector": first["sector"],
            "trades": len(idx), "wins": int((net[idx] > 0).sum()),
            "win_rate": float((net[idx] > 0).mean()), "mean_net": float(net[idx].mean()),
            "total_net": float(net[idx].sum()), "profit": float(profit[idx].sum()),
            "book_trades": int(taken[idx].sum()),
            "book_profit": float(profit[idx][taken[idx]].sum()),
            "mean_over": float(over[idx].mean()), "best": float(net[idx].max()),
            "worst": float(net[idx].min()),
            "last_entry": str(table["entry_date"].iloc[idx[-1]])[:10],
        }))  # fmt: skip
    rows.sort(key=lambda r: r["profit"] or 0.0, reverse=True)
    return rows


def equity(book: dict, dates: np.ndarray, spy: np.ndarray, first_row: int, capital: float) -> dict:
    pnl, positions = book["pnl"], book["positions"]
    active = np.flatnonzero(positions > 0)
    last = int(active[-1]) if active.size else first_row
    span = slice(first_row, last + 1)
    cum = np.cumsum(pnl)[span]
    peak = np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
    base = spy[first_row] if first_row < len(spy) else np.nan
    spy_line = (spy[span] / base - 1) * capital if np.isfinite(base) else np.full(len(cum), np.nan)
    step = max(1, len(cum) // 1200)  # at most about 1,200 points for the chart
    pick = np.arange(0, len(cum), step)
    if len(cum) and pick[-1] != len(cum) - 1:
        pick = np.append(pick, len(cum) - 1)
    clean = lambda a: [None if not np.isfinite(v) else round(float(v), 2) for v in a]  # noqa: E731
    return {
        "dates": [str(d)[:10] for d in dates[span][pick]],
        "profit": clean(cum[pick]), "drawdown": clean((cum - peak)[pick]),
        "spy": clean(spy_line[pick]), "positions": positions[span][pick].tolist(),
        "capital": capital,
    }  # fmt: skip
