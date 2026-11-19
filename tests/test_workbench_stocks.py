import json
from datetime import date

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from apps.workbench import stocks
from tests.lab_fake import FakeStore, Stock, business_days, walk


class StockStore(FakeStore):
    def __init__(self, *args, history=(), **kwargs):
        super().__init__(*args, **kwargs)
        names = ("permaticker", "symbol", "valid_from", "valid_to")
        self.history = pa.Table.from_pylist(
            [dict(zip(names, row, strict=True)) for row in history],
            schema=pa.schema([("permaticker", pa.int64()), ("symbol", pa.string()),
                              ("valid_from", pa.date32()), ("valid_to", pa.date32())]),
        )  # fmt: skip
        self.build_id = f"stock-{id(self)}"

    def symbol_history(self) -> pa.Table:
        return self.history

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
