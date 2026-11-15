import gzip
import json
from datetime import date

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from kinn.costs import model as cost_model
from kinn.data import quotes, seal

COSTS = cost_model.load("ibkr_pro_tiered")


def events_file(tmp_path, rows):
    cols = ["day", "symbol", "signal_minute", "entry_minute", "entry_price", "adv20_prev"]
    table = pa.table({c: [r[i] for r in rows] for i, c in enumerate(cols)})
    path = tmp_path / "events.parquet"
    pq.write_table(table, path)
    return path


def test_minute_ns_handles_daylight_saving():
    assert quotes.minute_ns(date(2019, 6, 3), 570) == 1559568600 * 10**9  # 13:30 UTC
    assert quotes.minute_ns(date(2019, 12, 2), 570) == 1575297000 * 10**9  # 14:30 UTC


def test_plan_draws_from_every_cell_and_measure_compares_with_the_model(tmp_path):
    rows = []
    for year in (2010, 2020):
        for adv in (5e5, 5e6, 5e7):
            for k in range(5):
                rows.append((date(year, 3, 2 + k), f"S{int(adv)}", 640, 641, 10.0, adv))
    path = quotes.plan(events_file(tmp_path, rows), tmp_path / "plan", per_cell=3, seed=1)
    windows = quotes.read_windows(path)
    assert len(windows) == 18 and {w["bucket"] for w in windows} == {b[0] for b in quotes.BUCKETS}
    first = windows[0]
    assert first["entry_ns"] - first["start_ns"] == 60 * 10**9
    assert first["end_ns"] - first["entry_ns"] == 600 * 10**9

    raw = tmp_path / "raw"
    for w in windows[:-1]:  # one file is left missing
        file = quotes.sample_file(raw, "quotes", w["day"], w["symbol"])
        file.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(file, "wt") as handle:
            for ts, bid, ask in (
                (w["start_ns"], 9.95, 10.05),
                (w["entry_ns"] - 1, 9.90, 10.10),
                (w["entry_ns"] + 5, 1.0, 99.0),
                (w["end_ns"] - 1, 9.98, 10.02),
            ):
                handle.write(
                    json.dumps(
                        {"sip_timestamp": ts, "bid_price": bid, "ask_price": ask, "ask_size": 1}
                    )
                    + "\n"
                )
    result = quotes.measure(windows, raw, COSTS.half_spread_bps)
    assert result["missing_files"] == 1 and result["all"]["events"] == 17
    # The last quote at or before the entry is 9.90 x 10.10: a half-spread of 100 bps.
    assert result["all"]["quoted_half_bps_median"] == pytest.approx(100.0)
    assert result["all"]["later_half_bps_median"] == pytest.approx(20.0)
    assert result["all"]["ask_vs_assumed_bps_median"] == pytest.approx(100.0)
    liquid = result["by_bucket"]["ADV $10M and over"]
    assert liquid["model_half_bps_median"] == pytest.approx(5.0)  # table value for $10–50M
    assert liquid["share_model_too_low"] == 1.0
    assert "Model too low" in quotes.render(result, "test")


def test_holdout_events_cannot_be_planned(tmp_path):
    path = events_file(tmp_path, [(date(2024, 1, 5), "AAA", 640, 641, 10.0, 5e6)])
    with pytest.raises(seal.HoldoutError):
        quotes.plan(path, tmp_path / "plan")
