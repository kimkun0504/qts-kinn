"""Subprocess tests for acquisition metadata; nothing imports the research sandbox."""

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

SCRIPT = Path(__file__).resolve().parents[1] / "research/gpt/plan_bid_quote_windows.py"
RID = "20160101T000000Z_gpt_bid_replenishment_reversal_abcdef12"


def setup(tmp_path, *, forward=1.0, scratch=False):
    from datetime import date

    runs = tmp_path / "runs"
    data = tmp_path / "processed"
    source = runs / RID
    source.mkdir(parents=True)
    manifest = {
        "run_id": RID,
        "strategy": "bid_replenishment_reversal",
        "kind": "event_study",
        "config": "development_control",
        "status": "complete",
        "scratch": scratch,
        "git": {"dirty": False, "commit": "synthetic"},
        "resolved_config": {"params": {"use_quotes": False}},
        "period": {"start": "2003-09-10", "end": "2016-12-30"},
        "data_build_id": "synthetic",
    }
    (source / "manifest.json").write_text(json.dumps(manifest))
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "day": date(2010, 1, 4),
                    "symbol": "ABC",
                    "permaticker": 1,
                    "signal_minute": 600,
                    "prev_close": 10.0,
                    "adv20_prev": 10e6,
                    "entry_price": 999.0,
                    "r_120": forward,
                },
                {
                    "day": date(2010, 7, 1),
                    "symbol": "DEF",
                    "permaticker": 2,
                    "signal_minute": 600,
                    "prev_close": 20.0,
                    "adv20_prev": 20e6,
                    "entry_price": 888.0,
                    "r_120": -forward,
                },
            ]
        ),
        source / "events.parquet",
    )
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": str(SCRIPT.parents[2] / "src"),
        "KINN_RUNS_DIR": str(runs),
        "KINN_DATA_DIR": str(data),
        "KINN_RAW_DIR": str(tmp_path / "raw"),
        "UV_NO_ENV_FILE": "1",
    }
    return env, data


def invoke(env, output=None):
    args = [sys.executable, str(SCRIPT), "--source-run", RID]
    if output is not None:
        args += ["--output", str(output)]
    return subprocess.run(args, env=env, text=True, capture_output=True, check=False)


def test_all_events_outcomes_ignored_dst_and_immutable_plan(tmp_path):
    env, _ = setup(tmp_path / "a", forward=1)
    result = invoke(env)
    assert result.returncode == 0, result.stderr
    path = Path(result.stdout.strip())
    with path.open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2 and rows[0]["entry_price"] == "10.0"
    assert int(rows[0]["entry_ns"]) - int(rows[0]["start_ns"]) == 10_000_000_000
    assert int(rows[0]["end_ns"]) - int(rows[0]["entry_ns"]) == 2_000_000_000
    assert int(rows[0]["late_target_ns"]) == int(rows[0]["entry_ns"]) - 1
    assert invoke(env).returncode == 0
    other, _ = setup(tmp_path / "b", forward=1000)
    result2 = invoke(other)
    assert result2.returncode == 0, result2.stderr
    assert Path(result2.stdout.strip()).read_bytes() == path.read_bytes()
    # 10:01 ET maps to different UTC hours across the daylight-saving boundary.
    from datetime import UTC, datetime

    assert datetime.fromtimestamp(int(rows[0]["entry_ns"]) / 1e9, tz=UTC).hour == 15
    assert datetime.fromtimestamp(int(rows[1]["entry_ns"]) / 1e9, tz=UTC).hour == 14


def test_raw_output_and_scratch_sources_are_refused(tmp_path):
    env, _ = setup(tmp_path / "normal")
    result = invoke(env, Path(env["KINN_RAW_DIR"]) / "plan")
    assert result.returncode != 0 and not Path(env["KINN_RAW_DIR"]).exists()
    env, _ = setup(tmp_path / "scratch", scratch=True)
    assert invoke(env).returncode != 0
