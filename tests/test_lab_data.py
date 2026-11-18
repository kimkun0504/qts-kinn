"""What an algorithm sees in the Lab, and the checks on what it returns (decision 0023)."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from kinn.lab import algorithm as alg
from kinn.lab import data as lab_data
from kinn.lab.data import DataError, LabData
from kinn.lab.settings import parse
from tests.lab_fake import FakeStore, Stock, business_days, standard, walk

PERIOD = {
    "period": "custom",
    "start": "2015-01-02",
    "end": "2015-09-30",
    "universe": {"min_market_cap": 1e6},
}


@pytest.fixture(scope="module")
def store():
    return standard()


@pytest.fixture
def data(store):
    return LabData(store, parse(PERIOD))


def code(body: str) -> alg.Algorithm:
    return alg.load("import numpy as np\nimport pandas as pd\n\n" + body)


# -- the data -----------------------------------------------------------------------------
def test_tables_are_sessions_by_stocks(data):
    close = data.close
    assert isinstance(close, pd.DataFrame)
    assert list(close.columns) == ["UPP", "DWN", "SPL", "GON", "FLT"]  # by company id
    assert close.index.equals(data.dates) and close.dtypes.iloc[0] == np.float32
    assert isinstance(data.spy, pd.Series) and isinstance(data.sector, pd.Series)
    assert data.sector["DWN"] == "Energy"
    assert "close" in data.fields() and "revenue" in data.fields()


def test_adjusted_closes_run_through_a_split(data):
    day = pd.Timestamp("2015-03-02")  # SPL splits 2-for-1 that morning
    before = data.index.get_loc(day) - 1
    close, adj, returns = data.close["SPL"], data.adj_close["SPL"], data.returns["SPL"]
    assert close.iloc[before + 1] < 0.6 * close.iloc[before]  # the price halves
    assert abs(returns.loc[day]) < 0.05  # the return does not
    assert adj.loc[day] / adj.iloc[before] == pytest.approx(1 + returns.loc[day], rel=1e-5)
    first = close.first_valid_index()
    assert adj.loc[first] == pytest.approx(close.loc[first])  # anchored at the first close


def test_the_universe_opens_at_the_period_and_closes_after_the_last_entry(data):
    eligible = data.eligible
    assert not eligible.iloc[: data.first_row].any(axis=None)
    assert not eligible.iloc[data.last_signal_row + 2 :].any(axis=None)
    assert eligible.iloc[data.first_row]["UPP"]
    assert not eligible["GON"].loc["2015-06-01":].any()  # no bar, no entry
    assert data.dates[data.first_row] == pd.Timestamp("2015-01-02")


def test_events_fundamentals_and_trade_counts(data):
    assert data.earnings.loc["2015-02-10", "UPP"] and not data.earnings.loc["2015-04-07", "DWN"]
    assert data.filing.loc["2015-04-07", "DWN"]
    revenue = data.revenue["UPP"]
    assert np.isnan(revenue.loc["2015-02-10"])  # filed that day: usable the next session
    assert revenue.loc["2015-02-11"] == 1e8 and revenue.loc["2015-05-11"] == 1.2e8
    assert data.trade_size.iloc[data.first_row]["FLT"] == pytest.approx(4000)


def test_changing_a_table_never_changes_the_data(data):
    close = data.close
    close.iloc[0, 0] = -1.0
    close[close > 0] = np.nan
    close["UPP"] *= 2
    fresh = data.close
    assert fresh.iloc[0, 0] != -1.0 and fresh.notna().any(axis=None)
    assert not fresh.equals(close)
    with pytest.raises(ValueError, match="read-only"):
        data.close.to_numpy()[0, 0] = 1.0


def test_an_unknown_field_says_so(data):
    with pytest.raises(AttributeError, match="data has no field 'closing'"):
        data.closing  # noqa: B018


def test_a_cut_view_ends_at_the_cut_and_agrees_before_it(data):
    view = data.cut(data.first_row + 30)
    assert len(view.close) == data.first_row + 30
    assert view.adj_close.equals(data.adj_close.iloc[: data.first_row + 30])


def test_no_stock_in_the_universe_is_refused(store):
    with pytest.raises(DataError, match="No stock"):
        LabData(store, parse({**PERIOD, "universe": {"min_market_cap": 1e12}}))


def test_a_run_too_big_for_the_machine_is_refused(store, monkeypatch):
    monkeypatch.setattr(lab_data, "physical_memory", lambda: 10_000)
    with pytest.raises(DataError, match="needs about"):
        LabData(store, parse(PERIOD))


def test_blank_checks_can_be_left_out():
    days = business_days()
    shell = Stock("SHL", walk(len(days), 10.0, 0, seed=7), siccode="6770")
    store = FakeStore([Stock("ONE", walk(len(days), 10.0, 0, seed=8)), shell], days)
    keep = LabData(store, parse(PERIOD))
    drop = LabData(
        store, parse({**PERIOD, "universe": {"min_market_cap": 1e6, "exclude_blank_checks": True}})
    )
    assert list(keep.stocks) == ["ONE", "SHL"] and list(drop.stocks) == ["ONE"]


# -- loading the algorithm --------------------------------------------------------------
def test_a_syntax_error_names_the_line():
    with pytest.raises(alg.AlgorithmError, match=r"Syntax error at line 4"):
        code("def signal(data)\n    return data.close > 0\n")


def test_an_error_while_loading_names_the_owners_line():
    with pytest.raises(alg.AlgorithmError, match=r"your code, line 4"):
        code("x = 1 / 0\n")


def test_signal_is_required_and_settings_must_be_a_dict():
    with pytest.raises(alg.AlgorithmError, match="signal\\(data\\)"):
        code("def sig(data):\n    return 1\n")
    with pytest.raises(alg.AlgorithmError, match="SETTINGS must be a dict"):
        _ = code("SETTINGS = 3\ndef signal(data):\n    return data.close > 0\n").settings


def test_an_error_in_signal_names_the_owners_line(data):
    algorithm = code("def signal(data):\n    x = data.close\n    return x.nope()\n")
    with pytest.raises(alg.AlgorithmError, match=r"your code, line 6, in signal"):
        alg.signals(algorithm, data, "signal")


def test_an_unknown_field_in_signal_is_reported_plainly(data):
    algorithm = code("def signal(data):\n    return data.closing > 0\n")
    with pytest.raises(alg.AlgorithmError, match="data has no field 'closing'"):
        alg.signals(algorithm, data, "signal")


@pytest.mark.parametrize(
    ("body", "words"),
    [
        ("return data.close['UPP'] > 0", "one column"),
        ("return 3", "must return a pandas DataFrame"),
        ("return (data.close > 0).rename(columns={'UPP': 'ZZZ'})", "not in the data: ZZZ"),
        ("return (data.close > 0).iloc[:10]", "missing most dates"),
    ],
)
def test_a_wrong_shape_is_refused(data, body, words):
    algorithm = code(f"def signal(data):\n    {body}\n")
    with pytest.raises(alg.AlgorithmError, match=words):
        alg.signals(algorithm, data, "signal")


def test_arrays_numbers_and_scores_are_accepted(data):
    entries, exits = alg.signals(
        code("def signal(data):\n    return (data.close > 0).to_numpy()\n"), data, "signal"
    )
    assert entries.dtype == bool and entries.any() and exits is None
    numbers, _ = alg.signals(
        code("def signal(data):\n    return (data.close > 30) * 1\n"), data, "signal"
    )
    assert numbers.dtype == bool and numbers.any()
    scores, _ = alg.signals(
        code("def signal(data):\n    return data.returns.rolling(5).sum()\n"), data, "rank"
    )
    assert scores.dtype == np.float64 and np.isnan(scores[0]).all()
    with pytest.raises(alg.AlgorithmError, match="must return numbers"):
        alg.signals(code("def signal(data):\n    return data.close.astype(str)\n"), data, "rank")


def test_a_few_missing_dates_are_filled_with_no_signal(data):
    algorithm = code("def signal(data):\n    return (data.close > 0).iloc[5:]\n")
    entries, _ = alg.signals(algorithm, data, "signal")
    assert entries.dtype == bool and not entries[:5].any() and entries[5:].any()


# -- lookahead ----------------------------------------------------------------------------
def look(data, body: str, mode: str = "signal") -> dict:
    algorithm = code(body)
    entries, exits = alg.signals(algorithm, data, mode)
    return alg.lookahead(algorithm, data, mode, entries, exits)


def test_honest_code_passes_the_lookahead_test(data):
    found = look(
        data,
        "def signal(data):\n    r = data.returns.rolling(10).mean()\n"
        "    return r > r.rolling(60).mean()\n",
    )
    assert found["passed"] and len(found["checked"]) == 2


@pytest.mark.parametrize(
    "body",
    [
        "return data.returns.shift(-1) > 0",
        "return data.close > data.close.mean()",
        "return data.close.rank(pct=True) > 0.5",
    ],
)
def test_peeking_ahead_is_caught(data, body):
    found = look(data, f"def signal(data):\n    {body}\n")
    assert not found["passed"]
    assert "with the later data" in found["detail"]


def test_peeking_in_exit_signal_is_caught_and_ranks_are_compared(data):
    found = look(
        data,
        "def signal(data):\n    return data.close > 0\n"
        "def exit_signal(data):\n    return data.returns.shift(-1) < 0\n",
    )
    assert not found["passed"] and "exit_signal(data) changed" in found["detail"]
    found = look(data, "def signal(data):\n    return data.close.rolling(20).mean()\n", "rank")
    assert found["passed"]


def test_period_dates(data):
    assert data.load_start <= date(2014, 1, 1)
    assert data.load_end <= lab_data.LAST_DATA_DAY
