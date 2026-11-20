"""The two DataStore reads the Lab added, on a real (synthetic) build, and the seal on them."""

from datetime import date

import pytest

from kinn.data import seal
from kinn.data.store import DataStore
from kinn.data.universe import Universe
from tests.synthetic_raw import FILING_DAY, FIRST, LAST_OPEN

EVERYONE = Universe(name="t", min_sessions_prior=0)


def test_members_and_their_rows(built):
    store = DataStore(built)
    members = store.universe_members(FIRST, LAST_OPEN, EVERYONE)
    assert members == sorted(members) and len(members) >= 2
    some = members[:2]
    table = store.panel_of(FIRST, LAST_OPEN, permatickers=some, columns="date, permaticker, close")
    assert set(table["permaticker"].to_pylist()) <= set(some)
    keys = list(zip(table["date"].to_pylist(), table["permaticker"].to_pylist(), strict=True))
    assert keys == sorted(keys)
    assert max(table["date"].to_pylist()) <= LAST_OPEN


def test_a_tighter_universe_has_fewer_members(built):
    store = DataStore(built)
    everyone = store.universe_members(FIRST, LAST_OPEN, EVERYONE)
    seasoned = store.universe_members(FIRST, LAST_OPEN, Universe(name="t", min_sessions_prior=20))
    assert set(seasoned) < set(everyone)


@pytest.mark.parametrize("read", ["members", "rows"])
def test_holdout_dates_are_refused(built, read):
    store = DataStore(built)
    with pytest.raises(seal.HoldoutError):
        if read == "members":
            store.universe_members(FIRST, date(2023, 11, 9), EVERYONE)
        else:
            store.panel_of(FIRST, date(2023, 11, 9), permatickers=[1], columns="date")


def test_one_companys_events_and_the_symbol_history(built):
    store = DataStore(built)
    every = store.events(FIRST, LAST_OPEN)
    some = sorted(set(every["permaticker"].to_pylist()))[:1]
    mine = store.events_of(FIRST, LAST_OPEN, permatickers=some)
    assert mine.num_rows and set(mine["permaticker"].to_pylist()) == set(some)
    assert mine.num_rows == sum(p == some[0] for p in every["permaticker"].to_pylist())
    history = store.symbol_history()
    assert {"permaticker", "symbol", "valid_from", "valid_to"} <= set(history.column_names)
    with pytest.raises(seal.HoldoutError):
        store.events_of(FIRST, date(2023, 11, 9), permatickers=some)


def test_fundamentals_as_of_a_day_use_filings_made_before_it(built):
    store = DataStore(built)
    on_filing = store.fundamentals_as_of(FILING_DAY, fields=("equityusd",)).to_pylist()
    after = store.fundamentals_as_of(date(2023, 11, 8), fields=("equityusd",)).to_pylist()
    assert [r["equityusd"] for r in on_filing] == [400.0]
    assert [r["equityusd"] for r in after] == [500.0]
    assert after[0]["calendardate"] == date(2023, 9, 30) and after[0]["equityusd_year_ago"] is None
    with pytest.raises(seal.HoldoutError):
        store.fundamentals_as_of(date(2023, 11, 9), fields=("equityusd",))
    with pytest.raises(KeyError):
        store.fundamentals_as_of(date(2023, 11, 8), fields=("price",))


def test_one_companys_fundamentals_stop_at_the_seal(built):
    store = DataStore(built)
    perm = next(r["permaticker"] for r in store.securities().to_pylist() if r["ticker"] == "AAA")
    rows = store.fundamentals_of(perm, fields=("equityusd",), dimension="ART").to_pylist()
    assert [r["equityusd"] for r in rows] == [400.0, 500.0]
    assert store.fundamentals_of(perm, fields=("equityusd",), dimension="ARQ").num_rows == 0


def test_breadth_counts_rising_and_falling_common_stocks_and_stops_at_the_seal(built):
    store = DataStore(built)
    rows = store.breadth(FIRST, LAST_OPEN).to_pylist()
    assert rows and all(r["advancing"] + r["declining"] <= r["traded"] for r in rows)
    assert max(r["date"] for r in rows) <= LAST_OPEN
    with pytest.raises(seal.HoldoutError):
        store.breadth(FIRST, date(2023, 11, 9))
