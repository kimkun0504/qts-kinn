"""Native timed 8-K parsing, identity, point-in-time view and pinned runner contracts."""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import shutil
import zipfile
from dataclasses import replace
from datetime import UTC, date, datetime

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from kinn import cli
from kinn import run as runner
from kinn.core.types import TimedReport
from kinn.data import inputs
from kinn.data.seal import HoldoutError
from kinn.data.store import DataStore
from kinn.data.universe import Universe
from kinn.engine.intraday.data import load_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals, input_sessions

UNIVERSE = Universe("all", min_sessions_prior=1)


def record(day="2023-10-10", *, cik=100, accession="earnings", items="2.02,9.01", **changes):
    return {
        "cik": cik,
        "accession": accession,
        "form": "8-K",
        "filed": day,
        "accepted": f"{day}T20:00:30Z",
        "items": items,
        **changes,
    }


def write_records(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def environment(tmp_path, built, *, rows=None, identities=None):
    settings = replace(
        built, raw_dir=tmp_path / "raw", data_dir=tmp_path / "processed", runs_dir=tmp_path / "runs"
    )
    shutil.copytree(built.data_dir, settings.data_dir)
    build_id = (settings.data_dir / "builds/CURRENT").read_text().strip()
    info = json.loads((settings.data_dir / "builds" / build_id / "build.json").read_text())
    snapshot = settings.raw_dir / "sharadar" / info["sharadar_snapshot"]
    snapshot.mkdir(parents=True)
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["table", "permaticker", "secfilings"])
    for company, cik in identities or [(1001, 100), (1002, 200)]:
        writer.writerow(["SEP", company, f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik}"])
    with zipfile.ZipFile(snapshot / "SHARADAR_TICKERS_fixture.zip", "w") as archive:
        archive.writestr("tickers.csv", stream.getvalue())
    source = settings.raw_dir / "sec/filing_times/8k.jsonl.gz"
    rows = (
        rows
        if rows is not None
        else [
            record("2023-10-09", accession="begin", items="9.01"),
            record(),
            record(cik=200, accession="renamed-before", items="1.01"),
            record("2023-10-17", cik=200, accession="renamed-after"),
            record("2023-10-20", accession="end", items="9.01"),
        ]
    )
    write_records(source, rows)
    return settings, source, rows


def test_parser_aware_offsets_seconds_and_dst():
    winter = inputs._timed_record(record("2010-01-04", accepted="2010-01-04T16:00:59-05:00"))
    summer = inputs._timed_record(record("2010-07-01", accepted="2010-07-01T20:00:00Z"))
    assert winter["accepted"] == datetime(2010, 1, 4, 21, 0, 59, tzinfo=UTC)
    assert winter["usable_minute"] == summer["usable_minute"] == 961
    assert winter["items"] == ["2.02", "9.01"] and winter["earnings"]


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"accepted": "2023-10-10T16:00:30"}, "invalid_timestamp"),
        ({"accepted": None}, "invalid_timestamp"),
        ({"filed": "2023-11-09"}, "sealed_filed"),
        ({"accepted": "2023-11-09T15:00:00Z"}, "sealed_accepted"),
        ({"form": "8-K/A"}, "other_form"),
        ({"items": "2.02,invalid"}, "invalid_items"),
        ({"accession": ""}, "missing_accession"),
    ],
)
def test_parser_rejects_unknown_timing_and_both_seal_dates(changes, reason):
    with pytest.raises(ValueError, match=reason):
        inputs._timed_record(record(**changes))


def test_builder_keeps_accessions_separate_and_rejects_duplicates_conflicts_and_bad_rows(
    tmp_path, built
):
    rows = [
        record(),
        record(),
        record(accession="other", items="1.01"),
        record(accession="conflict", items="2.02"),
        record(accession="conflict", items="1.01"),
        record(accession="unknown", cik=999),
        record(accession="cross-issuer", cik=100),
        record(accession="cross-issuer", cik=999),
        record(accession="naive", accepted="2023-10-10T16:00:00"),
        record(accession="future", filed="2023-11-09"),
        record(accession="future-accepted", accepted="2023-11-09T15:00:00Z"),
    ]
    settings, source, _ = environment(tmp_path, built, rows=rows)
    before = source.read_bytes()
    input_id = inputs.build_form8k_timed(settings)
    meta = inputs.info(settings, "form8k_timed")
    assert meta["input_id"] == input_id and meta["rows"] == 2
    assert meta["rejections"]["exact_duplicates"] == 1
    assert meta["rejections"]["conflicting_accessions"] == 2
    assert meta["rejections"]["invalid_timestamp"] == 1
    assert meta["rejections"]["sealed_filed"] == meta["rejections"]["sealed_accepted"] == 1
    rows = DataStore(settings).form8k_timed(date(2023, 10, 10)).to_pylist()
    assert [(r["accession"], r["items"]) for r in rows] == [
        ("earnings", ["2.02", "9.01"]),
        ("other", ["1.01"]),
    ]
    assert source.read_bytes() == before
    assert inputs.build_form8k_timed(settings) == input_id


def test_ambiguous_issuer_and_security_mappings_are_not_guessed(tmp_path, built):
    rows = [record(cik=100), record(cik=200, accession="good")]
    settings, _, _ = environment(
        tmp_path, built, rows=rows, identities=[(1001, 100), (1002, 100), (1002, 200)]
    )
    with pytest.raises(inputs.InputError, match="no unambiguous"):
        inputs.build_form8k_timed(settings)
    assert not (inputs.root(settings, "form8k_timed") / "CURRENT").exists()


def test_native_view_uses_day_symbol_and_hides_future_filings_at_each_prefix(tmp_path, built):
    settings, _, _ = environment(tmp_path, built)
    inputs.build_form8k_timed(settings)
    store = DataStore(settings)
    day = date(2023, 10, 10)
    assert not store.form8k_timed(day, asof_minute=960).num_rows
    assert store.form8k_timed(day, asof_minute=961).num_rows == 2
    assert not store.form8k_timed(date(2023, 10, 11)).num_rows
    view = load_day(store, day, UNIVERSE, form8k_timed_sessions=1).view
    assert isinstance(view.timed_reports["AAA"][0], TimedReport)
    assert view.timed_reports["OLD"][0].permaticker == 1002
    assert not any(view.upto(960).timed_reports.values())
    assert view.upto(961).timed_reports == view.timed_reports
    later = load_day(store, date(2023, 10, 17), UNIVERSE, form8k_timed_sessions=1).view
    assert "NEW" in later.timed_reports and "OLD" not in later.timed_reports
    assert load_day(store, day, UNIVERSE).view.timed_reports == {}


def test_missing_input_coverage_and_seal_fail_explicitly(tmp_path, built):
    settings, _, _ = environment(tmp_path, built)
    store = DataStore(settings)
    with pytest.raises(inputs.InputError, match="not built"):
        store.form8k_timed(date(2023, 10, 10))
    inputs.build_form8k_timed(settings)
    with pytest.raises(inputs.InputError, match="archive envelope"):
        store.form8k_timed(date(2023, 10, 23))
    with pytest.raises(HoldoutError):
        store.form8k_timed(date(2023, 11, 9))
    for sessions in (0, 2, True):
        with pytest.raises(ValueError, match="sessions=1"):
            store.form8k_timed(date(2023, 10, 10), sessions=sessions)


STRATEGY = """
from kinn.core.types import Signal
from kinn.data.universe import Universe

class Timed:
    name = "timed"
    features = ()
    universe = Universe("all",min_sessions_prior=1)
    inputs = {"form8k_timed":{"sessions":1}}
    def signals(self, view, features):
        return [Signal(s,r.usable_minute) for s,rows in view.timed_reports.items()
                for r in rows if r.earnings]
def build(params):
    return Timed()
"""


def test_runner_pins_input_in_manifest_hash_resume_and_spawn_workers(tmp_path, built, monkeypatch):
    settings, source, rows = environment(tmp_path, built)
    first_id = inputs.build_form8k_timed(settings)
    folder = tmp_path / "strategies/timed"
    (folder / "configs").mkdir(parents=True)
    (folder / "strategy.py").write_text(STRATEGY)
    (folder / "strategy.yaml").write_text(
        "name: timed\nfamily: timed\ncost_calibration: ibkr_pro_tiered\n"
    )
    (folder / "configs/week.yaml").write_text(
        "period: {start: 2023-10-09, end: 2023-10-13}\nlookahead_check_rate: 1.0\n"
    )
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(tmp_path / "strategies"))
    run = runner.start_run("timed", "week", settings=settings, scratch=True, agent="test")
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["inputs"]["form8k_timed"]["input_id"] == first_id
    assert not runner.continue_run(run, settings=settings, budget_seconds=0)
    # A later input corrects/conflicts with the old accession. Existing runs still use the old id.
    write_records(source, rows + [record(items="1.01")])
    second_id = inputs.build_form8k_timed(settings)
    assert second_id != first_id
    pinned = DataStore(settings, inputs={"form8k_timed": first_id})
    assert any(r["earnings"] for r in pinned.form8k_timed(date(2023, 10, 10)).to_pylist())
    assert not any(
        r["earnings"] for r in DataStore(settings).form8k_timed(date(2023, 10, 10)).to_pylist()
    )
    next_run = runner.start_run("timed", "week", settings=settings, scratch=True, agent="test")
    new_manifest = json.loads((next_run / "manifest.json").read_text())
    assert new_manifest["config_hash"] != manifest["config_hash"]
    assert runner.continue_run(run, settings=settings, workers=2)
    metrics = json.loads((run / "metrics.json").read_text())
    assert metrics["counts"]["signals"] == 1
    strategy = runner.load_strategy("timed", {})
    view = load_day(pinned, date(2023, 10, 10), UNIVERSE, form8k_timed_sessions=1).view
    check_no_lookahead(strategy, view, day_signals(strategy, view), [960, 961])
    with pytest.raises(ValueError, match="pinned input"):
        runner.continue_sweep([run, next_run], settings=settings)


def test_cli_and_invalid_declaration(tmp_path, built, monkeypatch, capsys):
    settings, _, _ = environment(tmp_path, built)
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    assert cli._inputs(argparse.Namespace(name="form8k_timed", action="build")) == 0
    assert inputs.FORM8K_TIMED_VERSION in capsys.readouterr().out

    class Bad:
        inputs = {"form8k_timed": {"sessions": 2}}

    with pytest.raises(ValueError, match="sessions=1"):
        input_sessions(Bad(), "form8k_timed")


def test_reader_rejects_misbuilt_future_timestamps_and_has_no_unseal_path(tmp_path, built):
    settings, _, _ = environment(tmp_path, built)
    input_id = inputs.build_form8k_timed(settings)
    path = inputs.root(settings, "form8k_timed") / input_id / "reports.parquet"
    table = pq.read_table(path)
    poisoned = table.to_pylist()[1].copy()
    poisoned.update(accession="poison", accepted=datetime(2023, 11, 9, 20, tzinfo=UTC))
    pq.write_table(pa.Table.from_pylist(table.to_pylist() + [poisoned], schema=table.schema), path)
    store = DataStore(settings)
    assert "poison" not in store.form8k_timed(date(2023, 10, 10))["accession"].to_pylist()
    store._unseal = True  # Synthetic object only; this input still refuses the date.
    with pytest.raises(HoldoutError):
        store.form8k_timed(date(2023, 11, 9))
