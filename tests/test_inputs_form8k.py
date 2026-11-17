"""The form8k input: 8-K items typed for the intraday engine, visible from the session after
the filing date, with its version in the run manifest."""

from __future__ import annotations

import json
from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import CurrentReport
from kinn.data import inputs
from kinn.data.seal import HoldoutError
from kinn.data.store import DataStore
from kinn.data.universe import Universe
from kinn.engine.intraday.data import load_day

UNIVERSE = Universe("everything", min_sessions_prior=1)
FILED = date(2023, 10, 10)  # the synthetic build's one 8-K: AAA, items 2.02 and 9.01


def test_a_filing_is_visible_from_the_session_after_its_filing_date(built):
    store = DataStore(built)

    def seen(day, sessions=1):
        table = store.form8k(date.fromisoformat(day), sessions=sessions)
        assert all(filed < date.fromisoformat(day) for filed in table["filed"].to_pylist())
        return table.to_pylist()

    assert seen("2023-10-09") == [] and seen("2023-10-10") == []  # filed that day: not yet
    (row,) = seen("2023-10-11")
    assert row["filed"] == FILED and row["eventcodes"] == "22|91"
    assert seen("2023-10-12") == []
    assert len(seen("2023-10-12", sessions=2)) == 1
    assert len(seen("2023-10-17", sessions=5)) == 1 and seen("2023-10-18", sessions=5) == []


def test_the_view_types_the_items_and_marks_earnings(built):
    store = DataStore(built)
    view = load_day(store, date(2023, 10, 11), UNIVERSE, form8k_sessions=1).view
    (symbol,) = view.reports
    (report,) = view.reports[symbol]
    assert report == CurrentReport(
        symbol, view.symbols[symbol].permaticker, FILED, (22, 91), ("2.02", "9.01"), True
    )
    assert view.upto(600).reports == view.reports  # known before the open
    # The day of the filing itself, replayed: nothing, however late the replay happens.
    assert load_day(store, FILED, UNIVERSE, form8k_sessions=5).view.reports == {}
    assert load_day(store, date(2023, 10, 11), UNIVERSE).view.reports == {}  # not asked for


def test_the_seal_holds(build_synthetic):
    store = DataStore(build_synthetic("with_later_filing", with_holdout=True))
    info = store.form8k_info()
    assert info["last_filed"] == FILED.isoformat() and info["rows"] == 1  # 2024's is not counted
    with pytest.raises(HoldoutError):
        store.form8k(date(2024, 2, 5))


def test_codes_that_are_not_8k_items_pass_through_without_an_item():
    assert inputs.item(22) == "2.02" and inputs.item(57) == "5.07"
    assert 22 in inputs.FORM8K_ITEMS and 34 not in inputs.FORM8K_ITEMS


STRATEGY = """
from kinn.core.types import Signal
from kinn.data.universe import Universe


class AfterEarnings:
    name = "after_earnings"
    features = ()
    inputs = {"form8k": {"sessions": 1}}
    universe = Universe("everything", min_sessions_prior=1)

    def signals(self, view, features):
        out = []
        for symbol, reports in view.reports.items():
            sd = view.symbols[symbol]
            if len(sd.minute) and any(r.earnings for r in reports):
                out.append(Signal(symbol, int(sd.minute[0]), max_hold_minutes=30))
        return out


def build(params):
    return AfterEarnings()
"""


def test_a_run_records_the_input_version(built, tmp_path, monkeypatch):
    folder = tmp_path / "strategies" / "after_earnings"
    (folder / "configs").mkdir(parents=True)
    (folder / "strategy.py").write_text(STRATEGY)
    (folder / "strategy.yaml").write_text(
        "name: after_earnings\nfamily: after_earnings\nprior_trials: 0\n"
        "cost_calibration: ibkr_pro_tiered\n"
    )
    (folder / "configs" / "week.yaml").write_text(
        "period: {start: 2023-10-09, end: 2023-10-13}\nlookahead_check_rate: 1.0\n"
    )
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(tmp_path / "strategies"))
    from dataclasses import replace

    settings = replace(built, runs_dir=tmp_path / "runs")
    run_dir = runner.start_run(
        "after_earnings", "week", settings=settings, scratch=True, agent="test"
    )
    manifest = json.loads((run_dir / "manifest.json").read_text())
    store = DataStore(settings)
    assert manifest["inputs"]["form8k"] == {
        "input_id": inputs.form8k_id(store.build_id), "version": inputs.FORM8K_VERSION,
        "last_filed": "2023-10-10", "rows": 1,
    }  # fmt: skip
    assert runner.continue_run(run_dir, settings=settings)
    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert metrics["counts"]["signals"] == 1  # the session after the filing, and only that one


def test_an_unknown_input_is_refused():
    from kinn.engine.intraday.strategy import form8k_sessions

    class Wrong:
        inputs = {"form8-k": {}}

    with pytest.raises(ValueError, match="unknown inputs"):
        form8k_sessions(Wrong())
