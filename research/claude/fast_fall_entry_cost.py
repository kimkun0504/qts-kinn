"""What it costs to buy a fast fall at once (rebound_limit HYPOTHESIS.md, addendum of
2026-11-16 00:10 ET). Reads quotes and trades already on disk for sampled events, development
years only. Starts no run.

    uv run python research/claude/fast_fall_entry_cost.py --budget 150      # measure, resumable
    uv run python research/claude/fast_fall_entry_cost.py --report
"""

from __future__ import annotations

import argparse
import csv
import glob
import gzip
import json
import time
from datetime import date
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings
from kinn.data import quotes
from kinn.validation.targets import DEVELOPMENT_END

FAST = -0.05
DELAYS = (1, 5, 30)
OTHER_COSTS = 0.0045
PLANS = (
    "20261115T191143Z_claude_intraday_rebound_217e2dd7",  # drawn at random from all events
    "fillcheck_x_o4",
    "fillcheck_s_l468",
)
NS = 1_000_000_000


def _tables(pattern: str) -> pa.Table:
    found = [pq.read_table(f) for f in sorted(glob.glob(pattern))]
    return pa.concat_tables([t for t in found if t.num_columns], promote_options="default")


def fast_events(base: Path) -> dict[tuple, dict]:
    """Every development fast fall: (day, symbol) -> its event, the study's entry price and
    return, and whether the low reached 4% under the event close within 10 minutes."""
    events = {
        (e["day"], e["symbol"]): e for e in _tables(str(base / "*.events.parquet")).to_pylist()
    }
    study = _tables(str(base / "study" / "*.parquet")).to_pylist()
    out = {}
    for row in study:
        if row["rule"] == "E0" and row["ret15"] is not None and row["ret15"] <= FAST:
            key = (row["day"], row["symbol"])
            out[key] = {**events[key], "study_entry": row["entry_price"], "study_return": row["X0"]}
    for path in sorted(glob.glob(str(base / "*.bars.parquet"))):
        if "low" not in pq.read_schema(path).names:
            continue  # a month with no event
        cols = pq.read_table(path, columns=["day", "symbol", "minute", "low"]).to_pydict()
        deepest: dict[tuple, float] = {}
        for day, symbol, minute, low in zip(*cols.values(), strict=True):
            event = out.get((day, symbol))
            if event and event["minute"] < minute <= event["minute"] + 10:
                deepest[(day, symbol)] = min(low, deepest.get((day, symbol), low))
        for key, low in deepest.items():
            out[key]["fell_on"] = low <= 0.96 * out[key]["event_close"]
    for event in out.values():
        event.setdefault("fell_on", False)
    return out


def _read(path: Path) -> list[dict]:
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def measure(event: dict, raw: Path) -> dict | None:
    day, symbol = event["day"], event["symbol"]
    quote_path = quotes.sample_file(raw, "quotes", day, symbol)
    if not quote_path.exists():
        return None
    t0 = quotes.minute_ns(day, event["minute"] + 1)  # the close of the event bar
    valid = [q for q in _read(quote_path)
             if q.get("bid_price", 0) > 0 and q.get("ask_price", 0) >= q["bid_price"]]  # fmt: skip
    stamps = np.array([q["sip_timestamp"] for q in valid])
    row = {"day": day, "symbol": symbol, "fell_on": event["fell_on"], "adv20": event["adv20"],
           "marketcap": event["marketcap"], "event_close": event["event_close"],
           "study_entry": event["study_entry"], "study_return": event["study_return"],
           "official_close": event["official_close"]}  # fmt: skip
    for delay in DELAYS:
        at = int(np.searchsorted(stamps, t0 + delay * NS, side="right")) - 1
        quote = valid[at] if at >= 0 else None
        row[f"bid_{delay}"] = quote["bid_price"] if quote else None
        row[f"ask_{delay}"] = quote["ask_price"] if quote else None
        row[f"ask_size_{delay}"] = quote.get("ask_size") if quote else None
    trade_path = quotes.sample_file(raw, "trades", day, symbol)
    row["traded_30s"], row["shares_30s"] = None, 0
    if trade_path.exists():
        start, end = t0 + 5 * NS, t0 + 35 * NS
        prints = [t for t in _read(trade_path)
                  if start <= t["sip_timestamp"] < end and t.get("price", 0) > 0
                  and not t.get("correction")]  # fmt: skip
        shares = sum(t["size"] for t in prints)
        if shares > 0:
            row["traded_30s"] = sum(t["price"] * t["size"] for t in prints) / shares
            row["shares_30s"] = int(shares)
    return row


def run(budget: float) -> None:
    settings = load_settings()
    base = settings.data_dir / "research" / "reversal"
    out = base / "entry_cost"
    out.mkdir(exist_ok=True)
    events = fast_events(base)
    print(f"fast falls in development: {len(events)}, "
          f"fell on: {sum(e['fell_on'] for e in events.values())}")  # fmt: skip
    deadline = time.time() + budget
    for plan in PLANS:
        target = out / f"{plan}.parquet"
        if target.exists():
            continue
        raw = settings.raw_dir / "massive" / "quotes_sample" / plan
        windows = settings.data_dir / "quotes_sample" / plan / "windows.csv"
        rows, seen = [], set()
        with open(windows) as handle:
            for window in csv.DictReader(handle):
                day = date.fromisoformat(window["day"])
                key = (day, window["symbol"])
                event = events.get(key)
                if (day > DEVELOPMENT_END or event is None or key in seen
                        or int(window["signal_minute"]) != event["minute"]):  # fmt: skip
                    continue
                seen.add(key)
                if time.time() > deadline:
                    print(f"{plan}: out of time after {len(rows)} events; run again")
                    return
                measured = measure(event, raw)
                if measured:
                    rows.append({**measured, "plan": plan})
        pq.write_table(pa.Table.from_pylist(rows), target)
        print(f"{plan}: {len(rows)} fast falls measured")


BINS = ("fell 4% or more", "fell 3 to 4%", "fell 1 to 3%", "held (under 1%)")


def deepest_bins(base: Path, events: dict) -> dict[tuple, int]:
    """Each fast fall by its deepest low in the 10 minutes after the event bar, against the
    event bar's close. The fill-check samples were drawn on exactly this, so averaging the
    sample with the population's share of each bin undoes the selection."""
    deepest: dict[tuple, float] = {}
    for path in sorted(glob.glob(str(base / "*.bars.parquet"))):
        if "low" not in pq.read_schema(path).names:
            continue
        cols = pq.read_table(path, columns=["day", "symbol", "minute", "low"]).to_pydict()
        for day, symbol, minute, low in zip(*cols.values(), strict=True):
            event = events.get((day, symbol))
            if event and event["minute"] < minute <= event["minute"] + 10:
                ratio = low / event["event_close"] - 1
                deepest[(day, symbol)] = min(ratio, deepest.get((day, symbol), ratio))

    def which(key: tuple) -> int:
        r = deepest.get(key, 0.0)
        return 0 if r <= -0.04 else 1 if r <= -0.03 else 2 if r <= -0.01 else 3

    return {key: which(key) for key in events}


def _clipped(x: np.ndarray) -> tuple[float, float, int]:
    """Mean with the top and bottom 1% pulled in, its standard error, and the count."""
    x = x[~np.isnan(x)]
    lo, hi = np.quantile(x, [0.01, 0.99])
    x = np.clip(x, lo, hi)
    return float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))), len(x)


def report() -> None:
    base = load_settings().data_dir / "research" / "reversal"
    events = fast_events(base)
    bins = deepest_bins(base, events)
    rows, seen = [], set()
    for row in _tables(str(base / "entry_cost" / "*.parquet")).to_pylist():
        key = (row["day"], row["symbol"])
        if key not in seen:
            seen.add(key)
            rows.append(row)

    def column(name: str) -> np.ndarray:
        return np.array([np.nan if r[name] is None else r[name] for r in rows], dtype=float)

    in_bin = np.array([bins[(r["day"], r["symbol"])] for r in rows])
    all_bins = np.array(list(bins.values()))
    all_returns = np.array([e["study_return"] for e in events.values()])
    share = np.array([(all_bins == b).mean() for b in range(4)])
    entry, close = column("study_entry"), column("official_close")
    study, event_close = column("study_return"), column("event_close")
    print(f"fast falls in development: {len(events)}; with quotes: {len(rows)}")
    print(
        f"{'':18}{'share of all':>13}{'study return':>14}{'sampled':>9}{'their study return':>20}"
    )
    for b, name in enumerate(BINS):
        print(f"{name:18}{100 * share[b]:>12.1f}%{100 * all_returns[all_bins == b].mean():>13.2f}%"
              f"{int((in_bin == b).sum()):>9}{100 * study[in_bin == b].mean():>19.2f}%")  # fmt: skip
    for delay in DELAYS:
        ask, bid = column(f"ask_{delay}"), column(f"bid_{delay}")
        ok = (ask > 0.3 * event_close) & (ask < 3 * event_close)
        cost = np.where(ok, ask / entry - 1, np.nan)
        to_close = np.where(ok, close / ask - 1, np.nan)
        half = np.where(ok, (ask - bid) / (ask + bid), np.nan)
        total_cost = total_return = variance = 0.0
        print(f"\n{delay} s after the event bar")
        for b, name in enumerate(BINS):
            c, _, _ = _clipped(cost[in_bin == b])
            r, se, n = _clipped(to_close[in_bin == b])
            print(f"  {name:18} ask over the study's price {100 * c:+.2f}%  half-spread (median) "
                  f"{100 * np.nanmedian(half[in_bin == b]):.2f}%  ask to close {100 * r:+.2f}% "
                  f"(se {100 * se:.2f}, n {n})")  # fmt: skip
            total_cost += share[b] * c
            total_return += share[b] * r
            variance += (share[b] * se) ** 2
        print(f"  all fast falls: ask over the study's price {100 * total_cost:+.2f}%; ask to "
              f"close {100 * total_return:+.2f}% (se {100 * variance**0.5:.2f}); net after "
              f"{100 * OTHER_COSTS:.2f}% other costs {100 * (total_return - OTHER_COSTS):+.2f}%")  # fmt: skip
    dollars = column("ask_size_5") * column("ask_5")
    print(f"\nshown at the ask 5 s after: median ${np.nanmedian(dollars):,.0f}; "
          f"$2,000 or more in {100 * np.nanmean(dollars >= 2000):.0f}% of events")  # fmt: skip


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=float, default=150.0)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.report:
        report()
    else:
        run(args.budget)
