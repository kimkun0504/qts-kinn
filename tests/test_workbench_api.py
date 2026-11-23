"""The Workbench reads only the run store. Tested on real run folders from the engine."""

import json
import shutil
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
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


def test_runs_carry_their_period_and_targets_only_out_of_sample(runs_dir, tmp_path):
    rows = api.list_runs(runs_dir)
    # The synthetic world sits inside the validation years, so its backtests are judged.
    backtests = [r for r in rows if r["kind"] == "backtest"]
    assert backtests and all(r["phase"] == "validation" for r in rows)
    for row in backtests:
        judged = row["targets"]
        assert judged["of"] == 4 and judged["fills"] == "not checked" and not judged["all_met"]
        assert [i["key"] for i in judged["items"]] == ["net_per_trade", "sharpe", "drawdown"]
        assert judged["met"] == sum(i["met"] for i in judged["items"])
    assert all(r["targets"] is None for r in rows if r["kind"] != "backtest")
    detail = api.run_detail(runs_dir, backtests[0]["run_id"])
    assert detail["phase"] == "validation" and detail["targets"] == backtests[0]["targets"]


def test_targets_and_periods_follow_decision_0017():
    from datetime import date

    from kinn.validation import targets

    assert targets.phase(date(2003, 9, 10), date(2016, 12, 30)) == "development"
    assert targets.phase(date(2017, 1, 3), date(2023, 11, 8)) == "validation"
    assert targets.phase(date(2003, 9, 10), date(2023, 11, 8)) == "full"
    assert targets.phase(date(2023, 11, 9), date(2026, 11, 6)) == "holdout"
    assert targets.phase(date(2017, 1, 3), date(2026, 11, 6)) == "full"

    def metrics(net, sharpe, drawdown):
        side = {"mean_return": net, "sharpe": sharpe, "max_drawdown": drawdown}
        return {"slippage_2x": side, "equity": 20_000.0}

    assert [i["met"] for i in targets.check(metrics(0.0156, 1.37, -4485.0))] == [True, True, True]
    assert [i["met"] for i in targets.check(metrics(0.0122, 0.94, -4913.0))] == [True, False, True]
    assert [i["met"] for i in targets.check(metrics(0.0099, 1.0, -10_000.0))] == [False] * 3


def test_a_passed_fill_check_confirms_the_fills_of_the_runs_it_covers(runs_dir, tmp_path):
    store = tmp_path / "runs"
    shutil.copytree(runs_dir, store)
    rows = [r for r in api.list_runs(store) if r["kind"] == "backtest" and not r["scratch"]]
    covered, other = rows[0]["run_id"], rows[1]["run_id"]
    check = store / "20990101T000000Z_t_random_entry_fillcheck"
    check.mkdir()
    manifest = json.loads((store / covered / "manifest.json").read_text())
    manifest.update(
        run_id=check.name, kind="fill_check", config="fill_check:plan", scratch=False,
        resolved_config={"plan": "plan", "source_runs": {covered: "validation"}},
    )  # fmt: skip
    (check / "manifest.json").write_text(json.dumps(manifest))
    result = {"verdict": {"passed": True, "validation_net_per_trade_2x": 0.012},
              "all_traded": {"orders": 77}, "periods": {}}  # fmt: skip
    (check / "fill_check.json").write_text(json.dumps(result))
    by_id = {r["run_id"]: r for r in api.list_runs(store)}
    assert by_id[covered]["targets"]["fills"] == "confirmed"
    assert by_id[covered]["targets"]["fills_run"] == check.name
    assert by_id[other]["targets"]["fills"] == "not checked"
    listed = by_id[check.name]
    assert (listed["kind"], listed["fill_check_passed"], listed["trades"]) == (
        "fill_check",
        True,
        77,
    )
    assert api.run_detail(store, check.name)["fill_check"]["verdict"]["passed"] is True


def test_strategies_report_status_candidate_and_readiness(runs_dir, tmp_path):
    folder = tmp_path / "strategies"
    rows = [r for r in api.list_runs(runs_dir) if r["kind"] == "backtest" and not r["scratch"]]
    config = rows[0]["config"]
    (folder / "random_entry").mkdir(parents=True)
    (folder / "random_entry" / "strategy.yaml").write_text(
        f"name: random_entry\nstatus: developing\nowner: claude\ncandidate: {config}\n"
    )
    (folder / "idle").mkdir()
    (folder / "idle" / "strategy.yaml").write_text("name: idle\nstatus: parked\nowner: gpt\n")
    (folder / "_template").mkdir()
    (folder / "_template" / "strategy.yaml").write_text("name: template\n")
    found = {s["strategy"]: s for s in api.strategies(runs_dir, folder)}
    assert set(found) == {"random_entry", "idle"}
    first = found["random_entry"]
    assert first["state"] == "candidate" and first["candidate_run"]["config"] == config
    assert first["ready_for_paper"] is False  # random entries meet no target, fills unchecked
    assert found["idle"]["state"] == "parked" and found["idle"]["candidate_run"] is None
    assert [s["strategy"] for s in api.strategies(runs_dir, folder)][0] == "random_entry"


def _equity(runs, run_id, days, net):
    folder = runs / run_id
    folder.mkdir(parents=True)
    pq.write_table(pa.table({"date": days, "net": net}), folder / "equity.parquet")


def test_compare_puts_runs_on_one_calendar_and_measures_them_together(tmp_path):
    days = [f"2020-{m:02d}-{d:02d}" for m in range(1, 7) for d in range(1, 21)]
    rng = np.random.default_rng(3)
    a = rng.normal(10, 50, len(days))
    _equity(tmp_path, "a", days, a.tolist())
    _equity(tmp_path, "b", days, (-a).tolist())
    _equity(tmp_path, "late", days[60:], rng.normal(0, 50, len(days) - 60).tolist())

    out = api.compare(tmp_path, ["a", "b", "../a", "missing", ""])
    assert [r["run_id"] for r in out["runs"]] == ["a", "b"]
    assert out["overlap"]["correlation"][0][1] == pytest.approx(-1.0)
    assert out["overlap"]["together"]["total"] == pytest.approx(0.0, abs=1e-6)
    assert out["overlap"]["alone"][0]["total"] == pytest.approx(a.sum())
    assert out["together"][-1] == pytest.approx(0.0, abs=0.01)

    out = api.compare(tmp_path, ["a", "late"])
    assert out["overlap"]["start"] == days[60] and out["overlap"]["sessions"] == len(days) - 60
    assert len(out["curves"][1]) == len(out["dates"]) == len(days)
    assert out["curves"][1][59] == 0.0
    assert api.compare(tmp_path, ["a"])["overlap"] is None


def _lab_run(lab, run_id, days, pnl, *, daily=True):
    folder = lab / "runs" / run_id
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text(json.dumps({"algorithm": "two_up", "run_id": run_id}))
    (folder / "summary.json").write_text(json.dumps({"period_label": "2020"}))
    if daily:
        pq.write_table(pa.table({"date": days, "pnl": pnl}), folder / "book.parquet")
    else:
        cum = np.cumsum(pnl)[::2].tolist()
        (folder / "equity.json").write_text(json.dumps({"dates": days[::2], "profit": cum}))


def test_compare_puts_lab_runs_beside_backtests(tmp_path):
    days = [f"2020-{m:02d}-{d:02d}" for m in range(1, 7) for d in range(1, 21)]
    rng = np.random.default_rng(5)
    a = rng.normal(10, 50, len(days))
    _equity(tmp_path / "runs", "a", days, a.tolist())
    lab = tmp_path / "lab"
    full = "20260101T000000Z_two_up_0123abcd"
    drawn = "20260102T000000Z_two_up_89abcdef"
    _lab_run(lab, full, days, (2 * a).tolist())
    _lab_run(lab, drawn, days, a.tolist(), daily=False)

    out = api.compare(tmp_path / "runs", ["a", f"lab:{full}", f"lab:{drawn}", "lab:../x"], lab)
    assert [r["run_id"] for r in out["runs"]] == ["a", f"lab:{full}", f"lab:{drawn}"]
    assert out["runs"][0]["lab"] is None
    assert out["runs"][1]["lab"] == {"algorithm": "two_up", "period": "2020", "daily": True}
    assert out["runs"][2]["lab"]["daily"] is False
    assert out["overlap"]["correlation"][0][1] == pytest.approx(1.0)
    alone = out["overlap"]["alone"]
    assert alone[1]["total"] == pytest.approx(2 * alone[0]["total"])
    assert out["overlap"]["end"] == days[-2]
    assert out["curves"][2][-1] == pytest.approx(np.cumsum(a)[::2][-1], abs=0.01)
    assert api.compare(tmp_path / "runs", [f"lab:{full}"])["runs"] == []
