import math
from datetime import date

import pyarrow as pa
import pytest

from apps.workbench import markets, stocks
from tests.lab_fake import business_days


class MarketStore:
    def __init__(self):
        self.days = business_days(date(2020, 1, 1), date(2022, 12, 30))
        self.asked: list[date] = []
        rows = []
        for i, d in enumerate(self.days):
            rows.append({"date": d, "symbol": "SPY", "close": 300.0 * 1.001**i})
            rows.append({"date": d, "symbol": "USO", "close": 10.0 if i < 100 else 80.0})
        self.bars = pa.Table.from_pylist(rows)

    def sessions(self, start, end):
        self.asked.append(end)
        return [d for d in self.days if start <= d <= end]

    def daily(self, start, end, *, symbols):
        self.asked.append(end)
        keep = [
            r for r in self.bars.to_pylist() if start <= r["date"] <= end and r["symbol"] in symbols
        ]
        return pa.Table.from_pylist(keep)

    def breadth(self, start, end):
        self.asked.append(end)
        days = [d for d in self.days if start <= d <= end]
        return pa.Table.from_pylist(
            [{"date": d, "advancing": 60, "declining": 30, "traded": 100} for d in days]
        )


def test_a_split_sized_jump_is_taken_out_and_the_series_ends_at_the_last_price():
    values = stocks.continuous([10.0, 10.5, 84.0, 85.0, None, 86.0])
    assert values[-1] == 86.0 and values[4] is None
    assert math.isclose(values[2] / values[1], 1.0, rel_tol=1e-9)
    assert math.isclose(values[1] / values[0], 1.05, rel_tol=1e-9)


def test_funds_with_their_returns_and_the_days_breadth():
    store = MarketStore()
    page = markets.markets(store, date(2022, 12, 31))
    assert page["on"] == "2022-12-30" and max(store.asked) <= markets.LAST
    rows = {r["symbol"]: r for g in page["groups"] for r in g["rows"]}
    spy = rows["SPY"]
    assert math.isclose(spy["day"], 0.001, rel_tol=1e-4)
    assert math.isclose(spy["year"], 1.001**252 - 1, rel_tol=1e-4)
    assert rows["USO"]["three_years"] == 0.0 and rows["USO"]["close"] == 80.0
    assert rows["QQQ"]["close"] is None
    assert page["breadth"][-1] == {
        "date": "2022-12-30",
        "advancing": 60,
        "declining": 30,
        "traded": 100,
    }


def test_a_day_before_any_session_is_refused():
    with pytest.raises(ValueError):
        markets.markets(MarketStore(), date(1999, 1, 1))
