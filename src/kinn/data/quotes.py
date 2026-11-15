"""A quote sample around a study's events: what the spread really was.

Three steps, the middle one done by the owner because it needs the vendor key and writes to the
raw folder:

1. ``plan``     pick events from an event-study run and write the windows to fetch.
2. (owner)      ``tools/owner/download_quotes.py`` fetches NBBO quotes and trades for them.
3. ``measure``  compare the quoted spread at each entry with the cost model's fallback.
"""

from __future__ import annotations

import csv
import gzip
import json
import random
from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pyarrow.parquet as pq

from kinn.data import seal

NEW_YORK = ZoneInfo("America/New_York")
BUCKETS = (("ADV under $1M", 0.0, 1e6), ("ADV $1–10M", 1e6, 1e7), ("ADV $10M and over", 1e7, 1e18))
PERIODS = (("2003–2016", 2003, 2016), ("2017–2023", 2017, 2023))
MINUTES_AFTER_ENTRY = 10
WINDOW_FIELDS = ["day", "symbol", "signal_minute", "entry_minute", "entry_price", "adv20_prev",
                 "start_ns", "entry_ns", "end_ns", "bucket", "period"]  # fmt: skip


def minute_ns(day: date, minute_et: int) -> int:
    local = datetime(day.year, day.month, day.day, tzinfo=NEW_YORK) + timedelta(minutes=minute_et)
    return int(local.timestamp()) * 1_000_000_000


def plan(events_path: Path, out_dir: Path, *, per_cell: int = 70, seed: int = 0) -> Path:
    """Write ``windows.csv``: an equal random draw from every liquidity bucket and period."""
    events = pq.read_table(
        events_path,
        columns=["day", "symbol", "signal_minute", "entry_minute", "entry_price", "adv20_prev"],
    ).to_pylist()
    latest = max((e["day"] for e in events), default=None)
    if latest is not None:
        seal.check_range(latest, latest, source="quote sample plan")
    rng = random.Random(seed)
    rows = []
    for bucket, low, high in BUCKETS:
        for period, first, last in PERIODS:
            cell = [e for e in events if low <= (e["adv20_prev"] or 0) < high
                    and first <= e["day"].year <= last]  # fmt: skip
            for event in rng.sample(cell, min(per_cell, len(cell))):
                rows.append({
                    **event,
                    "start_ns": minute_ns(event["day"], event["signal_minute"]),
                    "entry_ns": minute_ns(event["day"], event["entry_minute"]),
                    "end_ns": minute_ns(event["day"], event["entry_minute"] + MINUTES_AFTER_ENTRY),
                    "bucket": bucket, "period": period,
                })  # fmt: skip
    rows.sort(key=lambda r: (r["day"], r["symbol"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "windows.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WINDOW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def read_windows(path: Path) -> list[dict]:
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["day"] = date.fromisoformat(row["day"])
        for key in ("signal_minute", "entry_minute", "start_ns", "entry_ns", "end_ns"):
            row[key] = int(row[key])
        row["entry_price"] = float(row["entry_price"])
        row["adv20_prev"] = float(row["adv20_prev"]) if row["adv20_prev"] else None
    return rows


def sample_file(raw_sample_dir: Path, kind: str, day: date, symbol: str) -> Path:
    return raw_sample_dir / kind / f"{day.isoformat()}_{symbol}.jsonl.gz"


def _read(path: Path) -> list[dict]:
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def measure(
    windows: list[dict],
    raw_sample_dir: Path,
    model_half_spread_bps: Callable[[float, float | None], float],
) -> dict:
    """Quoted spread at each entry against the cost model's fallback (passed in as a function
    of price and 20-day dollar volume), by bucket and period."""
    rows = []
    missing = empty = 0
    for w in windows:
        seal.check_range(w["day"], w["day"], source="quote sample")
        path = sample_file(raw_sample_dir, "quotes", w["day"], w["symbol"])
        if not path.exists():
            missing += 1
            continue
        quotes = [q for q in _read(path) if q.get("bid_price", 0) > 0
                  and q.get("ask_price", 0) >= q.get("bid_price", 0)]  # fmt: skip

        def at(ns, quotes=quotes):
            before = [q for q in quotes if q["sip_timestamp"] <= ns]
            return before[-1] if before else None

        entry, later = at(w["entry_ns"]), at(w["end_ns"])
        if entry is None:
            empty += 1
            continue
        mid = (entry["bid_price"] + entry["ask_price"]) / 2
        half = (entry["ask_price"] - entry["bid_price"]) / 2 / mid * 1e4
        later_half = None
        if later is not None:
            later_mid = (later["bid_price"] + later["ask_price"]) / 2
            later_half = (later["ask_price"] - later["bid_price"]) / 2 / later_mid * 1e4
        rows.append({
            "bucket": w["bucket"], "period": w["period"],
            "quoted_half_bps": half,
            "later_half_bps": later_half,
            "model_half_bps": model_half_spread_bps(w["entry_price"], w["adv20_prev"]),
            # What a market buy pays (the ask) against the price the study assumed (the bar's open).
            "ask_vs_assumed_bps": (entry["ask_price"] / w["entry_price"] - 1) * 1e4,
            "ask_size": entry.get("ask_size"),
        })  # fmt: skip

    def summary(subset: list[dict]) -> dict:
        if not subset:
            return {"events": 0}
        quoted = np.array([r["quoted_half_bps"] for r in subset])
        model = np.array([r["model_half_bps"] for r in subset])
        later = np.array([r["later_half_bps"] for r in subset if r["later_half_bps"] is not None])
        ask = np.array([r["ask_vs_assumed_bps"] for r in subset])
        return {
            "events": len(subset),
            "quoted_half_bps_median": float(np.median(quoted)),
            "quoted_half_bps_mean": float(quoted.mean()),
            "quoted_half_bps_p90": float(np.percentile(quoted, 90)),
            "model_half_bps_median": float(np.median(model)),
            "model_half_bps_mean": float(model.mean()),
            "later_half_bps_median": float(np.median(later)) if len(later) else None,
            "ask_vs_assumed_bps_median": float(np.median(ask)),
            "ask_vs_assumed_bps_mean": float(ask.mean()),
            "share_model_too_low": float((quoted > model).mean()),
        }

    out = {"windows": len(windows), "missing_files": missing, "no_quote_before_entry": empty,
           "all": summary(rows), "by_bucket": {}, "by_period": {}}  # fmt: skip
    for bucket, _, _ in BUCKETS:
        out["by_bucket"][bucket] = summary([r for r in rows if r["bucket"] == bucket])
    for period, _, _ in PERIODS:
        out["by_period"][period] = summary([r for r in rows if r["period"] == period])
    return out


def render(result: dict, name: str) -> str:
    def row(label: str, s: dict) -> str:
        if not s.get("events"):
            return f"| {label} | 0 | | | | | | |"
        later = "" if s["later_half_bps_median"] is None else f"{s['later_half_bps_median']:.0f}"
        return (
            f"| {label} | {s['events']} | {s['quoted_half_bps_median']:.0f} | "
            f"{s['quoted_half_bps_mean']:.0f} | {s['quoted_half_bps_p90']:.0f} | "
            f"{s['model_half_bps_median']:.0f} | {later} | "
            f"{s['ask_vs_assumed_bps_median']:+.0f} | {100 * s['share_model_too_low']:.0f}% |"
        )

    head = (
        "| | Events | Quoted half-spread at entry, median (bps) | Mean | 90th pct | "
        "Model half-spread, median | Quoted, 10 min later | Ask vs assumed entry price, median "
        "(bps) | Model too low |\n|---|---|---|---|---|---|---|---|---|"
    )
    lines = [
        f"# Quote sample: {name}",
        "",
        f"{result['windows']} events planned; {result['missing_files']} not downloaded; "
        f"{result['no_quote_before_entry']} had no quote before the entry.",
        "",
        "Half-spread is half the quoted bid-ask spread, in basis points of the mid price. "
        '"Model too low" is the share of events where the real half-spread was wider than the '
        "cost model's fallback.",
        "",
        head,
        row("All", result["all"]),
    ]
    lines += [row(label, s) for label, s in result["by_bucket"].items()]
    lines += [row(label, s) for label, s in result["by_period"].items()]
    return "\n".join(lines) + "\n"


def passive_orders(windows: list[dict], raw_sample_dir: Path) -> list[dict]:
    """One row per event for a buy limit resting at the bid for the window after the entry.

    ``filled_strict``: a trade printed strictly below the limit (the price traded through).
    ``filled_lenient``: a trade printed at or below it. Prices only; costs are applied later.
    """
    rows = []
    for w in windows:
        seal.check_range(w["day"], w["day"], source="quote sample")
        quote_path = sample_file(raw_sample_dir, "quotes", w["day"], w["symbol"])
        trade_path = sample_file(raw_sample_dir, "trades", w["day"], w["symbol"])
        if not quote_path.exists() or not trade_path.exists():
            continue
        valid = [q for q in _read(quote_path) if q.get("bid_price", 0) > 0
                 and q.get("ask_price", 0) >= q.get("bid_price", 0)
                 and q["sip_timestamp"] <= w["entry_ns"]]  # fmt: skip
        if not valid:
            continue
        bid, ask = valid[-1]["bid_price"], valid[-1]["ask_price"]
        prices = [
            t["price"]
            for t in _read(trade_path)
            if w["entry_ns"] <= t["sip_timestamp"] < w["end_ns"] and t.get("price", 0) > 0
        ]
        rows.append({
            "day": w["day"], "symbol": w["symbol"], "bucket": w["bucket"], "period": w["period"],
            "adv20_prev": w["adv20_prev"], "bid": bid, "ask": ask,
            "trades_in_window": len(prices),
            "filled_strict": any(p < bid for p in prices),
            "filled_lenient": any(p <= bid for p in prices),
        })  # fmt: skip
    return rows
