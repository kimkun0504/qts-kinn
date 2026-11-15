"""Canaries 2 and 3, through the real entry point on random-walk data.

2. Random entries must lose money after costs.
3. Identical configurations must give identical results.
Plus: the run entry point refuses lookahead and uncommitted code.
"""

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest

from kinn import run as runner
from kinn.core.settings import load_settings
from kinn.data import build
from kinn.features.base import LookaheadError
from kinn.registry import runs as registry
from tests import synthetic_raw as syn

REPO = Path(__file__).resolve().parents[2]
CONFIG = """
params: {entries_per_session: 10, hold_minutes: 60, seed: 5, min_sessions_prior: 5}
risk: {equity: 10000, position_dollars: 500, buying_power: 10000}
period: {start: 2023-09-25, end: 2023-11-08}
lookahead_check_rate: 1.0
seed: 5
"""
CHEAT = """
import numpy as np
from kinn.core.types import Signal
from kinn.data.universe import Universe


class BuyTheLow:
    name, features = "cheat", ()
    universe = Universe("cheat", min_sessions_prior=5)

    def signals(self, view, features):
        return [Signal(s, int(sd.minute[np.argmin(sd.low)])) for s, sd in view.symbols.items()
                if len(sd.minute)]


def build(params):
    return BuyTheLow()
"""


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("walk")
    raw = syn.make_random_walk_raw(tmp / "raw")
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
    (strategies / "random_entry" / "configs" / "test.yaml").write_text(CONFIG)
    (strategies / "cheat" / "configs").mkdir(parents=True)
    (strategies / "cheat" / "strategy.py").write_text(CHEAT)
    (strategies / "cheat" / "strategy.yaml").write_text(
        "name: cheat\ncost_calibration: ibkr_pro_tiered\nfamily: canary_cheat\n"
    )
    (strategies / "cheat" / "configs" / "test.yaml").write_text(CONFIG)
    return settings, strategies


def _run(world, monkeypatch, strategy="random_entry", agent="claude", workers=1):
    settings, strategies = world
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(strategies))
    run_dir = runner.start_run(strategy, "test", settings=settings, scratch=True, agent=agent)
    assert runner.continue_run(run_dir, settings=settings, workers=workers)
    return run_dir


@pytest.fixture(scope="module")
def first_run(world):
    with pytest.MonkeyPatch.context() as patch:
        return _run(world, patch)


def test_canary_random_entries_lose_money_after_costs(first_run):
    metrics = json.loads((first_run / "metrics.json").read_text())
    trades = pq.read_table(first_run / "trades.parquet").to_pydict()
    net = np.array(trades["net"]) / np.array(trades["notional"])
    assert metrics["trades"] >= 200
    assert abs(metrics["gross_mean_return"]) < 0.001  # no edge before costs
    upper = net.mean() + 3 * net.std(ddof=1) / np.sqrt(len(net))
    assert upper < 0, "random entries did not lose after costs: the engine or costs are wrong"
    assert metrics["slippage_2x"]["mean_return"] < metrics["slippage_1x"]["mean_return"] < 0
    assert metrics["counts"]["lookahead_checks"] > 0


def test_canary_identical_configurations_give_identical_results(world, first_run, monkeypatch):
    second = _run(world, monkeypatch, agent="gpt", workers=2)  # other agent, parallel months
    assert second.name != first_run.name
    a, b = (pq.read_table(d / "trades.parquet") for d in (first_run, second))
    assert a.num_rows > 0 and a.equals(b)
    one, two = (json.loads((d / "manifest.json").read_text()) for d in (first_run, second))
    assert one["data_build_id"] == two["data_build_id"]


def test_the_run_writes_every_output_in_a_versioned_schema(first_run):
    for name in (
        "manifest.json",
        "metrics.json",
        "trades.parquet",
        "equity.parquet",
        "tearsheet.html",
        "tearsheet.md",
    ):
        assert (first_run / name).exists(), name
    manifest = json.loads((first_run / "manifest.json").read_text())
    assert manifest["status"] == "complete" and manifest["schemas"]["trades"] == "trades-1"
    assert {"commit", "branch", "dirty"} <= set(manifest["git"])
    assert first_run.name.split("_")[1:3] == ["claude", "random"]
    page = (first_run / "tearsheet.html").read_text()
    assert "2× slippage" in page and "SCRATCH" in page


def test_the_entry_point_refuses_a_strategy_that_looks_ahead(world, monkeypatch):
    with pytest.raises(LookaheadError):
        _run(world, monkeypatch, strategy="cheat")


def test_a_paused_run_resumes_and_matches(world, first_run, monkeypatch):
    settings, strategies = world
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(strategies))
    run_dir = runner.start_run(
        "random_entry", "test", settings=settings, scratch=True, agent="resume"
    )
    assert not runner.continue_run(run_dir, settings=settings, budget_seconds=-1)
    assert not (run_dir / "trades.parquet").exists()
    assert runner.continue_run(run_dir, settings=settings)
    assert pq.read_table(run_dir / "trades.parquet").equals(
        pq.read_table(first_run / "trades.parquet")
    )


def test_registry_counts_trials_and_skips_scratch_runs(world, first_run):
    settings, _ = world
    index = registry.rebuild_index(settings.runs_dir)
    assert index.exists()
    assert registry.trial_count(settings.runs_dir, "canary_random_entry") == 0  # all scratch
    assert registry.trial_count(settings.runs_dir, "canary_random_entry", prior_trials=6) == 6
    manifest = json.loads((first_run / "manifest.json").read_text())
    manifest.update(scratch=False, run_id="counted")
    (settings.runs_dir / "counted").mkdir()
    registry.write_json(settings.runs_dir / "counted" / "manifest.json", manifest)
    assert registry.trial_count(settings.runs_dir, "canary_random_entry") == 1


def test_uncommitted_code_is_refused_unless_scratch(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    (tmp_path / "a.txt").write_text("1")
    git("add", "-A")
    git("commit", "-qm", "one")
    registry.check_clean(registry.git_state(tmp_path), scratch=False)
    (tmp_path / "a.txt").write_text("2")
    state = registry.git_state(tmp_path)
    assert state["dirty"]
    with pytest.raises(registry.DirtyTreeError):
        registry.check_clean(state, scratch=False)
    registry.check_clean(state, scratch=True)


def test_event_study_measures_forward_returns_from_the_next_bar(world, monkeypatch):
    settings, strategies = world
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(strategies))
    run_dir = runner.start_run(
        "random_entry", "test", settings=settings, scratch=True, agent="study", kind="event_study"
    )
    assert runner.continue_run(run_dir, settings=settings)
    study = json.loads((run_dir / "study.json").read_text())
    events = pq.read_table(run_dir / "events.parquet").to_pylist()
    assert study["events"] == len(events) >= 200
    first = events[0]
    assert first["entry_minute"] == first["signal_minute"] + 1  # a bar every minute here
    # No edge in a random walk: gross about zero, net negative, 2x worse than 1x.
    close = study["curve"]["r_close"]
    assert abs(close["gross"]["mean"]) < 0.002
    assert close["net_2x"]["mean"] < close["net_1x"]["mean"] < 0
    assert close["net_1x"]["low"] < close["net_1x"]["mean"] < close["net_1x"]["high"]
    assert (run_dir / "study.html").exists() and "By liquidity" in (
        run_dir / "study.md"
    ).read_text()
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["kind"] == "event_study"
