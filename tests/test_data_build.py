"""The data layer, end to end on the synthetic raw folder (tests/synthetic_raw.py)."""

from datetime import date

import duckdb
import pyarrow.parquet as pq
import pytest

from kinn.core.settings import HOLDOUT_START
from kinn.data import build, master, raw, seal
from kinn.data.store import DataStore
from kinn.data.universe import PRE_OPEN_COLUMNS, Universe
from tests import synthetic_raw as syn

START, END = syn.FIRST, syn.LAST_OPEN


def _rows(table):
    return table.to_pylist()


def test_raw_listing_never_returns_holdout_files(built):
    for kind in ("day", "minute"):
        files = raw.massive_files(built.raw_dir, kind)
        assert files and max(f.day for f in files) == syn.LAST_OPEN


def test_no_processed_file_holds_a_holdout_date_or_the_poison_marker(built):
    con = duckdb.connect()
    files = list(built.data_dir.rglob("*.parquet"))
    assert len(files) > 40
    for path in files:
        schema = pq.read_schema(path)
        for field in schema:
            kind = str(field.type)
            if kind.startswith(("date", "timestamp")):
                latest = con.execute(
                    f"select max(\"{field.name}\")::date from '{path}'"
                ).fetchone()[0]
                limit = HOLDOUT_START if field.name == "valid_to" else seal.LAST_OPEN_DATE
                assert latest is None or latest <= limit, (path, field.name, latest)
            if kind in ("string", "large_string"):
                hit = con.execute(
                    f"select count(*) from '{path}' where \"{field.name}\" = 'POISON'"
                ).fetchone()[0]
                assert hit == 0, (path, field.name)


def test_names_listed_after_the_seal_do_not_exist(built):
    store = DataStore(built)
    tickers = set(pq.read_table(store.table_path("security_master"))["ticker"].to_pylist())
    assert "FUT" not in tickers and "AAA" in tickers


def test_a_delisting_after_the_seal_is_not_visible(built):
    store = DataStore(built)
    rows = {r["ticker"]: r for r in _rows(pq.read_table(store.table_path("security_master")))}
    assert rows["GONE"]["last_price_date"] is None and rows["GONE"]["delisted"] is False
    assert rows["DEAD1"]["last_price_date"] == syn.DEAD_LAST and rows["DEAD1"]["delisted"] is True


def test_symbol_history_handles_renames_and_reuse(built):
    store = DataStore(built)
    history = {}
    for row in _rows(pq.read_table(store.table_path("symbol_history"))):
        history.setdefault(row["permaticker"], []).append(
            (row["symbol"], row["valid_from"], row["valid_to"])
        )
    assert sorted(history[1002]) == [
        ("NEW", syn.RENAME_DAY, HOLDOUT_START),
        ("OLD", date(2020, 1, 2), syn.RENAME_DAY),
    ]
    # Renamed after the seal: before it, the company traded under the old symbol.
    assert history[1003] == [("PRE", date(2020, 1, 2), HOLDOUT_START)]
    # A reused symbol belongs to one company at a time.
    assert [s for s, _, _ in history[1004]] == ["DEAD"] and history[1004][0][2] <= syn.REUSE_FIRST
    assert history[1005] == [("DEAD", syn.REUSE_FIRST, HOLDOUT_START)]


def test_traded_symbol_strips_the_suffix_only_for_delisted_names():
    assert master.traded_symbol("FB1", delisted=True) == "FB"
    assert master.traded_symbol("BRK.B", delisted=True) == "BRK.B"
    assert master.traded_symbol("A1", delisted=False) == "A1"


def test_panel_attaches_the_right_company_through_a_rename_and_a_reuse(built):
    store = DataStore(built)
    rows = _rows(store.panel(START, END, columns="date, symbol, permaticker"))
    by_symbol = {}
    for row in rows:
        by_symbol.setdefault(row["symbol"], set()).add(row["permaticker"])
    assert by_symbol["OLD"] == by_symbol["NEW"] == {1002}
    assert by_symbol["PRE"] == {1003}
    assert by_symbol["DEAD"] == {1004, 1005}
    assert "SPY" not in by_symbol  # not in the security master
    dead = {r["date"]: r["permaticker"] for r in rows if r["symbol"] == "DEAD"}
    assert dead[syn.DEAD_LAST] == 1004 and dead[syn.REUSE_FIRST] == 1005


def test_prior_close_is_split_adjusted_and_lags_are_strictly_prior(built):
    store = DataStore(built)
    rows = {(r["symbol"], r["date"]): r for r in _rows(store.panel(START, END))}
    split = rows[("SPLT", syn.SPLIT_DAY)]
    assert split["split_ratio"] == 2 and split["prev_close"] == pytest.approx(20.0)
    assert split["open"] == pytest.approx(20.0)
    days = syn.sessions()
    first, second = rows[("AAA", days[0])], rows[("AAA", days[1])]
    assert first["prev_close"] is None and first["sessions_prior"] == 0
    assert second["adv20_prev"] == pytest.approx(first["dollar_volume"])
    assert second["marketcap_prev"] == pytest.approx(100.0e6)
    # The rename does not reset the company's history.
    assert rows[("NEW", syn.RENAME_DAY)]["sessions_prior"] == days.index(syn.RENAME_DAY)


def test_universe_filters_use_only_pre_open_columns(built):
    universe = Universe(
        "test", min_prev_close=5.0, max_adv20=1e12, min_marketcap=1.0, min_sessions_prior=3
    )
    where = universe.where()
    for column in ("open", "high", "low", "close", "volume", "dollar_volume"):
        assert column not in where.replace("prev_close", "")
    assert all(c in PRE_OPEN_COLUMNS for c in ("prev_close", "adv20_prev", "marketcap_prev"))
    rows = _rows(DataStore(built).panel(START, END, universe=universe, columns="symbol, date"))
    symbols = {r["symbol"] for r in rows}
    assert "AAA" in symbols and "DEAD" not in symbols and "PRE" in symbols
    assert min(r["date"] for r in rows) == syn.sessions()[3]


def test_canary_the_past_does_not_change_when_later_data_is_added(built, build_synthetic):
    """Point-in-time canary: a build that ends earlier must agree on every earlier row."""
    cutoff = date(2023, 10, 24)
    early = build_synthetic("early", last=cutoff, with_holdout=False)
    full_rows = _rows(DataStore(built).panel(START, cutoff))
    early_rows = _rows(DataStore(early).panel(START, cutoff))
    assert full_rows == early_rows and len(full_rows) > 100


def test_store_refuses_holdout_reads(built):
    store = DataStore(built)
    for read in (
        lambda: store.panel(START, HOLDOUT_START),
        lambda: store.calendar(START, date(2024, 1, 1)),
        lambda: store.minute(HOLDOUT_START),
        lambda: store.events(START, HOLDOUT_START),
        lambda: store.daily(START, HOLDOUT_START, symbols=["SPY"]),
    ):
        with pytest.raises(seal.HoldoutError):
            read()


def test_minute_bars_and_calendar(built):
    store = DataStore(built)
    day = date(2023, 11, 6)  # after the clocks change: 09:30 New York is 14:30 UTC
    bars = _rows(store.minute(day, symbols=["AAA"]))
    assert [b["minute_et"] for b in bars] == [480, 570, 571, 700, 959]
    assert bars[1]["bar_start"].hour == 14 and bars[1]["bar_start"].minute == 30
    summer = _rows(store.minute(date(2023, 10, 2), symbols=["AAA"]))
    assert summer[1]["bar_start"].hour == 13 and summer[1]["minute_et"] == 570
    calendar = {r["date"]: r for r in _rows(store.calendar(START, END))}
    assert len(calendar) == len(syn.sessions())
    assert calendar[syn.EARLY_CLOSE_DAY]["close_minute_et"] == 780
    assert calendar[day]["close_minute_et"] == 960


def test_events_are_keyed_by_company_and_stop_at_the_seal(built):
    rows = _rows(DataStore(built).events(START, END))
    assert rows == [{"permaticker": 1001, "date": date(2023, 10, 10), "eventcodes": "22|91"}]


def test_build_id_is_stable_and_changes_with_the_raw_data(built, build_synthetic):
    assert build.paths(built).build_id == build.paths(built).build_id
    assert DataStore(built).build_id == build.paths(built).build_id
    other = build_synthetic("other", last=date(2023, 10, 24), with_holdout=False)
    assert build.paths(other).build_id != build.paths(built).build_id


def test_audit_runs_and_reports_full_matching_on_the_synthetic_data(built):
    from kinn.data import audit

    result = audit.run(built)
    assert result["files"]["minute_files_converted"] == len(syn.sessions())
    assert result["match_by_year"][0]["matched_pct"] == 100.0
    assert result["early_closes"] == [str(syn.EARLY_CLOSE_DAY)]
    assert result["symbol_conflicts"]["overlapping_pairs"] == 0
    text = audit.render(result)
    assert "Identity match" in text and "POISON" not in text
