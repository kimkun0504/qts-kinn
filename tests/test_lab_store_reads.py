"""The two DataStore reads the Lab added, on a real (synthetic) build, and the seal on them."""

from datetime import date

import pytest

from kinn.data import seal
from kinn.data.store import DataStore
from kinn.data.universe import Universe
from tests.synthetic_raw import FIRST, LAST_OPEN

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
