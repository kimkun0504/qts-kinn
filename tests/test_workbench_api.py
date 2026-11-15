"""The Workbench reads only the run store. Tested on real run folders from the engine."""

import json
import shutil
from pathlib import Path

import pytest

from apps.workbench import api
from kinn import run as runner
from kinn.core.settings import load_settings
from kinn.data import build
from tests import synthetic_raw as syn

REPO = Path(__file__).resolve().parents[1]
CONFIG = """
params: {{entries_per_session: 8, hold_minutes: {hold}, seed: 2, min_sessions_prior: 5}}
risk: {{equity: 10000, position_dollars: 500, buying_power: 10000}}
period: {{start: 2023-09-25, end: 2023-11-08}}
lookahead_check_rate: 0.0
"""


@pytest.fixture(scope="module")
def runs_dir(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("bench")
    raw = syn.make_random_walk_raw(tmp / "raw", symbols=10, days=33)
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
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("KINN_STRATEGIES_DIR", str(strategies))
        for k, hold in enumerate((30, 60, 90)):
            (strategies / "random_entry" / "configs" / f"h{hold}.yaml").write_text(
                CONFIG.format(hold=hold)
            )
            run_dir = runner.start_run(
                "random_entry", f"h{hold}", settings=settings, scratch=True, agent=f"a{k}"
            )
            assert runner.continue_run(run_dir, settings=settings)
            manifest = json.loads((run_dir / "manifest.json").read_text())
            manifest["scratch"] = k == 0  # one scratch run, two counted
            (run_dir / "manifest.json").write_text(json.dumps(manifest))
        study = runner.start_run(
            "random_entry", "h30", settings=settings, scratch=True, agent="s", kind="event_study"
        )
        assert runner.continue_run(study, settings=settings)
    return settings.runs_dir


def test_run_list_has_headline_numbers_and_parameters(runs_dir):
    rows = api.list_runs(runs_dir)
    assert len(rows) == 4 and {r["kind"] for r in rows} == {"backtest", "event_study"}
    backtests = [r for r in rows if r["kind"] == "backtest"]
    assert all(r["net_1x"] < 0 and r["trades"] > 0 and r["schema_ok"] for r in backtests)
    assert {r["params"]["params.hold_minutes"] for r in backtests} == {30, 60, 90}


def test_run_detail_serves_a_tearsheet_or_a_study(runs_dir):
    rows = api.list_runs(runs_dir)
    backtest = api.run_detail(runs_dir, next(r["run_id"] for r in rows if r["kind"] == "backtest"))
    assert backtest["metrics"]["trades"] > 0 and len(backtest["equity"]["date"]) > 5
    assert sum(backtest["histogram"]["counts"]) == backtest["metrics"]["trades"]
    assert "sessions" not in backtest["manifest"]
    study = api.run_detail(runs_dir, next(r["run_id"] for r in rows if r["kind"] == "event_study"))
    assert study["study"]["curve"]["r_close"]["net_1x"]["mean"] < 0
    assert api.run_detail(runs_dir, "../etc") is None and api.run_detail(runs_dir, "nope") is None


def test_families_count_trials_and_score_overfitting(runs_dir):
    (family,) = api.families(runs_dir)
    assert family["family"] == "canary_random_entry"
    assert family["counted"] == 2 and family["scratch"] == 2 and family["trials"] == 2
    assert family["by_agent"] == {"a1": 1, "a2": 1}
    over = family["overfitting"]
    assert over["backtests"] == 2 and over["best_sharpe_annual"] < 0
    assert over["deflated_sharpe"] < 0.05 and 0 <= over["pbo"]["pbo"] <= 1
