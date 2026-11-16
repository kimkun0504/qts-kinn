"""Real fills of the opening range breakout (strategies/intraday_momentum/HYPOTHESIS.md,
addenda of 2026-11-16 01:10 and 02:20 ET), from the ticks the owner downloaded for 630 sampled
development trades. Starts no run.

    uv run python research/claude/momentum_fill_cost.py --budget 150    # measure, resumable
    uv run python research/claude/momentum_fill_cost.py --report
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import time
from datetime import date

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn import fill_check
from kinn.core.settings import load_settings
from kinn.data import quotes
from kinn.data.store import DataStore

NAME = "momentum_fills"
NS = 1_000_000_000
STOP_ATR = 0.10


def _read(path) -> list[dict]:
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def measure(w: dict, level: float, raw, ineligible: frozenset[int]) -> dict | None:
    day, symbol, side = w["day"], w["symbol"], int(w["direction"])
    quote_path = quotes.sample_file(raw, "quotes", day, symbol)
    trade_path = quotes.sample_file(raw, "trades", day, symbol)
    if not quote_path.exists() or not trade_path.exists():
        return None
    start, end = w["start_ns"], w["end_ns"]
    book = [q for q in _read(quote_path)
            if q.get("bid_price", 0) > 0 and q.get("ask_price", 0) >= q["bid_price"]]  # fmt: skip
    stamps = np.array([q["sip_timestamp"] for q in book])
    prints = [t for t in _read(trade_path)
              if t.get("price", 0) > 0 and not t.get("correction")
              and not set(t.get("conditions") or ()) & ineligible
              and start <= t["sip_timestamp"] < end]  # fmt: skip
    row = {"day": day, "symbol": symbol, "side": side, "level": level,
           "study_entry": w["entry_price"], "atr": float(w["atr"]),
           "quotes": len(book), "prints": len(prints)}  # fmt: skip

    def quote_at(ts: int) -> dict | None:
        at = int(np.searchsorted(stamps, ts, side="right")) - 1
        return book[at] if at >= 0 else None

    def taken(ts: int) -> float | None:  # what a market order in `side` direction pays
        q = quote_at(ts)
        return None if q is None else (q["ask_price"] if side > 0 else q["bid_price"])

    def given(ts: int) -> float | None:  # what a market order closing the position gets
        q = quote_at(ts)
        return None if q is None else (q["bid_price"] if side > 0 else q["ask_price"])

    trigger = next((t for t in prints if side * (t["price"] - level) > 0), None)
    row["triggered"] = trigger is not None
    for key in ("trigger_seconds", "trigger_price", "fill_0", "fill_1", "half_spread",
                "mid", "stop_seconds", "stop_fill_0", "stop_fill_1"):  # fmt: skip
        row[key] = None
    if trigger is None:
        return row
    at = trigger["sip_timestamp"]
    row["trigger_seconds"] = (at - start) / NS
    row["trigger_price"] = trigger["price"]
    row["fill_0"], row["fill_1"] = taken(at), taken(at + NS)
    seconds = np.arange(at + NS, end, NS)
    idx = np.searchsorted(stamps, seconds, side="right") - 1
    idx = idx[idx >= 0]
    if len(idx):
        bid = np.array([book[i]["bid_price"] for i in idx])
        ask = np.array([book[i]["ask_price"] for i in idx])
        ok = ask < 1.2 * bid  # leave out stub quotes
        if ok.any():
            row["half_spread"] = float(((ask - bid) / 2)[ok].mean())
            row["mid"] = float(((ask + bid) / 2)[ok].mean())
    stop = w["entry_price"] - side * STOP_ATR * float(w["atr"])
    row["stop"] = stop
    hit = next((t for t in prints
                if t["sip_timestamp"] > at and side * (t["price"] - stop) <= 0), None)  # fmt: skip
    if hit is not None:
        ts = hit["sip_timestamp"]
        row["stop_seconds"] = (ts - start) / NS
        row["stop_fill_0"], row["stop_fill_1"] = given(ts), given(ts + NS)
    return row


def run(budget: float) -> None:
    settings = load_settings()
    plan = settings.data_dir / "quotes_sample" / NAME
    raw = settings.raw_dir / "massive" / "quotes_sample" / NAME
    out = settings.data_dir / "research" / "momentum" / "fill_cost.parquet"
    done = pq.read_table(out).to_pylist() if out.exists() else []
    seen = {(r["day"], r["symbol"]) for r in done}
    ineligible, source = fill_check.ineligible_conditions(raw)
    base = settings.data_dir / "research" / "momentum"
    levels = {
        (r[0], r[1]): (r[2], r[3])
        for r in duckdb.sql(
            f"""select day, symbol, range_high, range_low
                from '{base}/candidates.parquet' where range = 'or5'"""
        ).fetchall()
    }
    deadline = time.time() + budget
    with open(plan / "windows.csv") as handle:
        windows = list(csv.DictReader(handle))
    for w in windows:
        w["day"] = date.fromisoformat(w["day"])
        for key in ("start_ns", "end_ns"):
            w[key] = int(w[key])
        w["entry_price"] = float(w["entry_price"])
        key = (w["day"], w["symbol"])
        if key in seen:
            continue
        if time.time() > deadline:
            break
        high, low = levels[key]
        row = measure(w, high if int(w["direction"]) > 0 else low, raw, ineligible)
        if row:
            done.append(row)
            seen.add(key)
    tmp = out.with_suffix(".tmp")
    pq.write_table(pa.Table.from_pylist(done), tmp)
    tmp.replace(out)
    print(f"conditions: {source}; measured {len(done)} of {len(windows)}")


def report() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "momentum"
    rows = duckdb.sql(
        f"""select f.*, f.side * (c.or_open / p.prev_close - 1) as gap
            from '{base}/fill_cost.parquet' f
            join '{base}/candidates.parquet' c
              on c.day = f.day and c.symbol = f.symbol and c.range = 'or5'
            join read_parquet('{store.root}/panel/*.parquet') p
              on p.date = f.day and p.symbol = f.symbol"""
    ).to_arrow_table().to_pylist()  # fmt: skip

    def col(name: str) -> np.ndarray:
        return np.array([np.nan if r[name] is None else r[name] for r in rows], dtype=float)

    side, level, entry = col("side"), col("level"), col("study_entry")
    year = np.array([r["day"].year for r in rows])
    ok = np.array([bool(r["triggered"]) for r in rows]) & ~np.isnan(col("fill_1"))
    sane = ok & (np.abs(col("fill_1") / entry - 1) < 0.05)
    print(f"sampled {len(rows)}; trigger found in the ticks: {int(ok.sum())}; "
          f"usable quotes: {int(sane.sum())}; trigger inside the entry bar: "
          f"{100 * np.mean(col('trigger_seconds')[ok] < 60):.0f}%")  # fmt: skip
    slip0 = side * (col("fill_0") - entry)
    slip1 = side * (col("fill_1") - entry)
    half = col("half_spread")
    stop_slip = side * (col("stop") - col("stop_fill_1"))
    stopped = ~np.isnan(col("stop_seconds"))

    def show(label: str, pick: np.ndarray) -> None:
        pick = pick & sane
        if pick.sum() < 5:
            print(f"{label:30} n={int(pick.sum())}")
            return
        e, h = slip1[pick], half[pick]
        px = entry[pick]
        st = stop_slip[pick & stopped & (np.abs(stop_slip) < 0.05 * entry)]
        side_cost = (np.nanmean(e) + np.nanmean(h)) / 2
        side_bp = (np.nanmean(e / px) + np.nanmean(h / px)) / 2 * 1e4
        print(f"{label:30} n={int(pick.sum()):4d} price {np.median(px):6.1f} | entry vs study: "
              f"mean {100 * np.nanmean(e):5.2f}c median {100 * np.nanmedian(e):5.2f}c "
              f"({1e4 * np.nanmean(e / px):5.1f} bp) | at once {100 * np.nanmean(slip0[pick]):5.2f}c"
              f" | half-spread mean {100 * np.nanmean(h):5.2f}c median {100 * np.nanmedian(h):5.2f}c"
              f" ({1e4 * np.nanmean(h / px):5.1f} bp) | COST A SIDE {100 * side_cost:5.2f}c "
              f"{side_bp:5.1f} bp | stop slip mean {100 * np.mean(st):5.2f}c n={len(st)}")  # fmt: skip

    everything = np.ones(len(rows), dtype=bool)
    show("all sampled trades", everything)
    show("gap with, 3% or more", col("gap") >= 0.03)
    show("gap under 3%", col("gap") < 0.03)
    show("long", side > 0)
    show("short", side < 0)
    for a, b in ((5, 20), (20, 50), (50, 100), (100, 1e9)):
        show(f"price ${a} to {'up' if b > 1e8 else b}", (entry >= a) & (entry < b))
    for a, b in ((2003, 2006), (2007, 2009), (2010, 2012), (2013, 2016)):
        show(f"{a} to {b}", (year >= a) & (year <= b))
    in_bar = stopped & (col("stop_seconds") < 60)
    print(f"\nfixed stop: reached within 20 minutes in {100 * stopped[sane].mean():.0f}% of trades; "
          f"inside the entry bar, after the entry, in {100 * in_bar[sane].mean():.0f}%; median "
          f"seconds from trigger to stop "
          f"{np.nanmedian((col('stop_seconds') - col('trigger_seconds'))[sane & stopped]):.0f}")  # fmt: skip
    worse = slip1[sane]
    print(f"entry slippage distribution (cents): 10th {100 * np.nanquantile(worse, 0.1):.1f}, "
          f"25th {100 * np.nanquantile(worse, 0.25):.1f}, 75th {100 * np.nanquantile(worse, 0.75):.1f}, "
          f"90th {100 * np.nanquantile(worse, 0.9):.1f}")  # fmt: skip


BUCKETS = ((5, 20), (20, 50), (50, 100), (100, 1e9))


def apply() -> None:
    """The development trades again, with the measured costs in place of the assumed ones:
    entry slippage and exit half-spread as basis points of the price, by price bucket."""
    import glob
    import math

    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "momentum"
    fills = pq.read_table(base / "fill_cost.parquet").to_pylist()

    def col(name: str) -> np.ndarray:
        return np.array([np.nan if r[name] is None else r[name] for r in fills], dtype=float)

    side, entry = col("side"), col("study_entry")
    sane = ~np.isnan(col("fill_1")) & (np.abs(col("fill_1") / entry - 1) < 0.05)
    cost = {}
    for name, fill in (("one second later", "fill_1"), ("at the trigger", "fill_0")):
        slip, half = side * (col(fill) - entry) / entry, col("half_spread") / entry
        cost[name] = [(float(np.nanmean(slip[sane & (entry >= a) & (entry < b)])),
                       float(np.nanmean(half[sane & (entry >= a) & (entry < b)])))
                      for a, b in BUCKETS]  # fmt: skip
        print(name, "entry / exit bp by price bucket:",
              [(round(1e4 * e, 1), round(1e4 * x, 1)) for e, x in cost[name]])  # fmt: skip
    files = [pq.read_table(f) for f in sorted(glob.glob(str(base / "trades" / "*.parquet")))]
    trades = pa.concat_tables([f for f in files if f.num_columns], promote_options="default")
    con = duckdb.connect()
    con.register("trades", trades)
    joined = con.sql(
        f"""select t.*, t.direction * (c.or_open / p.prev_close - 1) as gap
            from trades t
            join '{base}/candidates.parquet' c
              on c.day = t.day and c.symbol = t.symbol and c.range = t.range
            join read_parquet('{store.root}/panel/*.parquet') p
              on p.date = t.day and p.symbol = t.symbol
            where t.range = 'or5'"""
    ).to_arrow_table()
    d = {k: joined[k].to_numpy(zero_copy_only=False) for k in joined.column_names}
    calendar = store.calendar(date(2003, 9, 10), date(2016, 12, 30)).to_pylist()
    sessions = np.array([r["date"] for r in calendar]).astype("datetime64[D]")
    years = sessions.astype("datetime64[Y]").astype(int) + 1970
    index = np.searchsorted(sessions, d["day"].astype("datetime64[D]"))
    e, s = d["entry"], d["direction"].astype(float)
    bucket = np.digitize(e, [b for _, b in BUCKETS[:-1]])
    groups = {
        "all trades": np.ones(len(e), dtype=bool),
        "gap with, 3% or more": d["gap"] >= 0.03,
        "price $20 to $100": (e >= 20) & (e < 100),
        "gap 3%+ and $20 to $100": (d["gap"] >= 0.03) & (e >= 20) & (e < 100),
        "long only": s > 0,
        "short only": s < 0,
        "gap 3%+, long only": (d["gap"] >= 0.03) & (s > 0),
        "gap 3%+, short only": (d["gap"] >= 0.03) & (s < 0),
    }
    for exit_rule in ("vwap", "stop"):
        for name, table in cost.items():
            print(f"\nexit {exit_rule}; entry filled {name}")
            for label, pick in groups.items():
                n = np.floor(4000 / e[pick])
                out_price = d[exit_rule][pick]
                slip_in = np.array([table[b][0] for b in bucket[pick]])
                slip_out = np.array([table[b][1] for b in bucket[pick]])
                net = (s[pick] * (out_price - e[pick]) * n - 2 * np.maximum(0.35, 0.0035 * n)
                       - n * e[pick] * slip_in - n * out_price * slip_out)  # fmt: skip
                daily = np.bincount(index[pick], weights=net, minlength=len(sessions))
                equity = np.cumsum(daily)
                worst = (equity - np.maximum.accumulate(np.r_[0.0, equity])[:-1]).min()
                good = sum(daily[years == y].sum() > 0 for y in np.unique(years))
                print(f"  {label:26} trades {int(pick.sum()):6d} net/trade ${net.mean():6.2f} "
                      f"Sharpe {daily.mean() / daily.std(ddof=1) * math.sqrt(252):5.2f} "
                      f"${daily.sum() / 13.3:8,.0f}/yr years {good:2d}/14 drawdown {worst:9,.0f}")  # fmt: skip


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=float, default=150.0)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        apply()
    elif args.report:
        report()
    else:
        run(args.budget)
