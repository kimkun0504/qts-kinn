"""The reversal-confirmation study (rebound_limit HYPOTHESIS.md, addendum of 2026-11-15
23:50 ET): entry signals E0-E7 and exits X0-X4 measured on every development event saved by
reversal_events.py. Every rule's definition is in that addendum; this file implements them.

    uv run python research/claude/reversal_study.py --budget 150 --workers 4   # per-month trades
    uv run python research/claude/reversal_study.py --report                    # the tables
"""

from __future__ import annotations

import argparse
import glob
import math
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings

COST = 0.01  # round trip, of the position (see the addendum)
WINDOW = 90  # minutes after the event in which a signal may fire
LAST_SIGNAL_BEFORE_CLOSE = 15
ENTRIES = ("E0", "E2", "E3", "E4", "E5", "E6", "E7")
EXITS = ("X0", "X1", "X2", "X3", "X4")
_ERF = np.frompyfunc(math.erf, 1, 1)


def _phi(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + _ERF(z / math.sqrt(2.0)).astype(float))


def signals(ev: dict, b: dict) -> dict[str, tuple[int, int]]:
    """For each entry rule that fires: (signal bar index, index of the low it refers to)."""
    m, h, lo, c, v = b["minute"], b["high"], b["low"], b["close"], b["volume"]
    n = len(m)
    hit = np.flatnonzero(m == ev["minute"])
    if not len(hit):
        return {}
    i0 = int(hit[0])
    last_minute = min(ev["minute"] + WINDOW, ev["close_minute"] - LAST_SIGNAL_BEFORE_CLOSE)
    jmax = int(np.searchsorted(m, last_minute, side="right")) - 1
    jmax = min(jmax, n - 2)  # a signal needs a later bar to buy on
    out: dict[str, tuple[int, int]] = {}
    if i0 <= n - 2:
        out["E0"] = (i0, i0)
    dollar = c * v
    normal = ev["adv20"] / 390.0
    tp = (h + lo + c) / 3.0
    since = slice(i0, n)
    avwap = np.full(n, np.nan)
    cum_v = np.cumsum(v[since].astype(float))
    with np.errstate(invalid="ignore", divide="ignore"):
        avwap[since] = np.cumsum(tp[since] * v[since]) / cum_v
    below = np.zeros(n, dtype=int)
    below[since] = np.cumsum(c[since] < avwap[since])
    # Bulk volume classification: buy share of each bar from its close-to-close change,
    # scaled by the standard deviation of the session's changes so far (at least 10).
    change = np.diff(c, prepend=c[0])
    count = np.arange(n, dtype=float)  # changes seen up to and including bar k
    total, squares = np.cumsum(change), np.cumsum(change**2)
    with np.errstate(invalid="ignore", divide="ignore"):
        spread = np.sqrt(np.maximum(squares / count - (total / count) ** 2, 0.0))
        buy = np.where((count >= 10) & (spread > 0), _phi(change / spread), np.nan)
    known = ~np.isnan(buy) & (v > 0)
    num = np.cumsum(np.where(known, buy * v, 0.0))
    den = np.cumsum(np.where(known, v, 0.0))
    lag_num, lag_den = np.r_[np.zeros(5), num][:n], np.r_[np.zeros(5), den][:n]
    with np.errstate(invalid="ignore", divide="ignore"):
        buy5 = (num - lag_num) / (den - lag_den)  # volume-weighted over the last 5 bars
    prior_high = np.full(n, np.inf)  # highest high of the 5 bars before each bar
    if n > 5:
        prior_high[5:] = np.lib.stride_tricks.sliding_window_view(h, 5)[:-1].max(axis=1)

    low, i_low = float(lo[i0]), i0
    high, pulled = None, False  # E3 state: the bounce high after the low, and a pullback seen
    for j in range(i0 + 1, jmax + 1):
        new_low = lo[j] < low
        if new_low:
            if (
                "E2" not in out
                and h[j] > lo[j]
                and dollar[j] >= 5 * normal
                and dollar[j] >= 2 * dollar[max(j - 5, 0) : j].mean()
                and (c[j] - lo[j]) >= (2.0 / 3.0) * (h[j] - lo[j])
            ):
                out["E2"] = (j, j)
            low, i_low, high, pulled = float(lo[j]), j, None, False
            continue
        if "E3" not in out:
            if pulled and high is not None and c[j] > high:
                out["E3"] = (j, i_low)
            elif high is None or h[j] > high:
                high, pulled = float(h[j]), False
            elif high > low and lo[j] <= high - (high - low) / 3.0:
                pulled = True
        aged = j - i_low >= 3
        if "E4" not in out and aged and c[j] > prior_high[j]:
            out["E4"] = (j, i_low)
        if "E5" not in out and buy5[j] >= 0.60 and buy5[i_low] <= 0.40:
            out["E5"] = (j, i_low)
        if "E6" not in out and aged and below[j - 1] >= 5 and c[j] > avwap[j]:
            out["E6"] = (j, i_low)
    # E7: still 10% down 31 minutes before the close; buy at the open 30 minutes before it.
    k = int(np.searchsorted(m, ev["close_minute"] - 31, side="right")) - 1
    e = int(np.searchsorted(m, ev["close_minute"] - 30, side="left"))
    if k >= i0 and e < n and c[k] <= 0.9 * ev["prev_close"]:
        out["E7"] = (e - 1, int(i0 + np.argmin(lo[i0 : k + 1])))
    return out


def exits(ev: dict, b: dict, j: int, i_low: int) -> dict[str, float] | None:
    """Gross return of buying at the open of bar j+1 under each exit rule."""
    m, o, h, lo, c, v = b["minute"], b["open"], b["high"], b["low"], b["close"], b["volume"]
    n, e = len(m), j + 1
    entry = float(o[e])
    final = ev["official_close"] or float(c[-1])
    if not entry > 0:
        return None

    def sold(k: int) -> float:  # exit at the open after bar k, or at the close
        return float(o[k + 1]) if k + 1 < n else final

    def first(mask: np.ndarray, start: int) -> int | None:  # first True at or after `start`
        found = np.flatnonzero(mask[start:])
        return start + int(found[0]) if len(found) else None

    out = {"X0": final}
    k1 = first(c < float(lo[i_low]), e)
    out["X1"] = sold(k1) if k1 is not None else final
    prev = np.r_[c[0], c[:-1]]
    true_range = np.maximum(h, prev) - np.minimum(lo, prev)
    atr = float(true_range[max(j - 13, 0) : j + 1].mean())
    peak = np.r_[np.full(e, np.inf), np.maximum.accumulate(h[e:])]
    k2 = first(c < peak - 3 * atr, e) if atr > 0 else None
    out["X2"] = sold(k2) if k2 is not None else final
    tp = (h + lo + c) / 3.0
    anchored = np.full(n, np.nan)
    anchored[i_low:] = np.cumsum(tp[i_low:] * v[i_low:]) / np.maximum(np.cumsum(v[i_low:]), 1)
    with np.errstate(invalid="ignore"):
        under = c < anchored
    k3 = first(under & np.r_[False, under[:-1]], e + 1) if e + 1 < n else None
    out["X3"] = sold(k3) if k3 is not None else final
    k4 = int(np.searchsorted(m, m[e] + 30, side="left"))
    out["X4"] = sold(k4) if k4 < n and c[k4] < entry else final
    return {name: price / entry - 1.0 for name, price in out.items()}


def month_job(job: dict) -> str | None:
    if time.time() > job["deadline"]:
        return None
    base = Path(job["base"])
    events = pq.read_table(base / f"{job['month']}.events.parquet")
    rows = []
    if events.num_columns:
        bars = pq.read_table(base / f"{job['month']}.bars.parquet")
        spy = pq.read_table(base / f"{job['month']}.spy.parquet").to_pydict()
        market: dict = {}
        for day, minute, close in zip(spy["day"], spy["minute"], spy["close"], strict=True):
            market.setdefault(day, ([], []))
            market[day][0].append(minute)
            market[day][1].append(close)
        cols = {k: bars[k].to_numpy(zero_copy_only=False) for k in bars.column_names}
        key = np.char.add(cols["day"].astype(str), cols["symbol"].astype(str))
        starts = np.flatnonzero(np.r_[True, key[1:] != key[:-1]])
        ends = np.r_[starts[1:], len(key)]
        where = {key[a]: (a, b) for a, b in zip(starts, ends, strict=True)}
        for ev in events.to_pylist():
            span = where.get(f"{ev['day']}{ev['symbol']}")
            if span is None:
                continue
            a, z = span
            b = {k: cols[k][a:z].astype(float) for k in ("open", "high", "low", "close")}
            b["minute"] = cols["minute"][a:z].astype(int)
            b["volume"] = cols["volume"][a:z].astype(float)
            trades = cols["transactions"][a:z].astype(float)
            i0 = int(np.searchsorted(b["minute"], ev["minute"]))
            earlier_v, earlier_n = b["volume"][:i0].sum(), np.nansum(trades[:i0])
            size_ratio = None
            if earlier_n > 0 and i0 < len(trades) and trades[i0] > 0:
                size_ratio = (b["volume"][i0] / trades[i0]) / (earlier_v / earlier_n)
            minutes, closes = market.get(ev["day"], ([], []))
            at = int(np.searchsorted(minutes, ev["minute"], side="right")) - 1
            spy_ret = closes[at] / closes[0] - 1.0 if at >= 0 and closes else None
            for rule, (j, i_low) in signals(ev, b).items():
                result = exits(ev, b, j, i_low)
                if result is None:
                    continue
                rows.append(
                    {
                        "day": ev["day"],
                        "symbol": ev["symbol"],
                        "rule": rule,
                        "event_minute": ev["minute"],
                        "entry_minute": int(b["minute"][j + 1]),
                        "ret15": ev["ret15"],
                        "spy_ret": spy_ret,
                        "size_ratio": size_ratio,
                        "marketcap": ev["marketcap"],
                        "entry_price": float(b["open"][j + 1]),
                        **result,
                    }  # fmt: skip
                )
    out = base / "study"
    out.mkdir(exist_ok=True)
    tmp = out / f"{job['month']}.tmp"
    pq.write_table(pa.Table.from_pylist(rows) if rows else pa.table({}), tmp)
    tmp.replace(out / f"{job['month']}.parquet")
    return job["month"]


def line(label: str, days: np.ndarray, net: np.ndarray, gross: np.ndarray) -> dict:
    if not len(net):
        return {"rule": label, "trades": 0}
    order = np.argsort(days, kind="stable")
    days, net = days[order], net[order]
    starts = np.flatnonzero(np.r_[True, days[1:] != days[:-1]])
    daily = np.add.reduceat(net, starts) / np.diff(np.r_[starts, len(net)])
    t = daily.mean() / (daily.std(ddof=1) / math.sqrt(len(daily))) if len(daily) > 2 else 0.0
    years = days.astype("datetime64[Y]").astype(int) + 1970
    good = sum(net[years == y].mean() > 0 for y in np.unique(years))
    quiet = ~np.isin(years, (2008, 2009))
    return {
        "rule": label, "trades": len(net), "gross": 100 * gross.mean(),
        "net": 100 * net.mean(), "t": t, "win": 100 * (net > 0).mean(),
        "years+": f"{good}/{len(np.unique(years))}",
        "net_ex_08_09": 100 * net[quiet].mean() if quiet.any() else float("nan"),
        "worst": 100 * net.min(),
    }  # fmt: skip


def report(base: Path) -> None:
    files = [pq.read_table(f) for f in sorted(glob.glob(str(base / "study" / "*.parquet")))]
    t = pa.concat_tables([f for f in files if f.num_columns], promote_options="default")
    d = {k: t[k].to_numpy(zero_copy_only=False) for k in t.column_names}
    days = d["day"].astype("datetime64[D]")
    rows = []
    for rule in ENTRIES:
        pick = d["rule"] == rule
        rows.append(line(f"{rule} X0", days[pick], d["X0"][pick] - COST, d["X0"][pick]))
    table(rows, "Entry signals, sold at the close")
    rows = []
    for rule in ENTRIES:
        for x in EXITS[1:]:
            pick = d["rule"] == rule
            rows.append(line(f"{rule} {x}", days[pick], d[x][pick] - COST, d[x][pick]))
    table(rows, "Exits (all signals shown; the plan reads E0 and the two best)")
    spy = np.array([np.nan if x is None else x for x in d["spy_ret"]], dtype=float)
    size = np.array([np.nan if x is None else x for x in d["size_ratio"]], dtype=float)
    splits = {
        "market above -1%": spy > -0.01, "market at or below -1%": spy <= -0.01,
        "fast fall (5% in 15 min)": d["ret15"] <= -0.05, "slower fall": d["ret15"] > -0.05,
        "large prints (2x)": size >= 2, "normal prints": size < 2,
        "before 11:00": d["event_minute"] < 660,
        "11:00 to 14:00": (d["event_minute"] >= 660) & (d["event_minute"] < 840),
        "after 14:00": d["event_minute"] >= 840,
    }  # fmt: skip
    for rule in ENTRIES:
        rows = []
        for label, mask in splits.items():
            pick = (d["rule"] == rule) & mask
            rows.append(line(f"{rule} {label}", days[pick], d["X0"][pick] - COST, d["X0"][pick]))
        table(rows, f"Context splits of {rule}, sold at the close")


def table(rows: list[dict], title: str) -> None:
    print(f"\n{title}")
    print(f"{'rule':34}{'trades':>8}{'gross%':>8}{'net%':>8}{'t':>7}{'win%':>7}"
          f"{'years+':>8}{'ex0809%':>9}{'worst%':>8}")  # fmt: skip
    for r in rows:
        if not r["trades"]:
            print(f"{r['rule']:34}{0:>8}")
            continue
        print(
            f"{r['rule']:34}{r['trades']:>8}{r['gross']:>8.2f}{r['net']:>8.2f}{r['t']:>7.2f}"
            f"{r['win']:>7.1f}{r['years+']:>8}{r['net_ex_08_09']:>9.2f}{r['worst']:>8.1f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=float, default=150.0)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    base = load_settings().data_dir / "research" / "reversal"
    if args.report:
        report(base)
        return
    months = sorted(Path(f).name[:7] for f in glob.glob(str(base / "*.events.parquet")))
    pending = [m for m in months if not (base / "study" / f"{m}.parquet").exists()]
    deadline = time.time() + args.budget
    jobs = [{"month": m, "base": str(base), "deadline": deadline} for m in pending]
    with ProcessPoolExecutor(args.workers) as pool:
        done = sum(r is not None for r in pool.map(month_job, jobs))
    print(f"months {len(months)}, done now {done}, pending {len(pending) - done}")


if __name__ == "__main__":
    main()
