"""Native source provenance, exact pre-decision snapshots, replay and run pinning."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
from dataclasses import replace
from datetime import date

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from kinn import cli
from kinn import run as runner
from kinn.core.types import BookPair, QuoteSnapshot, Signal
from kinn.data import inputs, quotes
from kinn.data.seal import HoldoutError
from kinn.data.store import DataStore
from kinn.data.universe import Universe
from kinn.engine.intraday.data import load_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals, input_sessions
from kinn.features.base import LookaheadError

DAY = date(2023, 10, 10)
PERIOD = {"start": "2023-10-09", "end": "2023-10-13"}
SOURCE = "fixture_gpt_bid_replenishment_reversal_control"
NAME = "bid_replenishment_reversal"
UNIVERSE = Universe("all", min_sessions_prior=1)


def candidate(day=DAY, symbol="AAA", company=1001, minute=600):
    return {
        "day": day,
        "symbol": symbol,
        "permaticker": company,
        "signal_minute": minute,
        "prev_close": 10.0,
        "adv20_prev": 1_000_000.0,
    }


def quote(timestamp, **changes):
    return {
        "sip_timestamp": timestamp,
        "bid_price": 10.0,
        "ask_price": 10.01,
        "bid_size": 100,
        "ask_size": 100,
        **changes,
    }


def records(day=DAY, minute=600):
    end = quotes.minute_ns(day, minute + 1)
    return [
        quote(end - 5_000_000_000),
        quote(end - 1, bid_size=300),
        quote(end + 1, bid_price=1000, ask_price=1001),
    ]


def write_raw(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def rewrite_plan(plan, **changes):
    meta = json.loads((plan / "plan.json").read_text())
    meta.update(changes)
    (plan / "plan.json").write_text(json.dumps(meta, indent=2) + "\n")


def environment(tmp_path, built, *, candidates=None):
    settings = replace(
        built, raw_dir=tmp_path / "raw", data_dir=tmp_path / "processed", runs_dir=tmp_path / "runs"
    )
    shutil.copytree(built.data_dir, settings.data_dir)
    build_id = (settings.data_dir / "builds/CURRENT").read_text().strip()
    source = settings.runs_dir / SOURCE
    source.mkdir(parents=True)
    manifest = {
        "run_id": SOURCE,
        "strategy": NAME,
        "kind": "event_study",
        "config": "development_control",
        "status": "complete",
        "scratch": False,
        "git": {"commit": "a" * 40, "dirty": False},
        "resolved_config": {"params": {"use_quotes": False}},
        "data_build_id": build_id,
        "period": {"start": "2003-09-10", "end": "2016-12-30"},
    }
    (source / "manifest.json").write_text(json.dumps(manifest))
    pq.write_table(pa.Table.from_pylist([candidate(date(2004, 1, 5))]), source / "events.parquet")
    candidates = candidates if candidates is not None else [candidate()]
    plan = settings.data_dir / "quotes_sample/native_fixture"
    inputs.write_nbbo_price_plan(settings, SOURCE, candidates, PERIOD, plan)
    raw = settings.raw_dir / "massive/quotes_sample/native_fixture"
    paths = [quotes.sample_file(raw, "quotes", r["day"], r["symbol"]) for r in candidates]
    for c, path in zip(candidates, paths, strict=True):
        write_raw(path, records(c["day"], c["signal_minute"]))
    return settings, plan, paths


def test_exact_nanosecond_targets_dst_and_future_quote_invariance():
    for day in (date(2010, 1, 4), date(2010, 7, 1)):
        end = quotes.minute_ns(day, 601)
        baseline = quotes.replenishment_pair(records(day), end)
        assert baseline[0] == "available"
        assert baseline[1].sip_timestamp == end - 5_000_000_000
        assert baseline[2].sip_timestamp == end - 1
        assert baseline[2].bid_size == 300
        changed = records(day)[:2] + [quote(end, bid_price=None), quote(end + 1, bid_size=-999)]
        assert quotes.replenishment_pair(changed, end) == baseline
        # Exact target is allowed, one nanosecond later is excluded at either target.
        assert (
            quotes.replenishment_pair([quote(end - 5_000_000_000 + 1), quote(end)], end)[1] is None
        )
    assert quotes.minute_ns(date(2010, 7, 1), 601) % (86400 * 10**9) == (14 * 60 + 1) * 60 * 10**9
    assert quotes.minute_ns(date(2010, 1, 4), 601) % (86400 * 10**9) == (15 * 60 + 1) * 60 * 10**9


@pytest.mark.parametrize(
    "bad",
    [
        {"bid_price": 0},
        {"bid_price": float("nan")},
        {"ask_price": float("inf")},
        {"ask_price": 10.0},
        {"ask_price": 9.9},
        {"bid_size": 0},
        {"bid_size": -1},
        {"bid_size": 1.5},
        {"ask_size": True},
        {"bid_price": "10.0"},
        {"ask_size": 2**63},
    ],
)
def test_invalid_latest_never_resurrects_older_valid_quote(bad):
    end = quotes.minute_ns(DAY, 601)
    rows = [quote(end - 5_000_000_000), quote(end - 100), quote(end - 1, **bad)]
    status, early, late = quotes.replenishment_pair(rows, end)
    assert status == "late_invalid" and early is not None and late is None


def test_ties_staleness_and_empty_are_explicit():
    end = quotes.minute_ns(DAY, 601)
    rows = records()[:2]
    assert quotes.replenishment_pair(rows + [rows[-1]], end)[0] == "available"
    assert (
        quotes.replenishment_pair(rows + [quote(end - 1, bid_size=299)], end)[0] == "late_conflict"
    )
    rows = [quote(end - 6_000_000_000), quote(end - 1_000_000_001)]
    assert quotes.replenishment_pair(rows, end)[0] == "available"
    rows[-1]["sip_timestamp"] -= 1
    assert quotes.replenishment_pair(rows, end)[0] == "late_stale"
    assert quotes.replenishment_pair([], end) == ("early_missing;late_missing", None, None)


def test_builder_all_parents_empty_status_coverage_and_raw_immutability(tmp_path, built):
    settings, plan, paths = environment(
        tmp_path, built, candidates=[candidate(), candidate(symbol="OLD", company=1002)]
    )
    write_raw(paths[1], [])
    before = [p.read_bytes() for p in paths]
    input_id = inputs.build_nbbo_replenishment(settings, plan)
    meta = inputs.info(settings, "nbbo_replenishment")
    assert meta["rows"] == 2
    assert meta["coverage"]["all"] == {
        "parents": 2,
        "valid_pairs": 1,
        "valid_pair_fraction": 0.5,
        "statuses": {"available": 1, "early_missing;late_missing": 1},
    }
    assert meta["coverage"]["by_year"]["2023"]["parents"] == 2
    assert meta["coverage"]["2013_2016"]["valid_pair_fraction"] is None
    assert [p.read_bytes() for p in paths] == before
    assert inputs.build_nbbo_replenishment(settings, plan) == input_id
    store = DataStore(settings)
    view = load_day(store, DAY, UNIVERSE, nbbo_replenishment_sessions=1).view
    pair = view.book_pairs["AAA"][0]
    assert isinstance(pair, BookPair) and isinstance(pair.early, QuoteSnapshot)
    assert pair.late.bid_size == 300 and view.book_pairs["OLD"][0].status != "available"
    assert not any(view.upto(599).book_pairs.values())
    assert view.upto(600).book_pairs == view.book_pairs
    assert not store.nbbo_replenishment(DAY, asof_minute=599).num_rows
    assert not store.nbbo_replenishment(date(2023, 10, 11)).num_rows
    assert load_day(store, DAY, UNIVERSE).view.book_pairs == {}
    assert store.input_id("nbbo_replenishment") == input_id


def test_missing_file_refuses_before_publication_or_silent_zero(tmp_path, built):
    settings, plan, paths = environment(tmp_path, built)
    paths[0].unlink()
    with pytest.raises(inputs.InputError, match="1 of 1 quote files missing"):
        inputs.build_nbbo_replenishment(settings, plan)
    assert not inputs.root(settings, "nbbo_replenishment").exists()
    with pytest.raises(inputs.InputError, match="not built"):
        DataStore(settings).nbbo_replenishment(DAY)


@pytest.mark.parametrize(
    "change",
    [
        "window_hash",
        "manifest_hash",
        "events_hash",
        "missing_parent",
        "time",
        "company",
        "definition",
        "build",
    ],
)
def test_changed_sources_or_parent_population_fail_closed(tmp_path, built, change):
    settings, plan, _ = environment(tmp_path, built)
    source = settings.runs_dir / SOURCE
    if change == "window_hash":
        with (plan / "windows.csv").open("a") as handle:
            handle.write("\n")
    elif change in ("manifest_hash", "events_hash"):
        with (source / ("manifest.json" if change == "manifest_hash" else "events.parquet")).open(
            "ab"
        ) as handle:
            handle.write(b" ")
    elif change == "build":
        rewrite_plan(plan, data_build_id="wrong")
    elif change == "definition":
        rewrite_plan(plan, late_offset_ns=0)
    else:
        with (plan / "windows.csv").open(newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        if change == "missing_parent":
            rows = []
        else:
            rows[0]["signal_minute" if change == "time" else "permaticker"] = "777"
        with (plan / "windows.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        rewrite_plan(plan, windows_sha256=inputs._content_hash(plan / "windows.csv"))
    with pytest.raises(inputs.InputError):
        inputs.build_nbbo_replenishment(settings, plan)
    assert not inputs.root(settings, "nbbo_replenishment").exists()


@pytest.mark.parametrize(
    "change", ["float_timestamp", "other_date", "sealed", "outside_window", "symbol"]
)
def test_raw_provenance_seal_and_window_guards(tmp_path, built, change):
    settings, plan, paths = environment(tmp_path, built)
    row = records()[0]
    if change == "float_timestamp":
        row["sip_timestamp"] = float(row["sip_timestamp"])
    elif change in ("other_date", "sealed"):
        row["sip_timestamp"] = quotes.minute_ns(
            date(2023, 10, 11) if change == "other_date" else date(2023, 11, 9), 601
        )
    elif change == "outside_window":
        row["sip_timestamp"] -= 20_000_000_000
    else:
        row["ticker"] = "WRONG"
    write_raw(paths[0], [row])
    with pytest.raises((inputs.InputError, HoldoutError)):
        inputs.build_nbbo_replenishment(settings, plan)
    assert not inputs.root(settings, "nbbo_replenishment").exists()


def test_reader_range_seal_identity_and_immutable_hash(tmp_path, built):
    settings, plan, _ = environment(tmp_path, built)
    input_id = inputs.build_nbbo_replenishment(settings, plan)
    store = DataStore(settings)
    with pytest.raises(inputs.InputError, match="indexes price candidates"):
        store.nbbo_replenishment(date(2023, 10, 20))
    store._unseal = True  # Synthetic object only. This input still refuses sealed dates.
    with pytest.raises(HoldoutError):
        store.nbbo_replenishment(date(2023, 11, 9))
    with pytest.raises(ValueError, match="parent identity"):
        load_day(store, DAY, Universe("empty", min_prev_close=1000), nbbo_replenishment_sessions=1)
    for sessions in (0, 2, True):
        with pytest.raises(ValueError, match="sessions=1"):
            store.nbbo_replenishment(DAY, sessions=sessions)
    path = inputs.root(settings, "nbbo_replenishment") / input_id / "pairs.parquet"
    table = pq.read_table(path)
    row = table.to_pylist()[0]
    row["late"]["sip_timestamp"] = quotes.minute_ns(date(2023, 11, 9), 601)
    pq.write_table(pa.Table.from_pylist([row], schema=table.schema), path)
    with pytest.raises(inputs.InputError, match="hash mismatch"):
        DataStore(settings).nbbo_replenishment(DAY)


STRATEGY = """
from kinn.core.types import Signal
from kinn.data.universe import Universe
class TestBook:
    name = "bid_replenishment_reversal"
    universe = Universe("all", min_sessions_prior=1)
    features = ()
    inputs = {"nbbo_replenishment": {"sessions": 1}}
    def signals(self, view, features):
        return [Signal(s, p.minute) for s, rows in view.book_pairs.items()
                for p in rows if p.status == "available"]
def build(params):
    return TestBook()
"""


def test_runner_manifest_hash_pin_resume_and_spawn(tmp_path, built, monkeypatch):
    settings, plan, paths = environment(tmp_path, built)
    first_id = inputs.build_nbbo_replenishment(settings, plan)
    folder = tmp_path / "strategies" / NAME
    (folder / "configs").mkdir(parents=True)
    (folder / "strategy.py").write_text(STRATEGY)
    (folder / "strategy.yaml").write_text(
        f"name: {NAME}\nfamily: fixture\ncost_calibration: ibkr_pro_tiered\n"
    )
    (folder / "configs/week.yaml").write_text(
        "period: {start: 2023-10-09, end: 2023-10-13}\nlookahead_check_rate: 1.0\n"
    )
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(tmp_path / "strategies"))
    original_git = runner.registry._git
    monkeypatch.setattr(
        runner.registry,
        "_git",
        lambda repo, *args: STRATEGY.strip() if args[0] == "show" else original_git(repo, *args),
    )
    run = runner.start_run(NAME, "week", settings=settings, scratch=True, agent="test")
    manifest = json.loads((run / "manifest.json").read_text())
    assert manifest["inputs"]["nbbo_replenishment"]["input_id"] == first_id
    assert manifest["inputs"]["nbbo_replenishment"]["coverage"]["all"]["parents"] == 1
    assert not runner.continue_run(run, settings=settings, budget_seconds=0)
    write_raw(paths[0], [])
    second_id = inputs.build_nbbo_replenishment(settings, plan)
    assert second_id != first_id
    pinned = DataStore(settings, inputs={"nbbo_replenishment": first_id})
    assert pinned.nbbo_replenishment(DAY).to_pylist()[0]["status"] == "available"
    assert DataStore(settings).nbbo_replenishment(DAY).to_pylist()[0]["status"] != "available"
    next_run = runner.start_run(NAME, "week", settings=settings, scratch=True, agent="test")
    next_manifest = json.loads((next_run / "manifest.json").read_text())
    assert next_manifest["config_hash"] != manifest["config_hash"]
    assert runner.continue_run(run, settings=settings, workers=2)
    assert json.loads((run / "metrics.json").read_text())["counts"]["signals"] == 1
    with pytest.raises(ValueError, match="pinned input"):
        runner.continue_sweep([run, next_run], settings=settings)
    view = load_day(pinned, DAY, UNIVERSE, nbbo_replenishment_sessions=1).view
    strategy = runner.load_strategy(NAME, {})
    check_no_lookahead(strategy, view, day_signals(strategy, view), [599, 600, 601])

    class Cheater(type(strategy)):
        def signals(self, view, features):
            return [Signal("AAA", 599)] if any(view.book_pairs.values()) else []

    with pytest.raises(LookaheadError):
        check_no_lookahead(Cheater(), view, day_signals(Cheater(), view), [599])
    (folder / "strategy.py").write_text(STRATEGY + "\n# changed rule\n")
    with pytest.raises(ValueError, match="price definition changed"):
        runner.start_run(NAME, "week", settings=settings, scratch=True, agent="test")
    with pytest.raises(ValueError, match="changed after run creation"):
        runner.continue_run(next_run, settings=settings)


def test_cli_declaration_and_price_only_plan_rejects_seal_before_loading(
    tmp_path, built, monkeypatch, capsys
):
    settings, plan, _ = environment(tmp_path, built)
    monkeypatch.setattr(cli, "load_settings", lambda: settings)
    assert (
        cli._inputs(argparse.Namespace(name="nbbo_replenishment", action="build", plan=str(plan)))
        == 0
    )
    assert quotes.NBBO_VERSION in capsys.readouterr().out
    for options in ({"sessions": 2}, {"sessions": True}, {"other": 1}):
        strategy = type("Bad", (), {"inputs": {"nbbo_replenishment": options}})()
        with pytest.raises(ValueError, match="sessions=1"):
            input_sessions(strategy, "nbbo_replenishment")
    with pytest.raises(HoldoutError):
        runner.prepare_nbbo_plan(
            SOURCE, date(2023, 11, 9), date(2023, 11, 9), plan, settings=settings
        )


def test_native_build_postdecision_perturbation_changes_id_only(tmp_path, built):
    settings, plan, paths = environment(tmp_path, built)
    first_id = inputs.build_nbbo_replenishment(settings, plan)
    before = DataStore(settings).nbbo_replenishment(DAY).to_pylist()
    end = quotes.minute_ns(DAY, 601)
    write_raw(paths[0], records()[:2] + [quote(end, bid_price=-999, ask_size=None)])
    second_id = inputs.build_nbbo_replenishment(settings, plan)
    assert second_id != first_id
    assert DataStore(settings).nbbo_replenishment(DAY).to_pylist() == before


def test_source_plan_and_native_identity_time_conflicts_fail_closed(tmp_path, built):
    settings, plan, _ = environment(tmp_path, built, candidates=[candidate(symbol="WRONG")])
    inputs.build_nbbo_replenishment(settings, plan)
    with pytest.raises(ValueError, match="parent identity"):
        load_day(DataStore(settings), DAY, UNIVERSE, nbbo_replenishment_sessions=1)
    table = pq.read_table(plan / "candidates.parquet").to_pylist()
    table[0]["signal_minute"] = 600
    table.append(table[0])
    pq.write_table(pa.Table.from_pylist(table), plan / "candidates.parquet")
    rewrite_plan(plan, candidates_sha256=inputs._content_hash(plan / "candidates.parquet"))
    with pytest.raises(ValueError, match="one first price event"):
        inputs.build_nbbo_replenishment(settings, plan)


def test_price_only_planning_writes_no_outcomes_and_is_immutable(tmp_path, built, monkeypatch):
    settings, _, _ = environment(tmp_path, built)

    class PriceOnly:
        inputs = {}
        features = ()
        universe = UNIVERSE
        name = NAME

        def signals(self, view, features):
            bars = view.symbols["AAA"]
            return [Signal("AAA", 700)] if 700 in bars.minute else []

    monkeypatch.setattr(runner, "load_strategy", lambda name, params: PriceOnly())
    monkeypatch.setattr(runner, "check_nbbo_price_definition", lambda source, **kwargs: "frozen")
    monkeypatch.setattr(runner.registry, "git_state", lambda repo: {"dirty": False})

    def forbidden(*args, **kwargs):
        raise AssertionError("acquisition planning must not measure forward outcomes or simulate")

    monkeypatch.setattr(runner, "simulate_day", forbidden)
    # All study outcome computation is through this module; planning must not call it.
    monkeypatch.setattr(runner.event_study, "measure", forbidden)
    monkeypatch.setattr(runner.event_study, "measure_extended", forbidden)
    output = settings.data_dir / "quotes_sample/frozen_price_only"
    runner.prepare_nbbo_plan(SOURCE, DAY, DAY, output, settings=settings)
    meta, windows, _ = inputs.validate_nbbo_plan(settings, output)
    assert meta["source_kind"] == "price_plan" and len(windows) == 1
    assert pq.read_schema(output / "candidates.parquet").names == list(
        quotes.NBBO_CANDIDATE_COLUMNS
    )
    assert windows[0]["signal_minute"] == 700
    # Downloader's compatibility entry_price is strictly the prior close.
    assert (
        windows[0]["entry_price"]
        == pq.read_table(output / "candidates.parquet")["prev_close"][0].as_py()
    )
    assert runner.prepare_nbbo_plan(SOURCE, DAY, DAY, output, settings=settings) == output
    with (output / "windows.csv").open("a") as handle:
        handle.write("\n")
    with pytest.raises(inputs.InputError, match="hash changed"):
        runner.prepare_nbbo_plan(SOURCE, DAY, DAY, output, settings=settings)
