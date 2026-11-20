"""The Lab folder and whole runs, start to finish, on the in-memory store (decision 0023)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import pandas as pd
import pytest

from apps.workbench import lab as lab_api
from apps.workbench import screen_lab
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


def go(root, fake, name="two_up", code=GOOD, settings=PERIOD, sweep=None):
    store.save_algorithm(root, name, code)
    run_dir = store.new_run(root, name, code, settings, sweep)
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
    assert len(equity["dates"]) == len(equity["spy"]) == len(equity["spy_matched"])
    assert equity["spy_matched"][0] == 0.0
    assert len(equity["rolling_sharpe"]) == len(equity["dates"])
    luck = store.result(run_dir, "luck")
    assert luck is None or 0 <= luck["same_days"]["beaten"] <= 1
    assert equity["rolling_sharpe"][0] is None
    summary = store.result(run_dir, "summary")
    assert summary["beta_spy"] is None or -5 < summary["beta_spy"] < 5
    assert summary["correlation_spy"] is None or -1 <= summary["correlation_spy"] <= 1
    path = store.result(run_dir, "path")
    assert path["horizons"][0] == -20 and path["horizons"][-1] >= 40 and path["hold"] == 5
    zero = path["horizons"].index(0)
    assert path["stock"][zero] == 0.0 and path["excess"][zero] == 0.0
    assert path["trades"] == path["of"] == summary["trades"]
    assert all(lo <= hi for lo, hi in zip(path["low"], path["high"], strict=True)
               if lo is not None and hi is not None)  # fmt: skip
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


def test_a_short_run_finishes_with_the_book_and_spy_turned_round(root, fake):
    short = go(root, fake, settings={**PERIOD, "entry": {"side": "short"}})
    long = go(root, fake, settings=PERIOD)
    for run_dir in (short, long):
        assert store.status(run_dir)["state"] == "complete", store.status(run_dir).get("error")
    assert store.result(short, "summary")["settings"]["entry"]["side"] == "short"
    s, g = (pd.read_parquet(r / "trades.parquet") for r in (short, long))
    assert len(s) == len(g)
    assert s["gross"].to_numpy() == pytest.approx(-g["gross"].to_numpy(), rel=1e-6, abs=1e-9)
    s_spy, g_spy = (store.result(r, "equity")["spy_matched"] for r in (short, long))
    assert [x for x in s_spy if x] == pytest.approx([-x for x in g_spy if x], rel=1e-6)


def test_a_universe_of_named_tickers_trades_only_them(root, fake):
    run_dir = go(root, fake, settings={**PERIOD, "universe": {"tickers": "upp, dwn, zzzz"}})
    state = store.status(run_dir)
    assert state["state"] == "complete", state.get("error")
    summary = store.result(run_dir, "summary")
    assert summary["settings"]["universe"]["tickers"] == ["DWN", "UPP", "ZZZZ"]
    assert summary["tickers_not_found"] == ["ZZZZ"]
    traded = set(pd.read_parquet(run_dir / "trades.parquet")["ticker"])
    assert traded and traded <= {"UPP", "DWN"}
    missing = go(root, fake, settings={**PERIOD, "universe": {"tickers": ["ZZZZ"]}})
    assert store.status(missing)["error"].startswith("None of these tickers is in the universe")
    bad = go(root, fake, settings={**PERIOD, "universe": {"tickers": ["no way"]}})
    assert "universe.tickers" in store.status(bad)["error"]


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
    assert store.result(run_dir, "factor") is None or store.result(run_dir, "factor")["hold"] == 10
    trades = pd.read_parquet(run_dir / "trades.parquet")
    assert trades.groupby("entry_date").size().max() == 1  # the best free stock each day
    assert summary["average_positions"] <= 10


def test_both_sides_buy_one_end_and_short_the_other(root, fake):
    code = (
        'SETTINGS = {"entry": {"mode": "rank", "top_n": 1, "side": "both"}, '
        '"exit": {"hold_days": 5}, "book": {"max_positions": 3}}\n'
        "def signal(data):\n    return data.returns.rolling(20).sum()\n"
    )
    run_dir = go(root, fake, code=code)
    assert store.status(run_dir)["state"] == "complete", store.status(run_dir).get("error")
    trades = pd.read_parquet(run_dir / "trades.parquet")
    assert set(trades["side"]) == {"long", "short"}
    summary = store.result(run_dir, "summary")
    assert summary["capital"] == 2 * 3 * summary["settings"]["book"]["position_size"]
    assert "long and short trades" in summary["headline"]
    equity = store.result(run_dir, "equity")
    assert (
        max(equity["shorts"]) <= 3
        and max(p - s for p, s in zip(equity["positions"], equity["shorts"], strict=True)) <= 3
    )


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


# -- helper modules, the time limit, the cache and the command line -------------------------
HELPER = '''"""Shared."""


def up_days(data, n):
    up = data.returns > 0
    out = up
    for k in range(1, n):
        out = out & up.shift(k, fill_value=False)
    return out
'''
USES_HELPER = '''"""Uses the library."""
from lab.helpers import up_days


def signal(data):
    return up_days(data, 2)
'''


def test_a_helper_module_is_imported_and_kept_with_the_run(root, fake):
    store.save_module(root, "helpers", HELPER)
    run_dir = go(root, fake, name="helped", code=USES_HELPER)
    assert store.status(run_dir)["state"] == "complete", store.status(run_dir).get("error")
    assert (run_dir / "pkg" / "lab" / "helpers.py").read_text() == HELPER
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert set(manifest["library"]) == {"helpers"}
    # Changing the library later changes neither the old run's copy nor its hash.
    store.save_module(root, "helpers", HELPER.replace("n):", "n, extra=0):"))
    assert (run_dir / "pkg" / "lab" / "helpers.py").read_text() == HELPER
    again = store.new_run(root, "helped", USES_HELPER, PERIOD)
    assert again.name.split("_")[-1] != run_dir.name.split("_")[-1]


def test_an_error_in_a_helper_names_the_helper_line(root, fake):
    store.save_module(root, "helpers", "def up_days(data, n):\n    return data.nope\n")
    run_dir = go(root, fake, name="helped", code=USES_HELPER)
    error = store.status(run_dir)["error"]
    assert "lab/helpers.py, line 2" in error and "your code, line 6" in error


def test_a_missing_helper_fails_plainly(root, fake):
    run_dir = go(root, fake, name="helped", code=USES_HELPER)
    assert "No module named 'lab.helpers'" in store.status(run_dir)["error"]


def test_module_names_must_be_importable(root):
    for bad in ("Helpers", "2x", "my-tools", "class", ""):
        with pytest.raises(store.LabError):
            store.save_module(root, bad, HELPER)
    with pytest.raises(store.LabError):
        store.check_name("library")


def test_a_run_past_its_time_limit_stops(root, fake):
    code = "import time\n\ndef signal(data):\n    time.sleep(5)\n    return data.close > 0\n"
    store.save_algorithm(root, "slow", code)
    run_dir = store.new_run(root, "slow", code, PERIOD)
    started = time.time()
    runner.run(run_dir, open_store=lambda: fake, time_limit=0.5)
    state = store.status(run_dir)
    assert state["state"] == "failed" and "time limit" in state["error"]
    assert time.time() - started < 4


def test_the_owners_except_cannot_swallow_the_time_limit(root, fake):
    code = ("import time\n\ndef signal(data):\n    try:\n        time.sleep(5)\n"
            "    except Exception:\n        pass\n    return data.close > 0\n")  # fmt: skip
    store.save_algorithm(root, "stubborn", code)
    run_dir = store.new_run(root, "stubborn", code, PERIOD)
    runner.run(run_dir, open_store=lambda: fake, time_limit=0.5)
    assert "time limit" in store.status(run_dir)["error"]


def test_a_second_run_reads_the_cache_and_gets_the_same_result(root, fake):
    first = go(root, fake)
    second = go(root, fake)
    a, b = store.result(first, "summary"), store.result(second, "summary")
    assert (a["cache"], b["cache"]) == ("miss", "hit")
    for key in ("trades", "mean_net", "book_profit", "signals"):
        assert a[key] == b[key]
    assert pd.read_parquet(first / "trades.parquet").equals(
        pd.read_parquet(second / "trades.parquet")
    )
    assert "Loading prices" in a["timings"] and "Loading prices" not in b["timings"]
    log = (second / "log.txt").read_text()
    assert "Prices loaded from the cache" in log


def test_a_damaged_cache_entry_is_read_again(root, fake):
    go(root, fake)
    entry = next(p for p in (root / "cache").iterdir() if p.is_dir())
    (entry / "close.npy").write_bytes(b"not an array")
    run_dir = go(root, fake)
    assert store.status(run_dir)["state"] == "complete"
    assert store.result(run_dir, "summary")["cache"] == "miss"


def test_the_cache_keeps_to_its_limit(root, fake, monkeypatch):
    monkeypatch.setenv("KINN_LAB_CACHE_GB", "0")
    go(root, fake)
    go(root, fake, settings={**PERIOD, "end": "2015-06-30"})
    entries = [p for p in (root / "cache").iterdir() if p.is_dir() and not p.name.startswith(".")]
    assert len(entries) == 1  # the newest stays; the older one went


def test_the_command_line_runs_lists_and_refuses(root, fake, tmp_path, capsys):
    from functools import partial

    from kinn.lab import commands

    script = tmp_path / "Two Up.py"
    script.write_text(GOOD)
    lines = []
    run = partial(runner.run, open_store=lambda: fake)
    assert commands.run_algorithm(root, str(script), PERIOD, time_limit=60, out=lines.append,
                                  runner=run) == 0  # fmt: skip
    assert lines[0].startswith("run ") and "trades" in lines[1] and "best:" in lines[3]
    assert store.read_algorithm(root, "two_up") == GOOD
    lines.clear()
    assert commands.run_algorithm(root, "two_up", {"exit": {"hold_days": 0}}, time_limit=60,
                                  out=lines.append, runner=run) == 2  # fmt: skip
    assert "exit.hold_days" in lines[0]
    lines.clear()
    store.save_algorithm(root, "broken", "def signal(data)\n")
    assert commands.run_algorithm(root, "broken", {}, time_limit=60, out=lines.append,
                                  runner=run) == 2  # fmt: skip
    assert "line 1" in lines[0]
    assert commands.list_algorithms(root) == 0
    assert "two_up" in capsys.readouterr().out


def test_the_selfcheck_passes_on_good_templates(fake):
    from functools import partial

    from kinn.lab import commands

    lines = []
    small = {**PERIOD, "universe": {"min_market_cap": 1e6, "max_market_cap": None}}
    run = partial(runner.run, open_store=lambda: fake)
    code = commands.selfcheck(out=lines.append, runner=run, period=small)
    assert code == 0, lines
    assert lines[-1] == "self-check passed"
    assert any("caught a deliberate peek" in line for line in lines)


def test_every_save_keeps_the_version_before_it(root):
    store.save_algorithm(root, "kept", "one\n")
    store.save_algorithm(root, "kept", "one\n")  # unchanged: nothing to keep
    store.save_algorithm(root, "kept", "two\n")
    store.save_algorithm(root, "kept", "three\n")
    versions = store.history(root, "kept")
    assert [v["first_line"] for v in versions] == ["two", "one"]
    assert store.read_version(root, "kept", versions[-1]["version"]) == "one\n"
    with pytest.raises(store.LabError):
        store.read_version(root, "kept", "../../algorithms/kept")
    store.save_module(root, "tools", "a = 1\n")
    store.save_module(root, "tools", "a = 2\n")
    assert [v["first_line"] for v in store.module_history(root, "tools")] == ["a = 1"]


def test_history_keeps_a_bounded_number_of_versions(root, monkeypatch):
    monkeypatch.setattr(store, "KEEP_VERSIONS", 3)
    for k in range(6):
        store.save_algorithm(root, "many", f"v{k}\n")
    assert [v["first_line"] for v in store.history(root, "many")] == ["v4", "v3", "v2"]


def test_a_sweep_tries_each_value_on_the_same_signals_and_counts_each_as_a_trial(root, fake):
    code = "def signal(data):\n    return data.returns > 0.02\n"
    run_dir = go(root, fake, code=code, sweep={"field": "exit.hold_days", "values": [3, 5, 10]})
    state = store.status(run_dir)
    assert state["state"] == "complete", state.get("error")
    assert state["trials"] == 4 and state["trial_number"] == 1
    sweep = store.result(run_dir, "sweep")
    assert sweep["field"] == "exit.hold_days" and [r["value"] for r in sweep["rows"]] == [3, 5, 10]
    assert all(r["trades"] for r in sweep["rows"])
    summary = store.result(run_dir, "summary")
    assert summary["sweep"] == {"field": "exit.hold_days", "values": 3} and summary["trials"] == 4
    again = go(root, fake, code=code, sweep={"field": "exit.hold_days", "values": [20, 30]})
    assert store.status(again)["trial_number"] == 5 and store.status(again)["trials"] == 2
    assert store.algorithms(root)[0]["trials"] == 6


@pytest.mark.parametrize(
    "sweep",
    [
        {"field": "universe.min_price", "values": [1, 2]},
        {"field": "exit.hold_days", "values": [5]},
        {"field": "exit.hold_days", "values": [5, 5]},
        {"field": "exit.hold_days", "values": [5, "x"]},
        {"field": "exit.hold_days", "values": [5, 0]},
    ],
)
def test_bad_sweeps_are_refused(sweep):
    from kinn.lab.settings import SettingsError, sweep_settings

    with pytest.raises(SettingsError):
        sweep_settings({}, {}, sweep)


def test_the_command_line_reads_a_sweep():
    from kinn.lab.commands import sweep_from

    hold = sweep_from("exit.hold_days=5, 10,20")
    assert hold == {"field": "exit.hold_days", "values": [5, 10, 20]}
    assert sweep_from("exit.stop_loss=none,0.05") == {"field": "exit.stop_loss",
                                                       "values": [None, 0.05]}  # fmt: skip
    assert sweep_from(None) is None


def test_a_screen_becomes_an_algorithm_that_runs(root, fake):
    query = "sector=Technology&f=market_cap:1M:&f=ret_1m:-50:&f=ps:0:100000&f=close:1:"
    code = screen_lab.algorithm(query, "Cheap tech")
    assert 'passes &= data.sector == "Technology"' in code and "(ps <= 100000)" in code
    run_dir = go(root, fake, name="screen_cheap_tech", code=code)
    assert store.status(run_dir)["state"] == "complete", store.status(run_dir).get("error")
    summary = store.result(run_dir, "summary")
    assert summary["trades"] > 0 and summary["lookahead"]["passed"]

    status, payload = lab_api.route(
        "POST", ["from-screen"], {}, {"query": query, "title": "Cheap tech"}, root
    )
    assert status == 201 and payload["name"] == "screen_cheap_tech_2"
    assert store.read_algorithm(root, payload["name"]) == code
    status, payload = lab_api.route(
        "POST", ["from-screen"], {}, {"query": "q=apple", "title": "x"}, root
    )
    assert status == 400 and "no filter" in payload["error"]
    with pytest.raises(screen_lab.ScreenError, match="not a number"):
        screen_lab.algorithm("f=pe:cheap:", "x")
