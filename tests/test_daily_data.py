"""Daily data from a real build: total return, corporate actions, universe, fundamentals."""

import numpy as np
import pytest

from kinn.data.daily import load_daily
from kinn.data.store import DataStore
from kinn.data.universe import Universe
from tests import synthetic_raw as raw

EVERYONE = Universe("everyone", min_sessions_prior=1)


@pytest.fixture(scope="module")
def data(built):
    store = DataStore(built)
    return load_daily(
        store, store.sessions(raw.FIRST, raw.LAST_OPEN), EVERYONE, fundamentals=("equityusd",)
    )


def at(data, name, day, symbol):
    return getattr(data, name)[data.dates.index(day), data.symbols.index(symbol)]


def test_a_split_shows_as_a_ratio_and_leaves_the_return_at_zero(data):
    assert at(data, "split", raw.SPLIT_DAY, "SPLT") == 2.0
    assert at(data, "close", raw.SPLIT_DAY, "SPLT") == 20.0
    assert at(data, "prev_close", raw.SPLIT_DAY, "SPLT") == 20.0
    assert at(data, "ret", raw.SPLIT_DAY, "SPLT") == 0.0


def test_a_dividend_is_part_of_the_return_on_its_ex_date_only(data):
    assert at(data, "dividend", raw.DIVIDEND_DAY, "NEW") == 0.5
    assert at(data, "ret", raw.DIVIDEND_DAY, "NEW") == pytest.approx(0.5 / 20.0)
    assert np.nansum(data.dividend) == 0.5
    assert np.nansum(np.abs(data.ret)) == pytest.approx(0.5 / 20.0)  # prices are flat otherwise


def test_companies_follow_their_permaticker_through_a_rename(data):
    column = data.symbols.index("NEW")
    assert np.isfinite(data.close[:, column]).all()  # traded as OLD, then NEW: one company


def test_top_by_marketcap_keeps_only_the_largest_names_each_session(built):
    store = DataStore(built)
    sessions = store.sessions(raw.FIRST, raw.LAST_OPEN)
    top = load_daily(store, sessions, EVERYONE, top_by_marketcap=2)
    assert sorted(top.symbols) == ["PRE", "SPLT"]  # market caps 300 and 400; AAA and NEW smaller
    assert top.eligible[5:].all() and not top.eligible[0].any()  # no prior session on day one


def test_the_view_refuses_same_day_outcomes_and_history_stops_at_yesterday(data):
    i = data.dates.index(raw.SPLIT_DAY)
    view = data.view(i)
    with pytest.raises(KeyError):
        view.today("close")
    history = view.history("close", 3)
    assert history.shape[0] == 3 and np.array_equal(history[-1], data.close[i - 1], equal_nan=True)
    hidden = data.window(i, 5).view(5)
    assert np.isnan(hidden._data.close[-1]).all() and hidden.today("split").max() == 2.0


def test_canary_a_fundamental_is_not_visible_before_the_session_after_its_filing(data):
    column = data.symbols.index("AAA")
    equity = data.fundamentals["equityusd"][:, column]
    filed = data.dates.index(raw.FILING_DAY)
    assert (equity[: filed + 1] == 400.0).all()  # including the filing day itself
    assert (equity[filed + 1 :] == 500.0).all()
    everything = data.fundamentals["equityusd"]
    assert not np.isin(everything, [999.0, 777.0]).any()  # restated and holdout rows never load
    assert np.isnan(np.delete(everything, column, axis=1)).all()
