"""A book run end to end on a synthetic build: files, resuming, and what the Workbench reads."""

import json

import pyarrow.parquet as pq
import pytest

from apps.workbench import api
from kinn import book_run
from kinn.core.settings import load_settings
from kinn.data import build
from tests import synthetic_raw as syn

ALPHA = """
import numpy as np


class Trailing:
    name, lookback = "trailing", 5

    def scores(self, view):
        r = view.history("ret", 5)
        return r.mean(axis=0) if len(r) == 5 else np.full(r.shape[1], np.nan)


def build(params):
    return Trailing()
"""
BOOK = """
book: tiny
family: tiny_family
cost_calibration: ibkr_pro_tiered
account: 25000
universe: {min_sessions_prior: 5}
alphas: [{strategy: trailing}]
risk_model: {window: 8, min_obs: 5}
portfolio: {kind: ranked, count: 3}
limits: {gross: 1.0, max_weight: 0.2, beta: null, sector: null}
execution: {at: close, min_trade: 0}
short: {min_marketcap: 0, min_price: 0}
rebalance: weekly
lookahead_check_rate: 1.0
period: {start: 2023-10-16, end: 2023-11-08}
"""


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("book")
    raw = syn.make_random_walk_raw(tmp / "raw", symbols=10, days=33)
    settings = load_settings({
        "KINN_RAW_DIR": str(raw), "KINN_DATA_DIR": str(tmp / "processed"),
        "KINN_RUNS_DIR": str(tmp / "runs"),
    })  # fmt: skip
    assert build.build_bars(settings, budget_seconds=300, workers=2)[1] == 0
    assert not build.build_tables(settings)[1]
    (tmp / "strategies" / "trailing").mkdir(parents=True)
    (tmp / "strategies" / "trailing" / "alpha.py").write_text(ALPHA)
    (tmp / "books").mkdir()
    (tmp / "books" / "tiny.yaml").write_text(BOOK)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("KINN_STRATEGIES_DIR", str(tmp / "strategies"))
        patch.setenv("KINN_BOOKS_DIR", str(tmp / "books"))
        run_dir = book_run.start_run("tiny", settings=settings, scratch=True, agent="t")
        assert not book_run.continue_run(run_dir, settings=settings, budget_seconds=-1)
        assert book_run.continue_run(run_dir, settings=settings)
        yield settings, run_dir


def test_a_book_run_writes_its_series_fills_positions_and_metrics(run):
    _, run_dir = run
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["kind"] == "book" and manifest["status"] == "complete"
    assert manifest["alphas"] == ["trailing"] and manifest["family"] == "tiny_family"
    daily = pq.read_table(run_dir / "daily.parquet").to_pydict()
    assert [str(d) for d in daily["date"]] == manifest["sessions"]
    assert daily["n_long"][-1] == 3 and daily["n_short"][-1] == 3
    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert metrics["fills"] == pq.read_table(run_dir / "fills.parquet").num_rows > 6
    assert metrics["counts"]["lookahead_checks"] == metrics["counts"]["rebalances"] == 4
    assert metrics["exposure"]["gross_max"] < 1.2
    total = metrics["slippage_1x"]["total_net"]
    assert total == pytest.approx(daily["equity"][-1] - 25_000)
    assert total == pytest.approx(sum(metrics["attribution"].values()), abs=0.01)


def test_a_book_run_resumes_from_the_saved_month_end_state(run):
    settings, run_dir = run
    before = pq.read_table(run_dir / "daily.parquet")
    fills = pq.read_table(run_dir / "fills.parquet")
    for path in (run_dir / "parts").glob("2023-11.*"):
        path.unlink()  # as if the run had stopped at the end of October
    assert book_run.continue_run(run_dir, settings=settings)
    assert pq.read_table(run_dir / "daily.parquet").equals(before)
    assert pq.read_table(run_dir / "fills.parquet").equals(fills)


def test_the_workbench_reads_a_book_run(run):
    settings, run_dir = run
    (row,) = api.list_runs(settings.runs_dir)
    assert row["kind"] == "book" and row["strategy"] == "tiny" and row["trades"] > 6
    assert row["net_1x"] is not None and row["sharpe"] is not None
    detail = api.run_detail(settings.runs_dir, run_dir.name)
    assert len(detail["equity"]["cum_net"]) == len(detail["exposure"]["equity"]) > 10
    assert detail["positions"]["count"] == 6 and len(detail["positions"]["rows"]) == 6
    assert {"symbol", "weight", "sector", "shares"} <= set(detail["positions"]["rows"][0])
    (family,) = api.families(settings.runs_dir)
    assert family["family"] == "tiny_family" and family["runs"] == 1
    (run_dir / "equity.parquet").unlink()  # older book runs have only daily.parquet
    again = api.run_detail(settings.runs_dir, run_dir.name)
    assert again["equity"] == detail["equity"] and again["fills"] == row["trades"]
