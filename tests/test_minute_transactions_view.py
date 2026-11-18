"""Existing bar counts reach the strategy unchanged and obey the same prefix as prices."""

from datetime import date

import numpy as np
import pyarrow as pa
import pytest

from kinn.data.universe import Universe
from kinn.engine.intraday.data import PRIOR_COLUMNS, load_day, make_symbol_day

DAY = date(2010, 1, 4)


def stock(transactions=None):
    return make_symbol_day(
        "ABC",
        1,
        [570, 571],
        [10, 11],
        [10, 11],
        [10, 11],
        [10, 11],
        [1000, 2000],
        {"prev_close": 10},
        transactions=transactions,
    )


def test_legacy_constructor_and_unavailable_counts_remain_compatible():
    bars = stock()
    assert bars.transactions is None
    assert bars.upto(570).transactions is None
    assert bars.upto(570).prior == {"prev_close": 10}


@pytest.mark.parametrize("counts", [[100], [[100, 200]], np.array(100)])
def test_count_alignment_is_validated_on_construction(counts):
    with pytest.raises(ValueError, match="align one-to-one"):
        stock(counts)


def test_prefix_truncates_counts_and_preserves_missing_and_observed_zero():
    bars = stock([100, np.nan])
    assert bars.upto(569).transactions.shape == (0,)
    np.testing.assert_equal(bars.upto(570).transactions, [100])
    np.testing.assert_equal(bars.upto(571).transactions, [100, np.nan])
    assert stock([0, 100]).transactions[0] == 0


class Store:
    def __init__(self, empty_bars=False):
        self.empty_bars = empty_bars
        self.selected = None

    def calendar(self, start, end):
        assert start == end == DAY
        return pa.table({"close_minute_et": [960]})

    def panel_columns(self):
        return list(PRIOR_COLUMNS)

    def panel(self, start, end, **kwargs):
        assert start == end == DAY
        rows = [
            {"symbol": s, "permaticker": i, "close": 11.0, **{c: None for c in PRIOR_COLUMNS}}
            for i, s in enumerate(("AAA", "BBB"), 1)
        ]
        return pa.Table.from_pylist(rows)

    def minute(self, day, *, symbols, columns):
        assert day == DAY and symbols == ["AAA", "BBB"]
        self.selected = columns
        table = pa.table(
            {
                "symbol": ["AAA", "AAA"],
                "minute_et": [570, 571],
                "open": [10.0, 11.0],
                "high": [10.0, 11.0],
                "low": [10.0, 11.0],
                "close": [10.0, 11.0],
                "volume": [1000, 2000],
                "transactions": pa.array([100, None], type=pa.int64()),
            }
        )
        return table.slice(0, 0) if self.empty_bars else table


@pytest.mark.parametrize("empty_bars", [False, True])
def test_loader_propagates_the_column_and_empty_members_without_imputation(empty_bars):
    store = Store(empty_bars)
    data = load_day(store, DAY, Universe("synthetic"))
    assert "transactions" in store.selected.split(", ")
    aaa, bbb = data.view.symbols["AAA"], data.view.symbols["BBB"]
    assert bbb.transactions.shape == bbb.minute.shape == (0,)
    if empty_bars:
        assert aaa.transactions.shape == (0,)
    else:
        np.testing.assert_equal(aaa.transactions, [100, np.nan])
        np.testing.assert_equal(data.view.upto(570).symbols["AAA"].transactions, [100])
        assert data.view.upto(570).symbols["AAA"].minute.tolist() == [570]
