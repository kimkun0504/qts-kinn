"""Event paths for the reversal-confirmation study (rebound_limit HYPOTHESIS.md, addendum of
2026-11-15 23:50 ET). For every base event (a first one-minute close 10% below the prior close,
the strategy's own definition) it saves the stock's regular-session bars for that day, with
trade counts, and SPY's closes. Development years only. Resumable: one file set per month.

    uv run python research/claude/reversal_events.py --budget 150 --workers 4
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import Settings, load_settings
from kinn.data.store import DataStore
from kinn.engine.intraday.data import load_day
from kinn.features.base import compute
from kinn.validation.targets import DEVELOPMENT_END

START = date(2003, 9, 10)
BAR_COLUMNS = "symbol, minute_et, open, high, low, close, volume, transactions"


def out_dir(settings: Settings) -> Path:
    return settings.data_dir / "research" / "reversal"


def month_job(job: dict) -> str | None:
    from kinn.run import load_strategy

    if time.time() > job["deadline"]:
        return None
    settings = Settings(**{k: Path(v) for k, v in job["settings"].items()})
    store = DataStore(settings)
    strategy = load_strategy("rebound_limit", {})
    events, bars, market = [], [], []
    for day in (date.fromisoformat(d) for d in job["sessions"]):
        data = load_day(store, day, strategy.universe)
        view = data.view
        features = {s: compute(strategy.features, sd) for s, sd in view.symbols.items()}
        found = strategy._events(view, features)
        names = [e[1] for e in found]
        table = store.minute(day, symbols=[*names, "SPY"], columns=BAR_COLUMNS).to_pylist()
        for row in table:
            if not view.open_minute <= row["minute_et"] < view.close_minute:
                continue
            if row["symbol"] == "SPY" and "SPY" not in names:
                market.append({"day": day, "minute": row["minute_et"], "close": row["close"]})
                continue
            if row["symbol"] == "SPY":
                market.append({"day": day, "minute": row["minute_et"], "close": row["close"]})
            bars.append({"day": day, **{("minute" if k == "minute_et" else k): v
                                        for k, v in row.items()}})  # fmt: skip
        for minute, symbol, close, ret15, adv, prev_close, cap, _ in found:
            events.append(
                {
                    "day": day,
                    "symbol": symbol,
                    "permaticker": int(view.symbols[symbol].permaticker),
                    "minute": minute,
                    "event_close": close,
                    "ret15": ret15,
                    "adv20": adv,
                    "prev_close": prev_close,
                    "marketcap": cap,
                    "official_close": data.official_close.get(symbol),
                    "close_minute": view.close_minute,
                }  # fmt: skip
            )
    base = out_dir(settings)
    base.mkdir(parents=True, exist_ok=True)
    for name, rows in (("bars", bars), ("spy", market), ("events", events)):  # events last
        tmp = base / f"{job['month']}.{name}.tmp"
        pq.write_table(pa.Table.from_pylist(rows) if rows else pa.table({}), tmp)
        tmp.replace(base / f"{job['month']}.{name}.parquet")
    return job["month"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=START.isoformat())
    parser.add_argument("--end", default=DEVELOPMENT_END.isoformat())
    parser.add_argument("--budget", type=float, default=150.0)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    if end > DEVELOPMENT_END:
        raise SystemExit("this study reads development years only")
    settings = load_settings()
    store = DataStore(settings)
    months: dict[str, list[str]] = {}
    for row in store.calendar(start, end).to_pylist():
        months.setdefault(row["date"].isoformat()[:7], []).append(row["date"].isoformat())
    base = out_dir(settings)
    pending = [m for m in months if not (base / f"{m}.events.parquet").exists()]
    deadline = time.time() + args.budget
    jobs = [
        {
            "month": m,
            "sessions": months[m],
            "deadline": deadline,
            "settings": {k: str(v) for k, v in vars(settings).items()},
        }  # fmt: skip
        for m in pending
    ]
    done = 0
    with ProcessPoolExecutor(args.workers) as pool:
        for result in pool.map(month_job, jobs):
            done += result is not None
    print(f"months: {len(months)}, done before {len(months) - len(pending)}, "
          f"done now {done}, pending {len(pending) - done}")  # fmt: skip


if __name__ == "__main__":
    main()
