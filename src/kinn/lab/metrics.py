"""What a run made: the summary, years, stocks, the spread of trades and the book's curve."""

from __future__ import annotations

import math
import warnings
from collections import defaultdict

import numpy as np
import pandas as pd

from kinn.lab.engine import REASONS, Trade

EPOCH = np.datetime64("2003-12-29")  # a Monday: weeks are counted from it
ROLLING = 252


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
        "side": np.where(get("short"), "short", "long"),
    })  # fmt: skip


def _against(daily_ret: np.ndarray, spy: np.ndarray, first_row: int,
             span_rows: int) -> tuple[float | None, float | None]:  # fmt: skip
    """The book's beta to SPY and the correlation of their daily returns."""
    prices = spy[max(first_row - 1, 0) : first_row + span_rows].astype(np.float64)
    if first_row == 0:
        prices = np.concatenate([[np.nan], prices])
    with np.errstate(divide="ignore", invalid="ignore"):
        market = prices[1:] / prices[:-1] - 1
    ok = np.isfinite(market) & np.isfinite(daily_ret)
    if ok.sum() < 20 or np.std(market[ok]) == 0 or np.std(daily_ret[ok]) == 0:
        return None, None
    cov = np.cov(daily_ret[ok], market[ok])
    return float(cov[0, 1] / cov[1, 1]), float(np.corrcoef(daily_ret[ok], market[ok])[0, 1])


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
    sides = 2 if settings.entry.side == "both" else 1
    capital = settings.book.position_size * (cap * sides or max(int(book["positions"].max()), 1))
    active = np.flatnonzero(book["positions"] > 0)
    span_rows = (active[-1] - first_row + 1) if active.size else 1
    years_span = max(span_rows / 252, 1 / 252)
    daily_ret = pnl[first_row : first_row + span_rows] / capital
    sharpe = (daily_ret.mean() / daily_ret.std() * math.sqrt(252)) if daily_ret.std() > 0 else None
    beta, correlation = _against(daily_ret, spy, first_row, span_rows)
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
        "beta_spy": beta, "correlation_spy": correlation,
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
    kind = {"short": "short trades", "both": "long and short trades"}.get(settings.entry.side,
                                                                          "trades")  # fmt: skip
    out["headline"] = f"{n:,} {kind}, {sign}{100 * out['mean_net']:.2f}% a trade after costs"
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


def signal_path(trades: list[Trade], adj_close: np.ndarray, universe_cum: np.ndarray, hold: int,
                limit: int = 20_000) -> dict | None:  # fmt: skip
    """The average split-adjusted move of the traded stocks from their signal day's close, from
    ``before`` sessions before it to ``after`` sessions after, beside the universe's over the same
    days: how the edge builds and fades around the signal, past the exit too. Moves are as
    held: a short's line rises when its price falls."""
    if not trades:
        return None
    before, after = 20, int(min(120, max(40, 3 * hold)))
    picked = trades
    if len(trades) > limit:
        keep = np.random.default_rng(0).choice(len(trades), size=limit, replace=False)
        picked = [trades[i] for i in sorted(keep)]
    rows = np.array([t.signal_row for t in picked])
    cols = np.array([t.stock for t in picked])
    held = np.array([-1.0 if t.short else 1.0 for t in picked])
    horizons = np.arange(-before, after + 1)
    sessions = adj_close.shape[0]
    stock = np.full((len(picked), len(horizons)), np.nan)
    market = np.full_like(stock, np.nan)
    base = adj_close[rows, cols].astype(np.float64)
    for k, h in enumerate(horizons):
        at = rows + h
        ok = (at >= 0) & (at < sessions) & (base > 0)
        price = np.full(len(picked), np.nan)
        price[ok] = adj_close[at[ok], cols[ok]]
        with np.errstate(divide="ignore", invalid="ignore"):
            stock[:, k] = held * (price / base - 1)
        market[ok, k] = held[ok] * np.expm1(universe_cum[at[ok]] - universe_cum[rows[ok]])
    excess = stock - market
    count = np.sum(np.isfinite(excess), axis=0)
    with np.errstate(invalid="ignore", divide="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mean_stock = np.nanmean(np.where(np.isfinite(excess), stock, np.nan), axis=0)
        mean_market = np.nanmean(np.where(np.isfinite(excess), market, np.nan), axis=0)
        mean_excess = np.nanmean(excess, axis=0)
        spread = np.nanstd(excess, axis=0, ddof=1) / np.sqrt(np.maximum(count, 1))
    clean = lambda a: [None if not np.isfinite(v) else round(float(v), 5) for v in a]  # noqa: E731
    return {
        "horizons": horizons.tolist(), "stock": clean(mean_stock), "universe": clean(mean_market),
        "excess": clean(mean_excess), "low": clean(mean_excess - 1.96 * spread),
        "high": clean(mean_excess + 1.96 * spread), "count": count.tolist(),
        "trades": len(picked), "of": len(trades), "hold": hold,
    }  # fmt: skip


def _ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values))
    ranks[order] = np.arange(len(values))
    return ranks


LUCK_DRAWS = 500


def _held(market, entry_rows: np.ndarray, cols: np.ndarray, hold: int) -> np.ndarray:
    """Split-adjusted return from the open of each entry row to the close ``hold`` sessions on."""
    exit_rows = np.minimum(entry_rows + hold - 1, len(market.close) - 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        factor = market.adj_close[entry_rows, cols] / market.close[entry_rows, cols]
        start = market.open[entry_rows, cols] * factor
        return market.adj_close[exit_rows, cols].astype(np.float64) / start - 1


def luck(trades: list[Trade], market, first_row: int, last_signal_row: int, hold: int,
         draws: int = LUCK_DRAWS, seed: int = 0, limit: int = 5_000) -> dict | None:  # fmt: skip
    """The run's trades against random picks, all held the same way (from the entry open to
    the close of the hold-th session, before costs, no stops or exit signals): random stocks
    the book could have bought on the same days, and the same stocks on random days of the
    period. A short counts the fall."""
    if len(trades) < 10:
        return None
    rng = np.random.default_rng(seed)
    rows = len(market.close)
    of = len(trades)
    if of > limit:
        trades = [trades[i] for i in sorted(rng.choice(of, size=limit, replace=False))]
    entry = np.array([t.entry_row for t in trades])
    stock = np.array([t.stock for t in trades])
    sign = np.array([-1.0 if t.short else 1.0 for t in trades])
    actual = sign * _held(market, entry, stock, hold)
    keep = np.isfinite(actual)
    entry, stock, sign, actual = entry[keep], stock[keep], sign[keep], actual[keep]
    if len(actual) < 10:
        return None
    exits = np.minimum(entry + hold - 1, rows - 1)

    same_days = np.full((draws, len(entry)), np.nan)
    for e in np.unique(entry):
        mine = np.flatnonzero(entry == e)
        x = min(e + hold - 1, rows - 1)
        pool = np.flatnonzero(market.enterable(e) & np.isfinite(market.adj_close[x]))
        if not pool.size:
            continue
        picks = pool[rng.integers(0, pool.size, size=(draws, mine.size))]
        rows_e = np.full(picks.shape, e)
        same_days[:, mine] = sign[mine] * _held(market, rows_e.ravel(), picks.ravel(),
                                                hold).reshape(picks.shape)  # fmt: skip

    lo, hi = first_row + 1, min(last_signal_row + 1, rows - 1)
    other_days = np.full((draws, len(entry)), np.nan)
    for n in np.unique(stock):
        mine = np.flatnonzero(stock == n)
        span = np.arange(lo, hi + 1)
        later = np.minimum(span + hold - 1, rows - 1)
        with np.errstate(invalid="ignore"):
            ok = market.eligible[span, n] & (market.open[span, n] > 0)
            ok &= (market.close[span, n] > 0) & np.isfinite(market.adj_close[later, n])
        pool = span[ok]
        if not pool.size:
            continue
        days = pool[rng.integers(0, pool.size, size=(draws, mine.size))]
        other_days[:, mine] = sign[mine] * _held(market, days.ravel(), np.full(days.size, n),
                                                 hold).reshape(days.shape)  # fmt: skip
    mean = float(actual.mean())

    def compare(sample: np.ndarray) -> dict | None:
        with np.errstate(invalid="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            means = np.nanmean(sample, axis=1)
        means = means[np.isfinite(means)]
        if not means.size:
            return None
        return {"mean": float(means.mean()), "low": float(np.percentile(means, 2.5)),
                "high": float(np.percentile(means, 97.5)),
                "beaten": float((means < mean).mean())}  # fmt: skip

    return {"trades": int(len(actual)), "of": of, "hold": hold, "draws": draws, "mean": mean,
            "same_days": compare(same_days), "other_days": compare(other_days),
            "exits_beyond": int((exits >= rows - 1).sum())}  # fmt: skip


def factor_report(scores: np.ndarray, market, dates: np.ndarray, first_row: int,
                  last_signal_row: int, hold: int, order: str, buckets: int = 10,
                  minimum: int = 30) -> dict | None:  # fmt: skip
    """How a ranking's scores line up with what followed: each day the scored stocks the book
    could have bought are split into ``buckets`` by score, and each bucket's return from the next
    open to the close ``hold`` sessions later is measured against that day's average; the
    rank correlation of score and return (IC) is taken each day. Before costs."""
    rows = scores.shape[0]
    last = min(last_signal_row, rows - hold - 1)
    sums = np.zeros(buckets)
    raw = np.zeros(buckets)
    days_in = np.zeros(buckets)
    ics, ic_rows = [], []
    for t in range(first_row, last + 1):
        score = scores[t]
        entry = market.adjusted(market.open, t + 1, slice(None))
        exit_ = market.adj_close[t + hold]
        with np.errstate(divide="ignore", invalid="ignore"):
            forward = exit_ / entry - 1
        ok = np.isfinite(score) & np.isfinite(forward) & market.enterable(t + 1)
        if ok.sum() < minimum:
            continue
        s, f = score[ok], forward[ok].astype(np.float64)
        rank = _ranks(s)
        bucket = np.minimum((rank * buckets / len(s)).astype(int), buckets - 1)
        mean = f.mean()
        for b in range(buckets):
            mine = bucket == b
            if mine.any():
                sums[b] += f[mine].mean() - mean
                raw[b] += f[mine].mean()
                days_in[b] += 1
        ics.append(float(np.corrcoef(rank, _ranks(f))[0, 1]))
        ic_rows.append(t)
    if not ics:
        return None
    ic = np.array(ics)
    spaced = ic[:: max(1, hold)]
    years: dict[int, list[float]] = defaultdict(list)
    for t, value in zip(ic_rows, ics, strict=True):
        years[int(str(dates[t])[:4])].append(value)
    excess = np.where(days_in > 0, sums / np.maximum(days_in, 1), np.nan)
    top, bottom = (buckets - 1, 0) if order == "highest" else (0, buckets - 1)
    clean = lambda v: None if not np.isfinite(v) else round(float(v), 6)  # noqa: E731
    return {
        "buckets": [{"bucket": b + 1, "excess": clean(excess[b]),
                     "mean": clean(raw[b] / days_in[b]) if days_in[b] else None,
                     "days": int(days_in[b])} for b in range(buckets)],
        "spread": clean(excess[top] - excess[bottom]), "order": order, "hold": hold,
        "ic": {"mean": clean(ic.mean()), "std": clean(ic.std(ddof=1)) if len(ic) > 1 else None,
               "t": clean(spaced.mean() / spaced.std(ddof=1) * np.sqrt(len(spaced)))
               if len(spaced) > 2 and spaced.std(ddof=1) > 0 else None,
               "positive": clean(float((ic > 0).mean())), "days": len(ics),
               "independent_days": len(spaced)},
        "ic_by_year": [{"year": y, "mean": clean(float(np.mean(v))), "days": len(v)}
                       for y, v in sorted(years.items())],
    }  # fmt: skip


def equity(book: dict, dates: np.ndarray, spy: np.ndarray, first_row: int, capital: float,
           position_size: float | None = None) -> dict:  # fmt: skip
    """The book's profit beside SPY on all the capital and SPY at the book's net exposure."""
    pnl, positions = book["pnl"], book["positions"]
    shorts = book.get("shorts", np.zeros_like(positions))
    active = np.flatnonzero(positions > 0)
    last = int(active[-1]) if active.size else first_row
    span = slice(first_row, last + 1)
    cum = np.cumsum(pnl)[span]
    peak = np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
    window = pd.Series(pnl[span]).rolling(ROLLING, min_periods=ROLLING)
    rolling = (window.mean() / window.std() * math.sqrt(252)).to_numpy()
    base = spy[first_row] if first_row < len(spy) else np.nan
    spy_line = (spy[span] / base - 1) * capital if np.isfinite(base) else np.full(len(cum), np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        spy_day = np.nan_to_num(spy[span][1:] / spy[span][:-1] - 1, nan=0.0, posinf=0.0, neginf=0.0)
    net = (positions - 2 * shorts)[span][1:] * (position_size or 0.0)
    invested = np.clip(net, -capital, capital)
    matched = np.concatenate([[0.0], np.cumsum(spy_day * invested)])
    step = max(1, len(cum) // 1200)  # at most about 1,200 points for the chart
    pick = np.arange(0, len(cum), step)
    if len(cum) and pick[-1] != len(cum) - 1:
        pick = np.append(pick, len(cum) - 1)
    clean = lambda a: [None if not np.isfinite(v) else round(float(v), 2) for v in a]  # noqa: E731
    return {
        "dates": [str(d)[:10] for d in dates[span][pick]],
        "profit": clean(cum[pick]), "drawdown": clean((cum - peak)[pick]),
        "spy": clean(spy_line[pick]), "positions": positions[span][pick].tolist(),
        "shorts": shorts[span][pick].tolist(),
        "rolling_sharpe": clean(rolling[pick]),
        "spy_matched": clean(matched[pick]) if position_size else None,
        "capital": capital,
    }  # fmt: skip
