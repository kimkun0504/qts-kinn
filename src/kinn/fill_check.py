"""Check the minute-bar fill rule against real trades.

The simulator fills a resting buy when a minute bar's low is a tick below the limit. This module
lists the orders of finished runs, plans the tick windows to fetch, and compares each order with
the vendor's trades and quotes. The definition and the pass bars live in the strategy's
HYPOTHESIS.md; this module only measures.

Three steps, the middle one done by the owner (it needs the vendor key and writes raw data):

1. ``list_orders`` + ``plan``   rebuild every order of the runs, write ``windows.csv``.
2. (owner)                      ``tools/owner/download_quotes.py`` fetches trades and quotes.
3. ``measure_orders`` + ``study``  compare, and record the result in the run store.
"""

from __future__ import annotations

import csv
import dataclasses
import gzip
import json
import multiprocessing
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import Settings
from kinn.costs import model as cost_model
from kinn.costs.model import CostModel
from kinn.data import quotes, seal
from kinn.data.store import DataStore
from kinn.engine.intraday.data import load_day
from kinn.engine.intraday.simulator import FillConfig, _through, simulate_signal
from kinn.engine.intraday.strategy import day_signals
from kinn.registry import runs as registry
from kinn.risk.sizing import RiskConfig

CAP_GROUPS = (("under $300M", 0.0, 3e8), ("$300M–$2B", 3e8, 2e9), ("over $2B", 2e9, float("inf")))
UNKNOWN_CAP = "unknown"
UNFILLED_PER_CELL = {"touched": 100, "near": 50, "far": 30}
NEAR = 0.01  # "near": the low came within this fraction of the limit
DELAYS = (0, 5, 30)  # seconds after the event bar before the order is in the book
MAIN_DELAY = 5
# Trade conditions that do not update the consolidated high and low. Used only if the vendor's
# own table was not downloaded with the data (conditions.json).
FALLBACK_INELIGIBLE = frozenset({2, 7, 10, 12, 13, 15, 16, 20, 21, 22, 29, 32, 33, 37, 38, 52, 53})
ODD_LOT = 37
ORDER_FIELDS = [
    "run", "day", "symbol", "permaticker", "signal_minute", "live_from", "last_entry",
    "limit_price", "order_quantity", "bar_quantity", "bar_fill_minute", "min_low", "kind",
    "close", "prev_close", "adv20_prev", "marketcap_prev", "tag",
]  # fmt: skip
WINDOW_FIELDS = [*quotes.WINDOW_FIELDS, "limit_price", "quantity", "kind", "run"]


def cap_group(marketcap: float | None) -> str:
    if marketcap is None or marketcap != marketcap:
        return UNKNOWN_CAP
    return next(name for name, low, high in CAP_GROUPS if low <= marketcap < high)


# -- 1. the orders of a run ----------------------------------------------------------------


def _list_month(job: dict) -> str | None:
    """Every order one run placed or would have placed in one month, with the bar rule's verdict.
    Runs in a worker process."""
    from kinn.run import load_strategy  # here, not at import: kinn.run imports the reporting stack

    if time.time() > job["deadline"]:
        return None
    settings = Settings(**{k: Path(v) for k, v in job["settings"].items()})
    store = DataStore(settings, build_id=job["build_id"])
    costs = cost_model.load(job["cost_calibration"])
    cfg = job["config"]
    strategy = load_strategy(job["strategy"], cfg.get("params", {}))
    risk = RiskConfig(**cfg.get("risk", {}))
    fills = FillConfig(**cfg.get("fills", {}))
    rows = []
    for day in (date.fromisoformat(d) for d in job["sessions"]):
        data = load_day(store, day, strategy.universe)
        view = data.view
        for signal in day_signals(strategy, view):
            if signal.limit_price is None:
                raise ValueError("the fill check is for limit orders")
            sd = view.symbols[signal.symbol]
            quantity = risk.shares(signal.weight, signal.limit_price)
            entry: list = []
            if quantity > 0:
                entry, _, _, _ = simulate_signal(
                    sd, signal, quantity, config=fills, costs=costs,
                    open_minute=view.open_minute, close_minute=view.close_minute,
                    official_close=data.official_close.get(sd.symbol),
                )  # fmt: skip
            live_from = max(signal.minute + 1, view.open_minute)
            last_entry = view.close_minute - fills.no_entry_before_close - 1
            if signal.expire_minute is not None:
                last_entry = min(last_entry, signal.expire_minute)
            live = (sd.minute >= live_from) & (sd.minute <= last_entry)
            min_low = float(sd.low[live].min()) if live.any() else None
            if entry:
                kind = "filled"
            elif min_low is not None and min_low <= signal.limit_price + 1e-9:
                kind = "touched"
            elif min_low is not None and min_low <= signal.limit_price * (1 + NEAR):
                kind = "near"
            else:
                kind = "far"
            rows.append({
                "run": job["run_id"], "day": day, "symbol": sd.symbol,
                "permaticker": sd.permaticker, "signal_minute": signal.minute,
                "live_from": live_from, "last_entry": last_entry,
                "limit_price": signal.limit_price, "order_quantity": quantity,
                "bar_quantity": sum(f.quantity for f in entry),
                "bar_fill_minute": entry[0].minute if entry else None, "min_low": min_low,
                "kind": kind, "close": data.official_close.get(sd.symbol),
                "prev_close": sd.prior.get("prev_close"), "adv20_prev": sd.prior.get("adv20_prev"),
                "marketcap_prev": sd.prior.get("marketcap_prev"), "tag": signal.tag,
            })  # fmt: skip
    out = Path(job["parts"])
    tmp = out / f"{job['month']}.parquet.tmp"
    pq.write_table(pa.Table.from_pylist(rows, schema=ORDER_SCHEMA), tmp)
    os.replace(tmp, out / f"{job['month']}.parquet")
    return job["month"]


ORDER_SCHEMA = pa.schema([
    ("run", pa.string()), ("day", pa.date32()), ("symbol", pa.string()),
    ("permaticker", pa.int64()), ("signal_minute", pa.int64()), ("live_from", pa.int64()),
    ("last_entry", pa.int64()), ("limit_price", pa.float64()), ("order_quantity", pa.int64()),
    ("bar_quantity", pa.int64()), ("bar_fill_minute", pa.int64()), ("min_low", pa.float64()),
    ("kind", pa.string()), ("close", pa.float64()), ("prev_close", pa.float64()),
    ("adv20_prev", pa.float64()), ("marketcap_prev", pa.float64()), ("tag", pa.string()),
])  # fmt: skip


def _pool(function, jobs: list[dict], workers: int) -> None:
    if workers <= 1:
        for job in jobs:
            function(job)
        return
    with ProcessPoolExecutor(
        max_workers=workers, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        list(pool.map(function, jobs))


def list_orders(
    settings: Settings, run_id: str, work_dir: Path, *, budget_seconds: float = float("inf"),
    workers: int = 1,
) -> bool:  # fmt: skip
    """Rebuild a finished run's orders month by month into ``work_dir``. Resumable. Returns True
    when every month is listed. This is a listing, not a run: nothing goes to the run store."""
    manifest = json.loads((settings.runs_dir / run_id / "manifest.json").read_text())
    if manifest.get("kind", "backtest") != "backtest" or manifest["status"] != "complete":
        raise ValueError(f"{run_id} is not a finished backtest")
    months: dict[str, list[str]] = {}
    for day in manifest["sessions"]:
        months.setdefault(day[:7], []).append(day)
    parts = work_dir / run_id
    parts.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + budget_seconds
    jobs = [
        {
            "settings": {k: str(v) for k, v in dataclasses.asdict(settings).items()},
            "build_id": manifest["data_build_id"],
            "strategy": manifest["strategy"],
            "config": manifest["resolved_config"],
            "run_id": run_id,
            "cost_calibration": manifest["cost_calibration"],
            "parts": str(parts),
            "month": month,
            "sessions": sessions,
            "deadline": deadline,
        }  # fmt: skip
        for month, sessions in months.items()
        if not (parts / f"{month}.parquet").exists()
    ]
    _pool(_list_month, jobs, workers)
    return all((parts / f"{m}.parquet").exists() for m in months)


def read_orders(work_dir: Path, run_id: str) -> list[dict]:
    files = sorted((work_dir / run_id).glob("*.parquet"))
    return [row for f in files for row in pq.read_table(f).to_pylist()]


def order_key(row: dict) -> tuple:
    """One order: a symbol on a day, and for a ladder the rung (its tag)."""
    return (row["day"], row["symbol"], row.get("tag") or "")


class OrdersMismatch(RuntimeError):
    """The rebuilt orders are not the run's orders."""


def check_against_run(settings: Settings, run_id: str, orders: list[dict]) -> dict:
    """Mark the orders the run traded, and insist the listing reproduces the run: same signal
    count, and every trade is a bar-filled order with the same quantity, minute and price."""
    run_dir = settings.runs_dir / run_id
    metrics = json.loads((run_dir / "metrics.json").read_text())
    trades = pq.read_table(run_dir / "trades.parquet").to_pylist()
    if len(orders) != metrics["counts"]["signals"]:
        raise OrdersMismatch(
            f"{run_id}: {len(orders)} orders listed, the run saw {metrics['counts']['signals']}"
        )
    by_key = {order_key(o): o for o in orders}
    if len(by_key) != len(orders):
        raise OrdersMismatch(f"{run_id}: two orders with one tag for one symbol on one day")
    for order in orders:
        order.update(traded=False, sim_net=None, sim_net_2x=None, sim_notional=None)
    for trade in trades:
        order = by_key.get(order_key(trade))
        same = order is not None and (
            order["bar_quantity"] == trade["quantity"]
            and order["bar_fill_minute"] == trade["entry_minute"]
            and abs(order["limit_price"] - trade["entry_price"]) < 1e-9
        )
        if not same:
            raise OrdersMismatch(f"{run_id}: trade {trade['day']} {trade['symbol']} not rebuilt")
        order["traded"] = True
        order["close"] = trade["exit_price"]
        order["sim_net"], order["sim_net_2x"] = trade["net"], trade["net_2x"]
        order["sim_notional"] = trade["notional"]
    return {
        "run": run_id, "orders": len(orders), "traded": len(trades),
        "bar_filled": sum(o["kind"] == "filled" for o in orders),
        "touched": sum(o["kind"] == "touched" for o in orders),
        "near": sum(o["kind"] == "near" for o in orders),
        "far": sum(o["kind"] == "far" for o in orders),
    }  # fmt: skip


# -- 2. the plan ---------------------------------------------------------------------------


def plan(
    settings: Settings, name: str, run_ids: list[str], work_dir: Path, *, seed: int = 0,
    per_cell: dict[str, int] | None = None, labels: dict[str, str] | None = None,
    also_reads: list[str] | None = None,
) -> Path:  # fmt: skip
    """Write the plan folder: ``orders.parquet`` (every traded order and the unfilled sample),
    ``windows.csv`` for the owner's download, and ``plan.json``.

    A ladder's rungs share one window. ``also_reads`` names earlier plans whose downloaded
    files are read where they are: a window already on disk there is not fetched again."""
    per_cell = per_cell or UNFILLED_PER_CELL
    chosen: list[dict] = []
    summary = {
        "name": name,
        "seed": seed,
        "per_cell": per_cell,
        "labels": labels or {r: r for r in run_ids},
        "also_reads": list(also_reads or []),
        "runs": [],
        "sample": {},
    }
    for run_id in run_ids:
        orders = read_orders(work_dir, run_id)
        summary["runs"].append(check_against_run(settings, run_id, orders))
        for order in orders:
            order["cap_group"] = cap_group(order["marketcap_prev"])
        chosen += [o for o in orders if o["traded"]]
        for group, _, _ in CAP_GROUPS:
            for kind, count in per_cell.items():
                cell = sorted(
                    (o for o in orders if o["kind"] == kind and o["cap_group"] == group
                     and o["order_quantity"] > 0),
                    key=order_key,
                )  # fmt: skip
                rng = random.Random(f"{seed}:{run_id}:{group}:{kind}")
                picked = rng.sample(cell, min(count, len(cell)))
                summary["sample"][f"{run_id}|{group}|{kind}"] = [len(picked), len(cell)]
                chosen += picked
    chosen.sort(key=order_key)
    latest = max(o["day"] for o in chosen)
    seal.check_range(latest, latest, source="fill check plan")
    out = settings.data_dir / "quotes_sample" / name
    out.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(chosen), out / "orders.parquet")
    earlier = [settings.raw_dir / "massive" / "quotes_sample" / n for n in summary["also_reads"]]
    seen: set[tuple] = set()
    fetch = on_disk = 0
    with (out / "windows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=WINDOW_FIELDS)
        writer.writeheader()
        for o in chosen:
            if (o["day"], o["symbol"]) in seen:
                continue
            seen.add((o["day"], o["symbol"]))
            if any(
                all(quotes.sample_file(d, k, o["day"], o["symbol"]).exists()
                    for k in ("trades", "quotes"))
                for d in earlier
            ):  # fmt: skip
                on_disk += 1
                continue
            fetch += 1
            start, live, end = window_ns(o)
            writer.writerow({
                "day": o["day"].isoformat(), "symbol": o["symbol"],
                "signal_minute": o["signal_minute"], "entry_minute": o["live_from"],
                "entry_price": o["limit_price"], "adv20_prev": o["adv20_prev"],
                "start_ns": start, "entry_ns": live, "end_ns": end, "bucket": o["cap_group"],
                "period": o["run"], "limit_price": o["limit_price"],
                "quantity": o["order_quantity"],
                "kind": "traded" if o["traded"] else o["kind"], "run": o["run"],
            })  # fmt: skip
    summary.update(orders=len(chosen), windows=fetch, windows_already_downloaded=on_disk)
    registry.write_json(out / "plan.json", summary)
    return out


def window_ns(order: dict) -> tuple[int, int, int]:
    """(start of the event bar, the order goes live, the order expires), in nanoseconds."""
    return (
        quotes.minute_ns(order["day"], order["signal_minute"]),
        quotes.minute_ns(order["day"], order["live_from"]),
        quotes.minute_ns(order["day"], order["last_entry"] + 1),
    )


# -- 3. the comparison with real trades ----------------------------------------------------


def raw_dirs(settings: Settings, name: str) -> list[Path]:
    """Where a plan's ticks are: its own raw folder, then those of the plans it also reads."""
    base = settings.raw_dir / "massive" / "quotes_sample"
    plan_file = settings.data_dir / "quotes_sample" / name / "plan.json"
    extra = json.loads(plan_file.read_text()).get("also_reads", []) if plan_file.exists() else []
    return [base / name, *(base / n for n in extra)]


def ineligible_conditions(raw_dir: Path | list[Path]) -> tuple[frozenset[int], str]:
    """Condition codes of trades that do not update the consolidated high and low: from the
    vendor's table if it was downloaded, otherwise the fallback list."""
    folders = raw_dir if isinstance(raw_dir, list) else [raw_dir]
    path = next((d / "conditions.json" for d in folders if (d / "conditions.json").exists()), None)
    if path is None:
        return FALLBACK_INELIGIBLE, "fallback list"
    codes = set()
    for row in json.loads(path.read_text()):
        if "trade" not in (row.get("data_types") or ["trade"]):
            continue
        rules = (row.get("update_rules") or {}).get("consolidated") or {}
        if rules.get("updates_high_low") is False:
            codes.add(int(row["id"]))
    return frozenset(codes), "vendor table"


def _read(path: Path) -> list[dict]:
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def order_ticks(
    order: dict, raw_dir: Path | list[Path], ineligible: frozenset[int], tick: float
) -> dict:
    """What real trades and quotes say about one order. Prices only; no costs."""
    seal.check_range(order["day"], order["day"], source="fill check")
    out = {"day": order["day"], "symbol": order["symbol"], "tag": order.get("tag") or "",
           "has_file": False, "prints": 0}  # fmt: skip
    folders = raw_dir if isinstance(raw_dir, list) else [raw_dir]
    raw_dir = next(
        (d for d in folders
         if quotes.sample_file(d, "trades", order["day"], order["symbol"]).exists()),
        None,
    )  # fmt: skip
    if raw_dir is None:
        return out
    trade_path = quotes.sample_file(raw_dir, "trades", order["day"], order["symbol"])
    out["has_file"] = True
    _, live, end = window_ns(order)
    limit = order["limit_price"]
    through = limit - _through(limit, FillConfig(), tick) + 1e-9
    strict_odd = set(ineligible) - {ODD_LOT}
    trades = [
        t for t in _read(trade_path)
        if live <= t["sip_timestamp"] < end and t.get("price", 0) > 0
        and not t.get("correction")
    ]  # fmt: skip
    out["prints"] = len(trades)
    for delay in DELAYS:
        start = live + delay * 1_000_000_000
        volume = volume_odd = count = at_limit = 0
        first = None
        for t in trades:
            if t["sip_timestamp"] < start:
                continue
            codes = set(t.get("conditions") or ())
            if t["price"] <= through:
                if not codes & strict_odd:
                    volume_odd += int(t["size"])
                if not codes & ineligible:
                    volume += int(t["size"])
                    count += 1
                    if first is None:
                        first = (t["sip_timestamp"] - live) / 1e9
            elif t["price"] <= limit + 1e-9 and not codes & ineligible:
                at_limit += int(t["size"])
        out[f"through_prints_{delay}"] = count
        out[f"through_volume_{delay}"] = volume
        out[f"through_volume_odd_{delay}"] = volume_odd
        out[f"at_limit_volume_{delay}"] = at_limit
        out[f"first_through_seconds_{delay}"] = first
    quote_path = quotes.sample_file(raw_dir, "quotes", order["day"], order["symbol"])
    out["has_quotes"] = False
    if quote_path.exists():
        start = live + MAIN_DELAY * 1_000_000_000
        valid = [q for q in _read(quote_path) if q.get("bid_price", 0) > 0
                 and q.get("ask_price", 0) >= q.get("bid_price", 0)
                 and q["sip_timestamp"] < end]  # fmt: skip
        before = [q for q in valid if q["sip_timestamp"] <= start]
        during = ([before[-1]] if before else []) + [q for q in valid if q["sip_timestamp"] > start]
        if during:
            out["has_quotes"] = True
            out["bid_at_start"], out["ask_at_start"] = (
                during[0]["bid_price"],
                during[0]["ask_price"],
            )
            out["bid_below_limit"] = min(q["bid_price"] for q in during) < limit - 1e-9
            out["ask_reached_limit"] = min(q["ask_price"] for q in during) <= limit + 1e-9
    return out


def _measure_part(job: dict) -> str | None:
    if time.time() > job["deadline"]:
        return None
    folders = [Path(d) for d in job["raw_dirs"]]
    ineligible = frozenset(job["ineligible"])
    rows = [order_ticks(o, folders, ineligible, job["tick"]) for o in job["orders"]]
    out = Path(job["parts"])
    tmp = out / f"{job['key']}.parquet.tmp"
    pq.write_table(pa.Table.from_pylist(rows), tmp)
    os.replace(tmp, out / f"{job['key']}.parquet")
    return job["key"]


def measure_orders(
    settings: Settings, name: str, work_dir: Path, *, costs: CostModel,
    budget_seconds: float = float("inf"), workers: int = 1,
) -> bool:  # fmt: skip
    """Read the downloaded ticks for every planned order, a year at a time into ``work_dir``.
    Resumable. Returns True when every year is measured."""
    orders = pq.read_table(settings.data_dir / "quotes_sample" / name / "orders.parquet")
    folders = raw_dirs(settings, name)
    ineligible, _ = ineligible_conditions(folders)
    parts = work_dir / f"{name}-ticks"
    parts.mkdir(parents=True, exist_ok=True)
    years: dict[str, list[dict]] = {}
    columns = ["day", "symbol", "signal_minute", "live_from", "last_entry", "limit_price"]
    if "tag" in orders.column_names:
        columns.append("tag")
    for order in orders.select(columns).to_pylist():
        years.setdefault(str(order["day"].year), []).append(order)
    deadline = time.time() + budget_seconds
    jobs = [
        {"key": year, "orders": rows, "raw_dirs": [str(d) for d in folders],
         "ineligible": sorted(ineligible),
         "tick": costs.tick, "parts": str(parts), "deadline": deadline}
        for year, rows in sorted(years.items()) if not (parts / f"{year}.parquet").exists()
    ]  # fmt: skip
    _pool(_measure_part, jobs, workers)
    return all((parts / f"{y}.parquet").exists() for y in years)


def trade_result(costs: CostModel, limit: float, close: float, quantity: int) -> dict | None:
    """A round trip bought passively at the limit and sold in the closing auction."""
    if quantity <= 0:
        return None
    value_in, value_out = quantity * limit, quantity * close
    c_in, f_in = costs.order_fees(
        side="buy", value=value_in, marketable=0, passive=quantity, auction=0
    )
    c_out, f_out = costs.order_fees(
        side="sell", value=value_out, marketable=0, passive=0, auction=quantity
    )
    slip = costs.auction_slippage(price=close, shares=quantity)
    net = value_out - value_in - c_in - f_in - c_out - f_out - slip
    return {"notional": value_in, "net": net, "net_2x": net - slip}


def _share(flags: list[bool]) -> float | None:
    return float(np.mean(flags)) if flags else None


def summarize_traded(rows: list[dict], costs: CostModel) -> dict:
    """The traded orders of one group: how many real trades confirm, and the result when each
    order is cut to the size real trades support."""
    covered = [r for r in rows if r["has_file"] and r["prints"] > 0]
    out = {
        "orders": len(rows),
        "no_file": sum(not r["has_file"] for r in rows),
        "file_without_prints": sum(r["has_file"] and r["prints"] == 0 for r in rows),
        "covered": len(covered),
        "coverage": len(covered) / len(rows) if rows else None,
    }
    if not covered:
        return out
    main = MAIN_DELAY
    multiple = [r[f"through_volume_{main}"] / r["bar_quantity"] for r in covered]
    with_quotes = [r for r in covered if r.get("has_quotes")]
    out.update({
        "confirmed": _share([r["through_prints_0"] > 0 for r in covered]),
        "confirmed_with_odd_lots": _share([r["through_volume_odd_0"] > 0 for r in covered]),
        f"confirmed_after_{main}s": _share([r[f"through_prints_{main}"] > 0 for r in covered]),
        "in_full_size": _share([m >= 1 for m in multiple]),
        "through_volume_multiple_median": float(np.median(multiple)),
        "through_volume_multiple_p10": float(np.percentile(multiple, 10)),
        "through_volume_multiple_p25": float(np.percentile(multiple, 25)),
        "with_quotes": len(with_quotes),
        "bid_fell_below_limit": _share([bool(r["bid_below_limit"]) for r in with_quotes]),
        "ask_reached_limit": _share([bool(r["ask_reached_limit"]) for r in with_quotes]),
        "confirmed_or_bid_below": _share(
            [r["through_prints_0"] > 0 or bool(r.get("bid_below_limit")) for r in covered]
        ),
        "simulated": _result([(r["sim_notional"], r["sim_net"], r["sim_net_2x"]) for r in covered]),
    })  # fmt: skip
    for delay in DELAYS:
        cut = []
        for r in covered:
            quantity = min(r["bar_quantity"], r[f"through_volume_{delay}"])
            result = trade_result(costs, r["limit_price"], r["close"], quantity)
            if result:
                cut.append((result["notional"], result["net"], result["net_2x"]))
        out[f"tick_rule_{delay}s"] = _result(cut)
        simulated = out["simulated"]["total_net_2x"]
        out[f"tick_rule_{delay}s"]["share_of_simulated_net_2x"] = (
            out[f"tick_rule_{delay}s"]["total_net_2x"] / simulated if simulated else None
        )
    return out


def _result(rows: list[tuple[float, float, float]]) -> dict:
    """(notional, net, net at 2x) per trade -> the standard per-trade and total figures."""
    if not rows:
        return {"trades": 0, "net_per_trade_1x": None, "net_per_trade_2x": None,
                "total_net_1x": 0.0, "total_net_2x": 0.0, "mean_notional": None}  # fmt: skip
    notional, net, net2 = (np.array(c, dtype=float) for c in zip(*rows, strict=True))
    return {
        "trades": len(rows),
        "net_per_trade_1x": float((net / notional).mean()),
        "net_per_trade_2x": float((net2 / notional).mean()),
        "total_net_1x": float(net.sum()),
        "total_net_2x": float(net2.sum()),
        "mean_notional": float(notional.mean()),
    }


def summarize_unfilled(rows: list[dict], costs: CostModel) -> dict:
    """Sampled orders the bar rule left unfilled: would real trades have filled them?"""
    covered = [r for r in rows if r["has_file"]]
    out = {"orders": len(rows), "covered": len(covered)}
    if not covered:
        return out
    main = MAIN_DELAY
    through = [r[f"through_prints_{main}"] > 0 for r in covered]
    at_limit = [r[f"at_limit_volume_{main}"] > 0 and not t
                for r, t in zip(covered, through, strict=True)]  # fmt: skip
    in_size = [r[f"at_limit_volume_{main}"] >= r["order_quantity"] and not t
               for r, t in zip(covered, through, strict=True)]  # fmt: skip
    out.update({
        "rule_missed_a_fill": _share(through),
        "printed_at_the_limit_only": _share(at_limit),
        "at_the_limit_in_full_size": _share(in_size),
    })  # fmt: skip
    for label, flags in (("if_missed_fills_traded", through), ("if_touches_filled", at_limit)):
        hypothetical = []
        for r, flag in zip(covered, flags, strict=True):
            if flag and r["close"] is not None:
                result = trade_result(costs, r["limit_price"], r["close"], r["order_quantity"])
                if result:
                    hypothetical.append((result["notional"], result["net"], result["net_2x"]))
        out[label] = _result(hypothetical)
    return out


def assemble(settings: Settings, name: str, work_dir: Path) -> list[dict]:
    """The planned orders joined with what the ticks said."""
    orders = pq.read_table(settings.data_dir / "quotes_sample" / name / "orders.parquet")
    ticks = {}
    for path in sorted((work_dir / f"{name}-ticks").glob("*.parquet")):
        for row in pq.read_table(path).to_pylist():
            ticks[order_key(row)] = row
    rows = []
    for order in orders.to_pylist():
        rows.append({**order, **ticks[order_key(order)]})
    return rows


def evaluate(rows: list[dict], costs: CostModel, run_labels: dict[str, str]) -> dict:
    """Every table of the report, and the verdict against the pass bars."""
    traded = [r for r in rows if r["traded"]]
    unfilled = [r for r in rows if not r["traded"]]
    groups = [g[0] for g in CAP_GROUPS] + [UNKNOWN_CAP]
    result: dict = {"schema": "fill-check-1", "main_delay_seconds": MAIN_DELAY, "periods": {}}
    for run, label in run_labels.items():
        mine = [r for r in traded if r["run"] == run]
        block = {
            "run": run,
            "all": summarize_traded(mine, costs),
            "by_cap": {g: summarize_traded([r for r in mine if r["cap_group"] == g], costs)
                       for g in groups},
            "by_rung": {t: summarize_traded([r for r in mine if (r.get("tag") or "") == t], costs)
                        for t in sorted({r.get("tag") or "" for r in mine}) if t},
            "before_2007": summarize_traded([r for r in mine if r["day"].year < 2007], costs),
            "from_2007": summarize_traded([r for r in mine if r["day"].year >= 2007], costs),
            "unfilled": {},
        }  # fmt: skip
        for kind in UNFILLED_PER_CELL:
            sample = [r for r in unfilled if r["run"] == run and r["kind"] == kind]
            block["unfilled"][kind] = {
                "all": summarize_unfilled(sample, costs),
                "by_cap": {g: summarize_unfilled([r for r in sample if r["cap_group"] == g], costs)
                           for g in groups[:-1]},
            }  # fmt: skip
        result["periods"][label] = block
    result["all_traded"] = summarize_traded(traded, costs)
    return result


def verdict(result: dict, validation_label: str) -> dict:
    """The three pass bars of the hypothesis (coverage, confirmed, tick-rule result)."""
    main = f"tick_rule_{MAIN_DELAY}s"
    periods = result["periods"]
    coverage = result["all_traded"].get("coverage") or 0.0
    confirmed = {k: p["all"].get("confirmed") for k, p in periods.items()}
    kept = {k: p["all"].get(main, {}).get("share_of_simulated_net_2x") for k, p in periods.items()}
    net = periods[validation_label]["all"].get(main, {}).get("net_per_trade_2x")
    bars = {
        "coverage_at_least_95pct": coverage >= 0.95,
        "confirmed_at_least_97pct_each_period": all((v or 0) >= 0.97 for v in confirmed.values()),
        "validation_net_2x_at_least_1pct": net is not None and net >= 0.01,
        "tick_rule_keeps_80pct_of_net_each_period": all((v or 0) >= 0.80 for v in kept.values()),
    }
    return {"bars": bars, "passed": all(bars.values()), "coverage": coverage,
            "confirmed": confirmed, "validation_net_per_trade_2x": net,
            "share_of_simulated_net_2x": kept}  # fmt: skip


def study(
    settings: Settings, name: str, work_dir: Path, *, strategy: str, run_labels: dict[str, str],
    validation_label: str, meta: dict, repo: Path, scratch: bool = False,
    agent: str | None = None,
) -> Path:  # fmt: skip
    """Record the fill check in the run store (one trial for the family)."""
    costs = cost_model.load(meta["cost_calibration"])
    git = registry.git_state(repo)
    registry.check_clean(git, scratch=scratch)
    raw_dir = raw_dirs(settings, name)
    rows = assemble(settings, name, work_dir)
    result = evaluate(rows, costs, run_labels)
    result["verdict"] = verdict(result, validation_label)
    result["conditions_source"] = ineligible_conditions(raw_dir)[1]
    result["plan"] = name
    agent = agent or os.environ.get("KINN_AGENT", "human")
    short = registry.config_hash({"meta": meta, "plan": name, "commit": git["commit"]})
    run_id = registry.new_run_id(agent, strategy, short)
    run_dir = settings.runs_dir / run_id
    run_dir.mkdir(parents=True)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    days = sorted(r["day"] for r in rows)
    manifest = {
        "schema": registry.MANIFEST_SCHEMA, "run_id": run_id, "kind": "fill_check",
        "strategy": strategy, "family": meta.get("family", strategy),
        "prior_trials": int(meta.get("prior_trials", 0)), "config": f"fill_check:{name}",
        "config_hash": short,
        "resolved_config": {"plan": name, "source_runs": run_labels,
                            "main_delay_seconds": MAIN_DELAY},
        "cost_calibration": meta["cost_calibration"], "git": git, "scratch": scratch,
        "agent": agent, "data_build_id": "tick-sample:" + name,
        "period": {"start": str(days[0]), "end": str(days[-1])},
        "started_at": now, "finished_at": now, "status": "complete",
    }  # fmt: skip
    registry.write_json(run_dir / "manifest.json", manifest)
    registry.write_json(run_dir / "fill_check.json", result)
    pq.write_table(pa.Table.from_pylist(rows), run_dir / "orders.parquet")
    (run_dir / "fill_check.md").write_text(render(result, run_id))
    return run_dir


# -- the report ----------------------------------------------------------------------------


def _pct(value: float | None, digits: int = 0) -> str:
    return "–" if value is None else f"{100 * value:.{digits}f}%"


def _ret(value: float | None) -> str:
    return "–" if value is None else f"{100 * value:+.2f}%".replace("-", "−")


def _usd(value: float | None) -> str:
    if value is None:
        return "–"
    return f"+${value:,.0f}" if value >= 0 else f"−${abs(value):,.0f}"


def render(result: dict, run_id: str) -> str:
    main = f"tick_rule_{result['main_delay_seconds']}s"
    v = result["verdict"]
    lines = [
        "# Fill check: minute-bar fills against real trades",
        "",
        f"`{run_id}`, plan `{result['plan']}`. Trade conditions from the "
        f"{result['conditions_source']}.",
        "",
        f"**{'PASSED' if v['passed'] else 'FAILED'}.** "
        + "; ".join(
            f"{k.replace('_', ' ')}: {'yes' if ok else 'NO'}" for k, ok in v["bars"].items()
        ),
        "",
    ]
    head = (
        "| | Traded orders | With ticks | Confirmed | After 5 s | In full size | Through-volume ÷ "
        "order, median | Bid fell below limit | Simulated net/trade 2× | Tick-rule trades | "
        "Tick-rule net/trade 2× | Simulated total 2× | Tick-rule total 2× | Kept |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    )

    def row(label: str, s: dict) -> str:
        if not s.get("covered"):
            return f"| {label} | {s['orders']} | 0 | | | | | | | | | | | |"
        sim, cut = s["simulated"], s[main]
        return (
            f"| {label} | {s['orders']} | {s['covered']} | {_pct(s['confirmed'], 1)} | "
            f"{_pct(s[f'confirmed_after_{MAIN_DELAY}s'], 1)} | {_pct(s['in_full_size'], 1)} | "
            f"{s['through_volume_multiple_median']:.0f}× | {_pct(s['bid_fell_below_limit'])} | "
            f"{_ret(sim['net_per_trade_2x'])} | {cut['trades']} | "
            f"{_ret(cut['net_per_trade_2x'])} | "
            f"{_usd(sim['total_net_2x'])} | {_usd(cut['total_net_2x'])} | "
            f"{_pct(cut['share_of_simulated_net_2x'])} |"
        )

    for label, block in result["periods"].items():
        lines += [f"## {label}", "", head, row("All", block["all"])]
        lines += [row(g, s) for g, s in block["by_cap"].items()]
        lines += [row(f"rung {t}", s) for t, s in block.get("by_rung", {}).items()]
        lines += [row("2003–2006", block["before_2007"]), row("2007 on", block["from_2007"]), ""]
        a = block["all"]
        if a.get("covered"):
            lines += [
                "Latency: tick-rule net per trade at 2× and total, with the order in the book "
                + ", ".join(
                    f"{d} s after the bar: {_ret(a[f'tick_rule_{d}s']['net_per_trade_2x'])}, "
                    f"{_usd(a[f'tick_rule_{d}s']['total_net_2x'])}"
                    for d in DELAYS
                )
                + ".",
                "",
            ]
        lines += [
            "Orders the bar rule left unfilled (sample):",
            "",
            "| | Sampled | With ticks | Real trades would have filled | Printed at the limit only "
            "| ... in full size | Net/trade 2× if the missed fills traded | Net/trade 2× if "
            "touches filled |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for kind, part in block["unfilled"].items():
            for name, s in [("all", part["all"]), *part["by_cap"].items()]:
                if not s.get("covered"):
                    lines.append(f"| {kind}, {name} | {s['orders']} | 0 | | | | | |")
                    continue
                missed, touch = s["if_missed_fills_traded"], s["if_touches_filled"]
                lines.append(
                    f"| {kind}, {name} | {s['orders']} | {s['covered']} | "
                    f"{_pct(s['rule_missed_a_fill'])} | {_pct(s['printed_at_the_limit_only'])} | "
                    f"{_pct(s['at_the_limit_in_full_size'])} | "
                    f"{_ret(missed['net_per_trade_2x'])} ({missed['trades']}) | "
                    f"{_ret(touch['net_per_trade_2x'])} ({touch['trades']}) |"
                )
        lines.append("")
    return "\n".join(lines)
