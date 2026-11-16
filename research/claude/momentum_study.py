"""The intraday momentum study (strategies/intraday_momentum/HYPOTHESIS.md). Development
years only. Every rule is defined in that file; this one implements them.

    uv run python research/claude/momentum_study.py candidates
    uv run python research/claude/momentum_study.py trades --budget 150 --workers 3   # resumable
    uv run python research/claude/momentum_study.py report
"""

from __future__ import annotations

import argparse
import glob
import math
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from kinn.validation.targets import DEVELOPMENT_END

ACCOUNT = 20_000.0
STOCK_POSITION = 4_000.0
COMMISSION, MIN_COMMISSION = 0.0035, 0.35
STOCK_SLIP = 0.0005  # of the price, per side, at 1x
ETF_SLIP = 0.005  # dollars a share, per side, at 1x
STOP_ATR = 0.10
STOCK_EXITS = ("stop", "vwap", "ema9", "ema20", "sma20", "ema9_5m", "ema20_5m")


# -- A: candidates ----------------------------------------------------------------------------


def candidates(base: Path, store: DataStore) -> None:
    scratch = tempfile.mkdtemp()  # not under the data folder: its files cannot be deleted
    con = duckdb.connect(f"{scratch}/work.duckdb")
    con.execute("set memory_limit='1500MB'; set threads=2")
    con.execute(f"set temp_directory='{scratch}'")
    con.execute(
        f"""create or replace table joined as
            select p.date as day, p.symbol, p.permaticker, p.high, p.low, p.close, p.volume,
                   p.prev_close, p.split_ratio, o.* exclude (day, symbol)
            from read_parquet('{store.root}/panel/*.parquet') p
            left join read_parquet('{base}/*.or.parquet') o
              on o.day = p.date and o.symbol = p.symbol
            where p.date <= DATE '{DEVELOPMENT_END.isoformat()}'"""
    )
    con.execute(
        """create or replace table featured as
           select *, avg(greatest(high, prev_close) - least(low, prev_close)) over w as atr14,
                  avg(volume) over w as volume14, count(*) over w as sessions14,
                  max(abs(ln(split_ratio))) over w as split14,
                  avg(coalesce(or5_volume, 0)) over w as or5_usual,
                  avg(coalesce(or15_volume, 0)) over w as or15_usual
           from joined
           window w as (partition by permaticker order by day
                        rows between 14 preceding and 1 preceding)"""
    )
    parts = []
    for name in ("or5", "or15"):
        parts.append(
            f"""select day, symbol, '{name}' as range, atr14, close as official_close, or_open,
                       {name}_high as range_high, {name}_low as range_low,
                       {name}_volume / {name}_usual as relative_volume,
                       sign({name}_close - or_open)::int as direction,
                       row_number() over (partition by day
                                          order by {name}_volume / {name}_usual desc) as rank
                from featured
                where sessions14 = 14 and split14 < 1e-9 and abs(ln(split_ratio)) < 1e-9
                  and or_open > 5 and volume14 >= 1e6 and atr14 > 0.5 and {name}_usual > 0
                  and {name}_volume >= {name}_usual"""
        )
    con.execute(
        f"""copy (select * from ({" union all ".join(parts)})
                  where rank <= 20 and direction <> 0 order by day, symbol, range)
            to '{base}/candidates.parquet' (format parquet)"""
    )
    print(con.execute(
        f"""select range, count(*), count(distinct day), round(avg(relative_volume), 1),
                   round(avg((direction > 0)::int), 2)
            from '{base}/candidates.parquet' group by 1"""
    ).fetchall())  # fmt: skip
    con.close()


# -- A: trades --------------------------------------------------------------------------------


def _ema(x: np.ndarray, n: int) -> np.ndarray:
    out, k = np.empty(len(x)), 2.0 / (n + 1)
    acc = x[0]
    for i, value in enumerate(x):
        acc = acc + k * (value - acc)
        out[i] = acc
    return out


def _sma(x: np.ndarray, n: int) -> np.ndarray:
    total = np.cumsum(x)
    out = total / np.arange(1, len(x) + 1)
    out[n:] = (total[n:] - total[:-n]) / n
    return out


def simulate(c: dict, m, o, h, lo, cl, v) -> dict | None:
    """One candidate: entry on the break of its opening range, then every exit rule."""
    d = c["direction"]
    start = 575 if c["range"] == "or5" else 585
    level = c["range_high"] if d > 0 else c["range_low"]
    live = m >= start
    broke = live & ((h > level) if d > 0 else (lo < level))
    hit = np.flatnonzero(broke)
    if not len(hit):
        return None
    k, n = int(hit[0]), len(m)
    entry = max(level, o[k]) if d > 0 else min(level, o[k])
    final = c["official_close"] or float(cl[-1])
    out = {"day": c["day"], "symbol": c["symbol"], "range": c["range"], "direction": d,
           "atr": c["atr14"], "entry_minute": int(m[k]), "entry": float(entry)}  # fmt: skip

    def after(j: int | None) -> float:  # out at the open after bar j, or at the close
        return float(o[j + 1]) if j is not None and j + 1 < n else final

    def first(mask: np.ndarray, begin: int) -> int | None:
        found = np.flatnonzero(mask[begin:])
        return begin + int(found[0]) if len(found) else None

    stop = entry - d * STOP_ATR * c["atr14"]
    if d * (cl[k] - stop) <= 0:
        out["stop"] = float(stop)
    else:
        touched = (lo <= stop) if d > 0 else (h >= stop)
        j = first(touched, k + 1) if k + 1 < n else None
        out["stop"] = final if j is None else float(min(stop, o[j]) if d > 0 else max(stop, o[j]))
    typical = (h + lo + cl) / 3.0
    vwap = np.cumsum(typical * v) / np.maximum(np.cumsum(v), 1)
    lines = {"vwap": vwap, "ema9": _ema(cl, 9), "ema20": _ema(cl, 20), "sma20": _sma(cl, 20)}
    for name, line in lines.items():
        out[name] = after(first(d * (cl - line) < 0, k))
    ends = np.flatnonzero(((m - 570) % 5 == 4) | (np.arange(n) == n - 1))
    five = cl[ends]
    for name, length in (("ema9_5m", 9), ("ema20_5m", 20)):
        crossed = d * (five - _ema(five, length)) < 0
        later = np.flatnonzero(crossed & (ends >= k))
        out[name] = after(int(ends[later[0]]) if len(later) else None)
    return out


def trades_month(job: dict) -> str | None:
    if time.time() > job["deadline"]:
        return None
    base = Path(job["base"])
    con = duckdb.connect()
    con.execute("set threads=1; set memory_limit='900MB'")
    files = ", ".join(f"'{f}'" for f in job["files"])
    wanted = con.execute(
        f"""select * from '{base}/candidates.parquet'
            where strftime(day, '%Y-%m') = '{job["month"]}' order by day, symbol"""
    ).to_arrow_table().to_pylist()  # fmt: skip
    rows = []
    if wanted:
        bars = con.execute(
            f"""select cast(b.bar_start as date) as day, b.symbol, b.minute_et as minute,
                       b.open, b.high, b.low, b.close, b.volume
                from read_parquet([{files}]) b
                where b.minute_et between 570 and 959
                  and (cast(b.bar_start as date), b.symbol) in
                      (select (day, symbol) from '{base}/candidates.parquet')
                order by 1, 2, 3"""
        ).to_arrow_table()  # fmt: skip
        cols = {name: bars[name].to_numpy(zero_copy_only=False) for name in bars.column_names}
        key = np.char.add(cols["day"].astype(str), cols["symbol"].astype(str))
        starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        where = dict(zip(key[starts], zip(starts, np.r_[starts[1:], len(key)], strict=True),
                         strict=True))  # fmt: skip
        for c in wanted:
            span = where.get(f"{c['day']}{c['symbol']}")
            if span is None:
                continue
            a, z = span
            series = [cols[name][a:z].astype(float)
                      for name in ("open", "high", "low", "close", "volume")]  # fmt: skip
            result = simulate(c, cols["minute"][a:z].astype(int), *series)
            if result:
                rows.append(result)
    out = base / "trades"
    out.mkdir(exist_ok=True)
    tmp = out / f"{job['month']}.tmp"
    pq.write_table(pa.Table.from_pylist(rows) if rows else pa.table({}), tmp)
    tmp.replace(out / f"{job['month']}.parquet")
    return job["month"]


# -- B, C, D: the ETFs ------------------------------------------------------------------------


def etf_days(base: Path, symbol: str) -> list[dict]:
    names = ("QQQ", "QQQQ") if symbol == "QQQ" else (symbol,)
    table = duckdb.sql(
        f"""select day, minute, open, high, low, close, volume
            from read_parquet('{base}/*.etf.parquet') where symbol in {names + ("",)}
            order by day, minute"""
    ).to_arrow_table()  # fmt: skip
    cols = {name: table[name].to_numpy(zero_copy_only=False) for name in table.column_names}
    day = cols["day"].astype("datetime64[D]")
    starts = np.flatnonzero(np.r_[True, day[1:] != day[:-1]])
    out = []
    for a, z in zip(starts, np.r_[starts[1:], len(day)], strict=True):
        out.append({"day": day[a], "minute": cols["minute"][a:z].astype(int),
                    **{k: cols[k][a:z].astype(float)
                       for k in ("open", "high", "low", "close", "volume")}})  # fmt: skip
    return out


def run_signal(d: dict, signal: np.ndarray, long_only: bool) -> tuple[float, float, int]:
    """Hold `signal[k]` from the open of bar k+1; flat at the close. Returns the day's profit
    a share, the shares traded per share held, and the number of orders."""
    o, cl = d["open"], d["close"]
    n = len(cl)
    if n < 2:
        return 0.0, 0.0, 0
    position = np.maximum(signal[: n - 1], 0) if long_only else signal[: n - 1]
    price = o[1:]  # where each position starts
    following = np.r_[price[1:], cl[-1]]  # where it is next marked: the next open, or the close
    change = np.abs(np.diff(np.r_[0.0, position, 0.0]))
    return (
        float((position * (following - price)).sum()),
        float(change.sum()),
        int((change > 0).sum()),
    )


def vwap_signal(d: dict) -> np.ndarray:
    typical = (d["high"] + d["low"] + d["close"]) / 3.0
    vwap = np.cumsum(typical * d["volume"]) / np.maximum(np.cumsum(d["volume"]), 1)
    return _held(np.sign(d["close"] - vwap))


def _held(raw: np.ndarray) -> np.ndarray:
    """Zeros (price exactly on the line) keep the previous side."""
    out = raw.copy()
    for i in range(1, len(out)):
        if out[i] == 0:
            out[i] = out[i - 1]
    return out


def noise_signals(days: list[dict]) -> list[np.ndarray]:
    """C: the half-hourly noise-area rule with the VWAP trailing stop."""
    grid = np.arange(570, 960)
    moves, out = [], []
    previous_close = None
    for d in days:
        at = np.searchsorted(d["minute"], grid, side="right") - 1
        path = np.where(at >= 0, d["close"][np.maximum(at, 0)], np.nan)
        path[grid > d["minute"][-1]] = np.nan
        open_ = d["open"][0]
        signal = np.zeros(len(d["close"]))
        if len(moves) >= 14 and previous_close:
            noise = np.nanmean(np.array(moves[-14:]), axis=0)
            typical = (d["high"] + d["low"] + d["close"]) / 3.0
            vwap = np.cumsum(typical * d["volume"]) / np.maximum(np.cumsum(d["volume"]), 1)
            upper = max(open_, previous_close) * (1 + noise)
            lower = min(open_, previous_close) * (1 - noise)
            side = 0.0
            for i, minute in enumerate(d["minute"]):
                if minute >= 599 and (minute - 569) % 30 == 0:  # bars ending at :00 and :30
                    g = minute - 570
                    price = d["close"][i]
                    if side > 0 and price < max(upper[g], vwap[i]):
                        side = 0.0
                    if side < 0 and price > min(lower[g], vwap[i]):
                        side = 0.0
                    if price > upper[g]:
                        side = 1.0
                    elif price < lower[g]:
                        side = -1.0
                signal[i] = side
        out.append(signal)
        moves.append(np.abs(path / open_ - 1.0))
        previous_close = d["close"][-1]
    return out


def average_signals(days: list[dict]) -> dict[str, list[np.ndarray]]:
    """D: price against one average and crossovers, on 1- and 5-minute bars. Averages run on
    the regular-session closes and carry over from the previous day."""
    closes = np.concatenate([d["close"] for d in days])
    minutes = np.concatenate([d["minute"] for d in days])
    sizes = np.cumsum([len(d["close"]) for d in days])[:-1]
    last = np.zeros(len(closes), dtype=bool)
    last[np.r_[sizes - 1, len(closes) - 1]] = True
    out = {}
    for bar, ends in (("1m", np.arange(len(closes))),
                      ("5m", np.flatnonzero(((minutes - 570) % 5 == 4) | last))):  # fmt: skip
        x = closes[ends]
        lines = {"EMA9": _ema(x, 9), "EMA20": _ema(x, 20), "EMA50": _ema(x, 50),
                 "SMA8": _sma(x, 8), "SMA20": _sma(x, 20), "SMA50": _sma(x, 50)}  # fmt: skip
        rules = {f"price>{name}": np.sign(x - line) for name, line in lines.items()}
        for kind, a, b, c in (("EMA", 9, 20, 50), ("SMA", 8, 20, 50)):
            for fast, slow in ((a, b), (a, c), (b, c)):
                rules[f"{kind}{fast}>{kind}{slow}"] = np.sign(
                    lines[f"{kind}{fast}"] - lines[f"{kind}{slow}"]
                )
        for name, raw in rules.items():
            full = np.zeros(len(closes))
            full[ends] = raw
            if bar == "5m":  # between 5-minute closes the last decision stands
                idx = np.maximum.accumulate(np.where(np.isin(np.arange(len(closes)), ends),
                                                     np.arange(len(closes)), 0))  # fmt: skip
                full = full[idx]
            out[f"{name} {bar}"] = np.split(_held(full), sizes)
    return out


# -- report -----------------------------------------------------------------------------------


def summary(label: str, days: np.ndarray, pnl: np.ndarray, trades: int) -> dict:
    """`pnl` is one dollar figure per session (zeros included)."""
    years = days.astype("datetime64[Y]").astype(int) + 1970
    by_year = [float(pnl[years == y].sum()) for y in np.unique(years)]
    equity = np.cumsum(pnl)
    drawdown = float((equity - np.maximum.accumulate(np.r_[0.0, equity])[:-1]).min())
    sharpe = pnl.mean() / pnl.std(ddof=1) * math.sqrt(252) if pnl.std() > 0 else 0.0
    return {"rule": label, "sharpe": sharpe, "per_year": pnl.sum() / (len(pnl) / 252),
            "years": f"{sum(v > 0 for v in by_year)}/{len(by_year)}", "drawdown": drawdown,
            "trades": trades}  # fmt: skip


def line(label: str, results: dict[str, dict], extra: str = "") -> str:
    text = f"{label:26}{results['1x']['trades']:>8}"
    for mult, r in results.items():
        text += f" |{mult:>3} {r['sharpe']:>6.2f} {r['per_year']:>8,.0f} {r['years']:>6} {r['drawdown']:>9,.0f}"
    return text + extra


HEAD = (f"{'rule':26}{'trades':>8} |    {'Sharpe':>6} {'$/year':>8} {'years+':>6} {'drawdown':>9}"
        " (repeated for each slippage level)")  # fmt: skip


def stock_report(base: Path, sessions: np.ndarray) -> None:
    files = [pq.read_table(f) for f in sorted(glob.glob(str(base / "trades" / "*.parquet")))]
    t = pa.concat_tables([f for f in files if f.num_columns], promote_options="default")
    d = {k: t[k].to_numpy(zero_copy_only=False) for k in t.column_names}
    day = d["day"].astype("datetime64[D]")
    index = np.searchsorted(sessions, day)
    shares = np.floor(STOCK_POSITION / d["entry"])
    side = d["direction"].astype(float)
    variants = {
        "A1 5-min, stop, both": ("or5", "stop", None), "A2 5-min, stop, long": ("or5", "stop", 1),
        "A1 short side only": ("or5", "stop", -1), "A3 15-min, stop, both": ("or15", "stop", None),
        "A4 VWAP exit": ("or5", "vwap", None), "A5 EMA9 1m exit": ("or5", "ema9", None),
        "A6 EMA20 1m exit": ("or5", "ema20", None), "A7 SMA20 1m exit": ("or5", "sma20", None),
        "A8 EMA9 5m exit": ("or5", "ema9_5m", None), "A9 EMA20 5m exit": ("or5", "ema20_5m", None),
    }  # fmt: skip
    print("\nA and D on stocks in play: $4,000 a position")
    print(HEAD)
    for label, (rng, exit_rule, only) in variants.items():
        pick = (d["range"] == rng) & (shares > 0)
        if only is not None:
            pick &= side == only
        out_price = d[exit_rule][pick]
        n, entry, s = shares[pick], d["entry"][pick], side[pick]
        gross = s * (out_price - entry) * n
        commission = np.minimum(np.maximum(MIN_COMMISSION, COMMISSION * n), 0.01 * n * entry)
        commission = commission + np.minimum(np.maximum(MIN_COMMISSION, COMMISSION * n),
                                             0.01 * n * out_price)  # fmt: skip
        results = {}
        for mult in (1, 2, 4):
            net = gross - commission - mult * STOCK_SLIP * n * (entry + out_price)
            daily = np.bincount(index[pick], weights=net, minlength=len(sessions))
            results[f"{mult}x"] = summary(label, sessions, daily, int(pick.sum()))
        move = s * (out_price - entry) / entry
        risk = s * (out_price - entry) / (STOP_ATR * d["atr"][pick])
        extra = (f" | win {100 * (gross > 0).mean():.0f}% gross {100 * move.mean():+.3f}% "
                 f"of the position, {risk.mean():+.3f} R")  # fmt: skip
        print(line(label, results, extra))


def etf_report(base: Path) -> None:
    for symbol in ("QQQ", "SPY"):
        days = etf_days(base, symbol)
        dates = np.array([d["day"] for d in days])
        rules: dict[str, list[np.ndarray]] = {"B VWAP trend": [vwap_signal(d) for d in days],
                                              "C noise area": noise_signals(days)}  # fmt: skip
        rules.update({f"D {k}": v for k, v in average_signals(days).items()})
        print(f"\n{symbol}: one $20,000 position, flat at the close")
        print(HEAD)
        for name, signals in rules.items():
            for long_only in (False, True):
                if long_only and name.startswith("C"):
                    continue
                profit, traded, orders = (np.zeros(len(days)) for _ in range(3))
                for i, (d, signal) in enumerate(zip(days, signals, strict=True)):
                    n = math.floor(ACCOUNT / d["open"][0])
                    per_share, turnover, count = run_signal(d, signal, long_only)
                    profit[i], traded[i], orders[i] = per_share * n, turnover * n, count
                commission = np.maximum(orders * MIN_COMMISSION, COMMISSION * traded)
                results = {
                    f"{m}x": summary(name, dates, profit - commission - m * ETF_SLIP * traded,
                                     int(orders.sum()))
                    for m in (0, 1, 2)
                }  # fmt: skip
                print(line(f"{name}{' long only' if long_only else ''}", results,
                           f" | {orders.mean():.1f} orders a day"))  # fmt: skip


def report(base: Path, store: DataStore) -> None:
    from datetime import date

    calendar = store.calendar(date(2003, 9, 10), DEVELOPMENT_END).to_pylist()
    sessions = np.array([r["date"] for r in calendar]).astype("datetime64[D]")
    stock_report(base, sessions)
    etf_report(base)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("candidates", "trades", "report"))
    parser.add_argument("--budget", type=float, default=150.0)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "momentum"
    if args.stage == "candidates":
        candidates(base, store)
    elif args.stage == "report":
        report(base, store)
    else:
        from datetime import date

        months: dict[str, list[str]] = {}
        for row in store.calendar(date(2003, 9, 10), DEVELOPMENT_END).to_pylist():
            d = row["date"]
            path = store.bars_root / "minute" / f"year={d.year}" / f"{d.isoformat()}.parquet"
            months.setdefault(d.isoformat()[:7], []).append(str(path))
        pending = [m for m in months if not (base / "trades" / f"{m}.parquet").exists()]
        deadline = time.time() + args.budget
        jobs = [{"month": m, "files": months[m], "base": str(base), "deadline": deadline}
                for m in pending]  # fmt: skip
        with ProcessPoolExecutor(args.workers) as pool:
            done = sum(r is not None for r in pool.map(trades_month, jobs))
        print(f"months {len(months)}, done now {done}, pending {len(pending) - done}")


if __name__ == "__main__":
    main()
