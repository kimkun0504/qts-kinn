import itertools
import json
from datetime import date, timedelta

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from apps.workbench import stocks
from tests.lab_fake import FakeStore, Stock, business_days, walk

BUILDS = itertools.count()


class StockStore(FakeStore):
    def __init__(self, *args, history=(), **kwargs):
        super().__init__(*args, **kwargs)
        names = ("permaticker", "symbol", "valid_from", "valid_to")
        self.history = pa.Table.from_pylist(
            [dict(zip(names, row, strict=True)) for row in history],
            schema=pa.schema([("permaticker", pa.int64()), ("symbol", pa.string()),
                              ("valid_from", pa.date32()), ("valid_to", pa.date32())]),
        )  # fmt: skip
        self.build_id = f"stock-{next(BUILDS)}"

    def symbol_history(self) -> pa.Table:
        return self.history

    def fundamentals_of(self, permaticker, *, fields, dimension) -> pa.Table:
        rows = [
            {"calendardate": filed - timedelta(days=35), "datekey": filed,
             **{f: values.get(f) for f in fields}}
            for perm, filed, values in self.fundamental_rows
            if perm == permaticker and values.get("dimension") == dimension
        ]  # fmt: skip
        schema = pa.schema(
            [("calendardate", pa.date32()), ("datekey", pa.date32())]
            + [(f, pa.float64()) for f in fields]
        )
        return pa.Table.from_pylist(rows, schema=schema)

    def form4_of(self, symbols):
        rows = [
            {"filed": date(2014, 3, 3), "symbol": "ABCD", "transaction_code": "P", "acquired": "A",
             "shares": 1000.0, "amount": 40000.0, "first_traded": date(2014, 2, 27),
             "last_traded": date(2014, 2, 28), "owner_name": "Doe Jane", "officer": True,
             "director": False, "ten_percent_owner": False, "title": "CFO", "accession": "a1"},
            {"filed": date(2011, 6, 1), "symbol": "OLDX", "transaction_code": "S", "acquired": "D",
             "shares": 50.0, "amount": 500.0, "first_traded": None, "last_traded": None,
             "owner_name": "Roe Rick", "officer": False, "director": True,
             "ten_percent_owner": True, "title": None, "accession": "a2"},
            {"filed": date(2016, 6, 1), "symbol": "OLDX", "transaction_code": "S", "acquired": "D",
             "shares": 50.0, "amount": 500.0, "first_traded": None, "last_traded": None,
             "owner_name": "Someone Else", "officer": False, "director": True,
             "ten_percent_owner": False, "title": None, "accession": "a3"},
        ]  # fmt: skip
        kept = sorted((r for r in rows if r["symbol"] in symbols), key=lambda r: r["filed"])
        return pa.Table.from_pylist(kept), {"first_filed": "2006-01-03", "last_filed": "2023-09-29"}

    def events_of(self, start, end, *, permatickers) -> pa.Table:
        return self._sql(
            "select * from e where date between ? and ? and permaticker in (select unnest(?)) "
            "order by date",
            [start, end, permatickers],
            e=self.events_table,
        )


@pytest.fixture
def store():
    days = business_days()
    n = len(days)
    split = days.index(date(2015, 3, 2))
    stocks_ = [
        Stock("ABCD", walk(n, 40.0, 0.0004, seed=1)),
        Stock("SPLT", np.where(np.arange(n) < split, 100.0, 50.0), split={split: 2.0}),
        Stock("ACME", walk(n, 10.0, 0.0, seed=2)),
    ]
    return StockStore(
        stocks_,
        events=[(date(2014, 5, 1), "ABCD", "22|91"), (date(2014, 8, 1), "ABCD", "13")],
        fundamentals=[
            ("ABCD", date(2014, 5, 1), {"dimension": "ARQ", "revenueusd": 1e8, "epsusd": 0.25}),
            ("ABCD", date(2014, 8, 1), {"dimension": "ARQ", "revenueusd": 1.2e8}),
            ("ABCD", date(2014, 8, 1), {"dimension": "ART", "revenueusd": 4.4e8}),
        ],
        history=[(1001, "ABCD", date(2013, 1, 1), date(2015, 12, 31)),
                 (1001, "OLDX", date(2010, 1, 1), date(2012, 12, 31))],
    )  # fmt: skip


def test_search_ranks_the_ticker_then_old_symbols_then_names(store):
    assert stocks.search(store, "abcd")[0]["ticker"] == "ABCD"
    old = stocks.search(store, "OLDX")
    assert old[0]["ticker"] == "ABCD" and old[0]["matched"] == "OLDX"
    assert [r["ticker"] for r in stocks.search(store, "ACME INC")] == ["ACME"]
    assert stocks.search(store, "  ") == []


def test_prices_are_adjusted_for_splits_back_from_the_last_close(store, tmp_path):
    page = stocks.stock(store, tmp_path / "runs", tmp_path / "lab", "SPLT")
    p = page["prices"]
    first = p["close"][0] * p["factor"][0]
    last = p["close"][-1] * p["factor"][-1]
    assert p["factor"][-1] == 1.0 and abs(first - 50.0) < 1e-6 and abs(last - 50.0) < 1e-6
    assert page["sealed_from"] == "2023-11-09" and max(p["date"]) < "2023-11-09"


def test_events_and_trades_from_the_run_store_the_lab_and_paper(store, tmp_path, monkeypatch):
    monkeypatch.setenv("KINN_PAPER_DIR", str(tmp_path / "paper"))
    runs, lab = tmp_path / "runs", tmp_path / "lab"
    run = runs / "20261115T000000Z_claude_x_aaaa"
    run.mkdir(parents=True)
    (run / "manifest.json").write_text(json.dumps({
        "run_id": run.name, "strategy": "x", "config": "base", "kind": "backtest",
        "status": "complete"}))  # fmt: skip
    pq.write_table(pa.Table.from_pylist([
        {"day": date(2014, 6, 2), "symbol": "ABCD", "permaticker": 1001, "entry_price": 40.0,
         "exit_price": 41.0, "exit_reason": "close", "net": 50.0, "notional": 2000.0,
         "tag": ""},
        {"day": date(2014, 6, 2), "symbol": "ACME", "permaticker": 1003, "entry_price": 9.0,
         "exit_price": 9.5, "exit_reason": "close", "net": 10.0, "notional": 2000.0,
         "tag": ""},
    ]), run / "trades.parquet")  # fmt: skip
    lab_run = lab / "runs" / "20261118T000000Z_mine_bbbb"
    lab_run.mkdir(parents=True)
    (lab_run / "manifest.json").write_text(json.dumps({"algorithm": "mine"}))
    pq.write_table(pa.Table.from_pylist([
        {"ticker": "ABCD", "signal_date": date(2014, 7, 1), "entry_date": date(2014, 7, 2),
         "exit_date": date(2014, 7, 23), "entry_price": 41.0, "exit_price": 43.0,
         "net": 0.04, "reason": "hold", "taken": True},
        {"ticker": "ABCD", "signal_date": date(2009, 7, 1), "entry_date": date(2009, 7, 2),
         "exit_date": date(2009, 7, 23), "entry_price": 1.0, "exit_price": 1.0,
         "net": 0.0, "reason": "hold", "taken": True},
    ]), lab_run / "trades.parquet")  # fmt: skip
    page = stocks.stock(store, runs, lab, "ABCD")
    assert [e["results"] for e in page["events"]] == [True, False]
    sources = [(t["source"], t["label"], t["net"]) for t in page["trades"]]
    assert sources == [("lab", "mine", 0.04), ("run", "x", 0.025)]
    assert page["symbols"][0]["symbol"] in ("OLDX", "ABCD")
    assert stocks.stock(store, runs, lab, "NOPE") is None


def test_a_date_picks_the_company_that_held_the_symbol_then(tmp_path):
    days = business_days()
    n = len(days)
    store = StockStore(
        [Stock("NEWX", walk(n, 10.0, 0.0, seed=4)), Stock("ZZZZ", walk(n, 20.0, 0.0, seed=5))],
        history=[(1001, "NEWX", date(2014, 1, 1), date(2015, 12, 31)),
                 (1002, "NEWX", date(2008, 1, 1), date(2012, 12, 31)),
                 (1002, "ZZZZ", date(2013, 1, 1), date(2015, 12, 31))],
    )  # fmt: skip
    runs, lab = tmp_path / "runs", tmp_path / "lab"
    assert stocks.stock(store, runs, lab, "NEWX")["permaticker"] == 1001
    then = stocks.stock(store, runs, lab, "NEWX", on=date(2010, 6, 1))
    assert then["permaticker"] == 1002 and then["others"][0]["permaticker"] == 1001
    chosen = stocks.stock(store, runs, lab, "NEWX", permaticker=1002, on=date(2015, 1, 2))
    assert chosen["ticker"] == "ZZZZ"


def test_the_financials_by_quarter_and_trailing_year(store, tmp_path):
    page = stocks.stock(store, tmp_path / "runs", tmp_path / "lab", "ABCD")
    money = page["financials"]
    assert money["currency"] == "USD"
    assert [q["revenueusd"] for q in money["quarterly"]] == [1e8, 1.2e8]
    first = money["quarterly"][0]
    assert first["epsusd"] == 0.25 and first["filed"] == "2014-05-01"
    assert [q["revenueusd"] for q in money["trailing"]] == [4.4e8]
    empty = stocks.stock(store, tmp_path / "runs", tmp_path / "lab", "ACME")["financials"]
    assert empty["quarterly"] == [] and empty["trailing"] == []


def test_closes_for_stocks_split_adjusted_and_for_funds_as_traded(store):
    found = stocks.closes(store, ["splt", "SPY", "NOPE", " "])
    by = {s["symbol"]: s for s in found["series"]}
    assert set(by) == {"SPLT", "SPY"} and found["missing"] == ["NOPE"]
    assert set(by["SPLT"]["close"]) == {50.0}
    assert by["SPY"]["name"] == "SPY" and len(by["SPY"]["date"]) == len(by["SPY"]["close"]) > 100
    assert max(by["SPY"]["date"]) < found["sealed_from"]


def test_insider_buys_and_sells_under_each_symbol_the_company_held(store, tmp_path):
    page = stocks.stock(store, tmp_path / "runs", tmp_path / "lab", "ABCD")
    found = page["insiders"]
    assert found["last"] == "2023-09-29" and found["count"] == 2
    assert [(r["filed"], r["side"], r["role"]) for r in found["rows"]] == [
        ("2011-06-01", "sell", "Director, 10% owner"),
        ("2014-03-03", "buy", "CFO"),
    ]
    assert found["rows"][1]["traded_from"] == "2014-02-27" and found["rows"][1]["amount"] == 40000.0


def test_a_foreign_filers_local_currency_lines_are_marked():
    assert stocks.reports_in_dollars("Domestic Common Stock Primary Class")
    assert stocks.reports_in_dollars(None)
    assert not stocks.reports_in_dollars("ADR Common Stock")
    assert not stocks.reports_in_dollars("Canadian Common Stock")
