"""Prepare all registered control windows, without inspecting quote prices or returns.

This is acquisition metadata, not a backtest or a source of performance results.
The owner alone runs tools/owner/download_quotes.py on the resulting windows.csv.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from datetime import date
from pathlib import Path

import pyarrow.parquet as pq

from kinn.core.settings import load_settings
from kinn.data import quotes, seal

VERSION = "bid-quote-plan-1"
EXPECTED_PERIOD = {"start": "2003-09-10", "end": "2016-12-30"}
FIELDS = [*quotes.WINDOW_FIELDS, "permaticker", "early_target_ns", "late_target_ns", "decision_ns"]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(settings, source_run, output=None):
    if not source_run or any(x in source_run for x in ("/", "\\", "..")):
        raise ValueError("source run must be one run id")
    source = settings.runs_dir / source_run
    manifest = json.loads((source / "manifest.json").read_text())
    if not (
        manifest["run_id"] == source_run
        and manifest["strategy"] == "bid_replenishment_reversal"
        and manifest["kind"] == "event_study"
        and manifest["config"] == "development_control"
        and manifest["status"] == "complete"
        and not manifest["scratch"]
        and not manifest["git"]["dirty"]
        and manifest["resolved_config"]["params"] == {"use_quotes": False}
        and manifest["period"] == EXPECTED_PERIOD
    ):
        raise ValueError("plan requires the one finished, clean registered development control")
    seal.check_range(
        date.fromisoformat(EXPECTED_PERIOD["start"]),
        date.fromisoformat(EXPECTED_PERIOD["end"]),
        source=VERSION,
    )
    events = source / "events.parquet"
    days = pq.read_table(events, columns=["day"])["day"].to_pylist()
    if not all(date(2003, 9, 10) <= d <= date(2016, 12, 30) for d in days):
        raise ValueError("control has a date outside its registered development period")
    # Deliberately omit all forward returns and post-signal entry prices from this read.
    columns = ["day", "symbol", "permaticker", "signal_minute", "prev_close", "adv20_prev"]
    candidates = pq.read_table(events, columns=columns).to_pylist()
    rows, seen = [], set()
    for event in candidates:
        day, symbol = event["day"], event["symbol"]
        if not symbol or any(x in symbol for x in ("/", "\\", "\x00")):
            raise ValueError("unsafe or missing symbol")
        key = day, symbol
        if key in seen:
            raise ValueError("control must have only its first event per symbol/date")
        seen.add(key)
        end = quotes.minute_ns(day, int(event["signal_minute"]) + 1)
        rows.append(
            {
                "day": day.isoformat(),
                "symbol": symbol,
                "permaticker": event["permaticker"],
                "signal_minute": event["signal_minute"],
                "entry_minute": event["signal_minute"] + 1,
                # Downloader-compatible metadata only. This is not an entry price assumption.
                "entry_price": event["prev_close"],
                "adv20_prev": event["adv20_prev"],
                "start_ns": end - 10_000_000_000,
                "entry_ns": end,
                "end_ns": end + 2_000_000_000,
                "early_target_ns": end - 5_000_000_000,
                "late_target_ns": end - 1,
                "decision_ns": end,
                "bucket": "registered price candidates",
                "period": "2003–2016",
            }
        )
    rows.sort(key=lambda r: (r["day"], r["symbol"]))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    payload = stream.getvalue().encode()
    out = (
        Path(output)
        if output
        else (
            settings.data_dir
            / "quotes_sample"
            / f"gpt_bid_replenishment_{source_run.split('_')[0]}"
        )
    )
    out = out.resolve()
    if not out.is_relative_to(settings.data_dir.resolve()) or "sealed" in out.parts:
        raise ValueError("plan output must remain under the processed data directory")
    meta = {
        "schema": VERSION,
        "source_run": source_run,
        "source_manifest_sha256": digest(source / "manifest.json"),
        "source_events_sha256": digest(events),
        "source_git": manifest["git"],
        "data_build_id": manifest["data_build_id"],
        "period": EXPECTED_PERIOD,
        "events": len(rows),
        "windows": len(rows),
        "sampling": "all events, no availability/return filter",
        "early_offset_ns": -5_000_000_000,
        "late_offset_ns": -1,
        "max_age_ns": 1_000_000_000,
        "window_start_offset_ns": -10_000_000_000,
        "window_end_offset_ns": 2_000_000_000,
        "entry_price_field": "prior close compatibility placeholder; not a fill assumption",
        "postdecision_quotes": "never features; reserved for a future registered execution audit",
        "raw_plan_name": out.name,
        "windows_sha256": hashlib.sha256(payload).hexdigest(),
    }
    if out.exists():
        if (
            not (out / "plan.json").exists()
            or json.loads((out / "plan.json").read_text()) != meta
            or not (out / "windows.csv").is_file()
            or digest(out / "windows.csv") != meta["windows_sha256"]
        ):
            raise ValueError("refusing to overwrite a different published plan")
        return out
    out.mkdir(parents=True)
    (out / "windows.csv").write_bytes(payload)
    (out / "plan.json").write_text(json.dumps(meta, indent=2) + "\n")
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    out = prepare(load_settings(), args.source_run, args.output)
    print(out / "windows.csv")


if __name__ == "__main__":
    main()
