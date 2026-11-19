import math
from datetime import date

import numpy as np
import pyarrow as pa
import pytest

from apps.workbench import screener
from tests.lab_fake import FakeStore, Stock, business_days


class ScreenStore(FakeStore):
    def __init__(self, *args, books=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.bars = self.__dict__.pop("panel")
        self.books = list(books)
        self.asked: list[date] = []
        self.build_id = f"screen-{id(self)}"

    def sessions(self, start, end):
        self.asked.append(end)
        return super().sessions(start, end)

    def panel(self, start, end, *, columns="*"):
        self.asked.append(end)
        return self._sql(
            f"select {columns} from p where date between ? and ? order by date, symbol",
            [start, end],
            p=self.bars.append_column("exchange", pa.array(["NASDAQ"] * self.bars.num_rows)),
        )

    def securities(self):
        currency = pa.array(
            ["CAD" if t == "LOUD" else "USD" for t in self.master["ticker"].to_pylist()]
        )
        return self.master.append_column("currency", currency)

    def fundamentals_as_of(self, day, *, fields):
        self.asked.append(day)
        perm = {s.ticker: p for p, s in enumerate(self.stocks, start=1001)}
        rows = [
            {"permaticker": perm[t], "datekey": filed, "calendardate": period,
             **{f: values.get(f) for f in fields},
             **{f"{f}_year_ago": values.get(f"{f}_year_ago") for f in fields}}
            for t, filed, period, values in self.books if filed < day
        ]  # fmt: skip
        schema = pa.schema(
            [("permaticker", pa.int64()), ("datekey", pa.date32()), ("calendardate", pa.date32())]
            + [(f, pa.float64()) for f in fields]
            + [(f"{f}_year_ago", pa.float64()) for f in fields]
        )
        return pa.Table.from_pylist(rows, schema=schema)


@pytest.fixture
def store():
    screener._screens.clear()
    days = business_days()
    n = len(days)
    split = n - 50
    stopped = np.full(n, 20.0)
    stopped[-30:] = np.nan
    return ScreenStore(
        [
            Stock("GROW", 10.0 * 1.001 ** np.arange(n), market_cap=5e9),
            Stock("SPLT", np.where(np.arange(n) < split, 100.0, 50.0), split={split: 2.0}),
            Stock("GONE", stopped),
            Stock("LOUD", np.full(n, 8.0), market_cap=2e8),
        ],
        books=[
            ("GROW", date(2015, 11, 2), date(2015, 9, 30),
             {"revenueusd": 1e9, "revenueusd_year_ago": 8e8, "netinccmnusd": 2.5e8,
              "equityusd": 1e9, "fcf": 1e8}),
            ("GROW", date(2015, 12, 31), date(2015, 12, 31), {"revenueusd": 9e9}),
            ("SPLT", date(2013, 11, 4), date(2013, 9, 30), {"revenueusd": 1e9}),
            ("LOUD", date(2015, 11, 2), date(2015, 9, 30), {"revenueusd": 1e8, "fcf": 1e7}),
        ],
    )  # fmt: skip


def rows(page):
    return {r[0]: dict(zip(page["columns"], r, strict=True)) for r in page["rows"]}


def test_every_stock_that_traded_on_the_session_with_its_returns(store):
    page = screener.screen(store, date(2015, 12, 31))
    found = rows(page)
    assert page["on"] == "2015-12-31" and set(found) == {"GROW", "SPLT", "LOUD"}
    grow = found["GROW"]
    for name, n in screener.RETURNS.items():
        assert math.isclose(grow[name], 1.001**n - 1, rel_tol=1e-4)
    assert abs(grow["vol_60"]) < 1e-6
    assert list(found) == ["GROW", "SPLT", "LOUD"]
    assert math.isclose(grow["market_cap"], 5e9 * 1.001, rel_tol=1e-6)


def test_returns_and_the_distance_from_the_high_are_adjusted_for_splits(store):
    split = rows(screener.screen(store, date(2015, 12, 31)))["SPLT"]
    assert split["ret_1y"] == 0.0 and split["ret_3m"] == 0.0
    assert math.isclose(split["from_high"], 1 / 1.01 - 1, rel_tol=1e-4)


def test_valuations_use_only_filings_made_before_the_session(store):
    grow = rows(screener.screen(store, date(2015, 12, 31)))["GROW"]
    cap = grow["market_cap"]
    assert grow["filed"] == "2015-11-02" and grow["revenue"] == 1e9
    assert math.isclose(grow["pe"], cap / 2.5e8, rel_tol=1e-5)
    assert math.isclose(grow["ps"], cap / 1e9, rel_tol=1e-5)
    assert math.isclose(grow["fcf_yield"], 1e8 / cap, rel_tol=1e-5)
    assert math.isclose(grow["revenue_growth"], 0.25, rel_tol=1e-6)


def test_stale_and_foreign_currency_numbers_are_left_out(store):
    found = rows(screener.screen(store, date(2015, 12, 31)))
    assert found["SPLT"]["revenue"] is None and found["SPLT"]["ps"] is None
    assert found["LOUD"]["revenue"] == 1e8 and found["LOUD"]["fcf_yield"] is None


def test_a_young_stock_has_no_long_returns(store):
    found = rows(screener.screen(store, date(2014, 3, 3)))
    assert found["GROW"]["ret_1m"] is not None and found["GROW"]["ret_1y"] is None


def test_never_reads_past_the_seal_and_reuses_a_screen(store):
    with pytest.raises(ValueError):
        screener.screen(store, date(2030, 1, 1))
    assert max(store.asked) == screener.LAST
    first = screener.screen(store, date(2015, 12, 31))
    assert screener.screen(store, date(2016, 1, 3)) is first
    with pytest.raises(ValueError):
        screener.screen(store, date(1999, 1, 1))
