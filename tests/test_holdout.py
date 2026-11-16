"""The owner's unsealed build: refused without the token, kept apart from the research build,
identical to it before the seal, and good for exactly one run."""

import json
import shutil
from datetime import date
from pathlib import Path

import duckdb
import pyarrow.parquet as pq
import pytest

from kinn import run as runner
from kinn.core.settings import HOLDOUT_START, load_settings
from kinn.data import build, holdout, seal
from kinn.data.store import DataStore
from tests import synthetic_raw as syn

REPO = Path(__file__).resolve().parents[1]
CONFIG = """
params: {{entries_per_session: 6, hold_minutes: 45, seed: 4, min_sessions_prior: 5}}
risk: {{equity: 10000, position_dollars: 500, buying_power: 10000}}
period: {{start: {start}, end: {end}}}
lookahead_check_rate: 0.0
"""
SEALED_DAYS = 6


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("holdout")
    raw = syn.make_random_walk_raw(
        tmp / "raw", symbols=8, days=33, sealed=tmp / "sealed", sealed_days=SEALED_DAYS
    )
    settings = load_settings(
        {
            "KINN_RAW_DIR": str(raw),
            "KINN_DATA_DIR": str(tmp / "processed"),
            "KINN_RUNS_DIR": str(tmp / "runs"),
        }
    )
    assert build.build_bars(settings, budget_seconds=300, workers=2)[1] == 0
    assert not build.build_tables(settings)[1]
    strategies = tmp / "strategies"
    shutil.copytree(REPO / "strategies" / "random_entry", strategies / "random_entry")
    configs = strategies / "random_entry" / "configs"
    (configs / "before.yaml").write_text(CONFIG.format(start="2023-10-23", end="2023-11-08"))
    (configs / "after.yaml").write_text(CONFIG.format(start="2023-11-09", end="2023-11-16"))
    patch = pytest.MonkeyPatch()
    patch.setenv("KINN_STRATEGIES_DIR", str(strategies))
    patch.delenv(seal.TOKEN_VARIABLE, raising=False)
    yield settings, tmp / "sealed", patch
    patch.undo()


def trades(run_dir):
    rows = pq.read_table(run_dir / "trades.parquet").to_pylist()
    return [(t["day"], t["symbol"], t["quantity"], t["entry_minute"], t["net"]) for t in rows]


def test_everything_is_refused_without_the_owner_token(world):
    settings, sealed, _ = world
    with pytest.raises(seal.HoldoutError):
        holdout.build_unsealed(settings, sealed)
    with pytest.raises(seal.HoldoutError):
        DataStore(settings, unseal=True)
    with pytest.raises(seal.HoldoutError):
        runner.start_run("random_entry", "after", settings=settings, scratch=True, unseal=True)
    with pytest.raises(seal.HoldoutError):  # the ordinary path still refuses holdout dates
        runner.start_run("random_entry", "after", settings=settings, scratch=True)
    assert not (settings.data_dir / "holdout").exists()


def test_the_unsealed_build_is_separate_and_equal_before_the_seal(world):
    settings, sealed, patch = world
    research_before = (settings.data_dir / "builds" / "CURRENT").read_text()
    patch.setenv(seal.TOKEN_VARIABLE, "owner-secret")
    assert holdout.build_unsealed(settings, sealed, budget_seconds=-1)[1]  # out of time: pending
    build_id, pending = holdout.build_unsealed(settings, sealed)
    assert not pending
    report = holdout.check(settings)
    assert report["build_id"] == build_id and report["holdout_sessions"] == SEALED_DAYS
    assert report["first_session"] == HOLDOUT_START and report["last_session"] == date(2023, 11, 16)
    assert report["same_before_seal"] and report["rows_before_seal"] > 0
    assert report["panel_rows_in_holdout"] == SEALED_DAYS * 8
    assert holdout.covers(report, date(2023, 11, 16)) is False  # filings stop in 2021 here
    # The research build is untouched and still sealed.
    assert (settings.data_dir / "builds" / "CURRENT").read_text() == research_before
    research = settings.data_dir / "builds" / research_before.strip()
    latest = duckdb.sql(
        f"select max(date) from read_parquet('{research}/panel/*.parquet')"
    ).fetchall()[0][0]
    assert latest < HOLDOUT_START
    with pytest.raises(seal.HoldoutError):
        DataStore(settings).sessions(HOLDOUT_START, date(2023, 11, 16))
    opened = DataStore(settings, unseal=True)
    assert len(opened.sessions(HOLDOUT_START, date(2023, 11, 16))) == SEALED_DAYS
    assert opened.minute(date(2023, 11, 13)).num_rows > 0
    log = (settings.data_dir / seal.UNSEAL_LOG_NAME).read_text()
    assert "unsealed build" in log and "owner-secret" not in log
    patch.delenv(seal.TOKEN_VARIABLE)


def test_one_run_on_the_holdout_and_the_same_results_before_it(world):
    settings, _, patch = world
    plain = runner.start_run("random_entry", "before", settings=settings, scratch=True)
    assert runner.continue_run(plain, settings=settings)
    patch.setenv(seal.TOKEN_VARIABLE, "owner-secret")
    # Before the seal the unsealed build gives the research build's trades exactly.
    again = runner.start_run("random_entry", "before", settings=settings, scratch=True, unseal=True)
    assert runner.continue_run(again, settings=settings)
    assert trades(again) == trades(plain) and len(trades(plain)) > 20
    held = runner.start_run("random_entry", "after", settings=settings, scratch=True, unseal=True)
    assert not runner.continue_run(held, settings=settings, budget_seconds=-1)
    assert runner.continue_run(held, settings=settings, workers=2)
    manifest = json.loads((held / "manifest.json").read_text())
    assert manifest["unsealed"] is True and manifest["period"]["start"] == "2023-11-09"
    days = {t[0] for t in trades(held)}
    assert days and min(days) >= HOLDOUT_START and len(days) == SEALED_DAYS
    with pytest.raises(ValueError, match="never a sweep"):
        runner.continue_sweep([held, held], settings=settings)
    patch.delenv(seal.TOKEN_VARIABLE)
    # Without the token the paused or finished run cannot be continued or re-read.
    fresh = runner.start_run("random_entry", "before", settings=settings, scratch=True)
    assert "unsealed" not in json.loads((fresh / "manifest.json").read_text())
