"""The Lab folder and whole runs, start to finish, on the in-memory store (decision 0023)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pandas as pd
import pytest

from kinn.lab import runner, store
from tests.lab_fake import standard

PERIOD = {
    "period": "custom",
    "start": "2015-01-02",
    "end": "2015-09-30",
    "universe": {"min_market_cap": 1e6},
}
GOOD = '''"""Buy after two up days."""

SETTINGS = {"exit": {"hold_days": 5}, "book": {"max_positions": 2}}


def signal(data):
    up = data.returns > 0
    return up & up.shift(1, fill_value=False)
'''


@pytest.fixture(scope="module")
def fake():
    return standard()


@pytest.fixture
def root(tmp_path):
    return tmp_path / "lab"


def go(root, fake, name="two_up", code=GOOD, settings=PERIOD):
    store.save_algorithm(root, name, code)
    run_dir = store.new_run(root, name, code, settings)
    runner.run(run_dir, open_store=lambda: fake)
    return run_dir


# -- the folder ---------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["", "Big", "a b", "../x", "-x", "x" * 65, "a.py"])
def test_bad_names_are_refused(name):
    with pytest.raises(store.LabError):
        store.check_name(name)


def test_save_read_and_delete_keeps_a_copy(root):
    store.save_algorithm(root, "mine", GOOD)
    assert store.read_algorithm(root, "mine") == GOOD
    assert store.algorithms(root)[0]["description"] == "Buy after two up days."
    store.delete_algorithm(root, "mine")
    assert store.algorithms(root) == []
    assert [p.read_text() for p in (root / "trash").iterdir()] == [GOOD]
    with pytest.raises(store.LabError):
        store.read_algorithm(root, "mine")


def test_code_too_long_is_refused(root):
    with pytest.raises(store.LabError, match="longer"):
        store.save_algorithm(root, "big", "#" * (store.MAX_CODE + 1))


def test_run_ids_are_checked(root):
    for bad in ("../../etc", "20260101T000000Z_x_zzzzzzzz", ""):
        with pytest.raises(store.LabError):
            store.run_dir_of(root, bad)


def test_two_runs_of_the_same_code_get_their_own_folders(root):
    a = store.new_run(root, "same", GOOD, {})
    b = store.new_run(root, "same", GOOD, {})
    assert a != b and a.name.endswith(b.name[-8:])
    assert store.run_dir_of(root, b.name) == b


def test_a_finished_run_stays_finished(root):
    run_dir = store.new_run(root, "x", GOOD, {})
    store.set_status(run_dir, "cancelled", stage="Cancelled")
    store.set_status(run_dir, "running", stage="Late progress note")
    assert store.status(run_dir)["state"] == "cancelled"


def test_a_run_whose_process_died_is_marked_interrupted(root):
    run_dir = store.new_run(root, "x", GOOD, {})
    store.set_status(run_dir, "running", stage="Loading")
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    (run_dir / "pid").write_text(str(child.pid))
    found = store.status(run_dir)
    assert found["state"] == "interrupted" and "ended without finishing" in found["error"]
    assert store.active_run(root) is None


def test_templates_are_listed_with_their_code():
    names = [t["name"] for t in store.templates()]
    assert {"big_prints", "momentum_rank", "rsi_reversal"} <= set(names)
    assert all(t["description"] and "def signal" in t["code"] for t in store.templates())


# -- whole runs ---------------------------------------------------------------------------
def test_a_run_writes_its_results(root, fake):
    run_dir = go(root, fake)
    state = store.status(run_dir)
    assert state["state"] == "complete", state.get("error")
    assert state["signals_computed"] and state["trial_number"] == 1
    summary = store.result(run_dir, "summary")
    assert summary["trades"] > 0 and summary["lookahead"]["passed"]
    assert summary["settings"]["exit"]["hold_days"] == 5  # from the algorithm's SETTINGS
    assert summary["taken"] + summary["skipped"] == summary["trades"]
    trades = pd.read_parquet(run_dir / "trades.parquet")
    assert len(trades) == summary["trades"]
    assert (trades["entry_date"] > trades["signal_date"]).all()
    assert (trades["entry_date"] >= pd.Timestamp("2015-01-05")).all()
    assert (trades["entry_date"] <= pd.Timestamp("2015-09-30")).all()
    stocks = store.result(run_dir, "by_stock")
    profits = [s["profit"] for s in stocks]
    assert profits == sorted(profits, reverse=True)
    assert sum(s["trades"] for s in stocks) == len(trades)
    assert sum(s["book_profit"] for s in stocks) == pytest.approx(summary["book_profit"], rel=1e-6)
    years = store.result(run_dir, "by_year")
    assert [y["year"] for y in years] == [2015]
    equity = store.result(run_dir, "equity")
    assert equity["profit"][-1] == pytest.approx(summary["book_profit"], abs=0.01)
    assert len(equity["dates"]) == len(equity["spy"])
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["data_build_id"] == "fake-build" and len(manifest["code_sha256"]) == 64
    assert (run_dir / "algorithm.py").read_text() == GOOD


def test_trials_count_runs_that_computed_signals(root, fake):
    go(root, fake)
    broken = go(root, fake, code="def signal(data)\n    return 1\n")
    third = go(root, fake)
    assert store.status(broken)["state"] == "failed"
    assert store.status(third)["trial_number"] == 2
    runs = store.list_runs(root, "two_up")
    assert [r["trial"] for r in runs] == [True, False, True]
    assert store.algorithms(root)[0]["trials"] == 2


def test_errors_in_the_code_fail_the_run_with_the_owners_line(root, fake):
    run_dir = go(root, fake, code="def signal(data):\n    return data.close.nope()\n")
    state = store.status(run_dir)
    assert state["state"] == "failed" and "your code, line 2" in state["error"]
    assert not state.get("signals_computed")


def test_a_bad_setting_fails_the_run_and_names_it(root, fake):
    run_dir = go(root, fake, settings={**PERIOD, "exit": {"hold_days": 0}})
    assert "exit.hold_days" in store.status(run_dir)["error"]


def test_a_universe_with_no_stocks_fails_plainly(root, fake):
    run_dir = go(root, fake, settings={**PERIOD, "universe": {"min_market_cap": 1e13}})
    assert store.status(run_dir)["error"].startswith("No stock is in this universe")


def test_a_peek_is_flagged_but_the_run_completes(root, fake):
    # Entry is the next open (the fake's open is its close); exit the 20th close after.
    code = (
        "def signal(data):\n"
        "    return data.adj_close.shift(-20) / data.adj_close.shift(-1) > 1.05\n"
    )
    run_dir = go(root, fake, code=code)
    summary = store.result(run_dir, "summary")
    assert store.status(run_dir)["state"] == "complete"
    assert not summary["lookahead"]["passed"]
    assert summary["mean_net"] > 0.005  # it knows tomorrow, so it looks good


def test_rank_mode_and_an_exit_signal(root, fake):
    code = (
        'SETTINGS = {"entry": {"mode": "rank", "top_n": 1}, "exit": {"hold_days": 10}}\n'
        "def signal(data):\n    return data.returns.rolling(20).sum()\n"
        "def exit_signal(data):\n    return data.returns < -0.01\n"
    )
    run_dir = go(root, fake, code=code)
    summary = store.result(run_dir, "summary")
    assert store.status(run_dir)["state"] == "complete", store.status(run_dir).get("error")
    assert summary["has_exit_signal"] and "exit signal" in summary["exits"]
    trades = pd.read_parquet(run_dir / "trades.parquet")
    assert trades.groupby("entry_date").size().max() == 1  # the best free stock each day
    assert summary["average_positions"] <= 10


@pytest.mark.parametrize("template", [t["name"] for t in store.templates()])
def test_every_template_runs(root, fake, template):
    code = next(t["code"] for t in store.templates() if t["name"] == template)
    run_dir = go(
        root,
        fake,
        name=template.replace("_", "-"),
        code=code,
        settings={**PERIOD, "universe": {"min_market_cap": 1e6, "max_market_cap": None}},
    )
    state = store.status(run_dir)
    assert state["state"] == "complete", state.get("error")
    assert store.result(run_dir, "lookahead")["passed"]


def test_the_worker_runs_as_its_own_process(root, tmp_path):
    """The real worker entry point: a bad algorithm fails without touching any data."""
    code = "def signal(data)\n"
    store.save_algorithm(root, "w", code)
    run_dir = store.new_run(root, "w", code, {})
    env = {**os.environ, "KINN_LAB_DIR": str(root)}
    done = subprocess.run(
        [sys.executable, "-m", "kinn.lab.worker", str(run_dir)],
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert done.returncode == 0, done.stderr
    assert store.status(run_dir)["error"].startswith("Syntax error at line 1")
