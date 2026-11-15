"""Ingest Sharadar bulk exports. Holdout rows are dropped here and never reach processed data.

The exports are a 2026 snapshot, so some columns describe the future as seen from any research
date (current size buckets, adjusted prices, last price dates after the seal). Those are dropped
or censored here; see docs/data/DATA_NOTES.md.
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from kinn.core.settings import HOLDOUT_START

# table -> (date column, columns kept with their types)
DATED_TABLES: dict[str, tuple[str, dict[str, pa.DataType]]] = {
    "DAILY": ("date", {"ticker": pa.string(), "date": pa.date32(), "marketcap": pa.float64()}),
    "SEP": ("date", {"ticker": pa.string(), "date": pa.date32(), "closeunadj": pa.float64()}),
    "EVENTS": ("date", {"ticker": pa.string(), "date": pa.date32(), "eventcodes": pa.string()}),
    "ACTIONS": (
        "date",
        {
            "date": pa.date32(),
            "action": pa.string(),
            "ticker": pa.string(),
            "name": pa.string(),
            "value": pa.float64(),
            "contraticker": pa.string(),
            "contraname": pa.string(),
        },
    ),
}

# Fundamentals. Only the as-reported dimensions are kept: ARQ (quarterly) and ART (trailing
# twelve months), each row dated by ``datekey``, the day the filing reached the SEC. The "MR"
# dimensions are restated with later knowledge and are dropped here. Price-based columns
# (marketcap, pe, ev ...) are not read: they belong to the snapshot's price history.
SF1_FIELDS = (
    "revenueusd", "gp", "opinc", "ebitusd", "netinccmnusd", "equityusd", "assets",
    "liabilities", "debtusd", "cashnequsd", "ncfo", "capex", "fcf", "sharesbas", "shareswa",
    "epsusd", "bvps", "dps",
)  # fmt: skip
SF1_DIMENSIONS = ("ARQ", "ART")
DATED_TABLES["SF1"] = (
    "datekey",
    {
        "ticker": pa.string(),
        "dimension": pa.string(),
        "calendardate": pa.date32(),
        "datekey": pa.date32(),
        "reportperiod": pa.date32(),
        **dict.fromkeys(SF1_FIELDS, pa.float64()),
    },
)
ROW_FILTERS: dict[str, tuple[str, tuple[str, ...]]] = {"SF1": ("dimension", SF1_DIMENSIONS)}

TICKER_COLUMNS = {
    "table": pa.string(),
    "permaticker": pa.int64(),
    "ticker": pa.string(),
    "name": pa.string(),
    "exchange": pa.string(),
    "category": pa.string(),
    "siccode": pa.string(),
    "sector": pa.string(),
    "industry": pa.string(),
    "currency": pa.string(),
    "location": pa.string(),
    "firstpricedate": pa.date32(),
    "lastpricedate": pa.date32(),
}


def _open_member(zip_path: Path):
    archive = zipfile.ZipFile(zip_path)
    (member,) = archive.namelist()
    return archive.open(member)


def _reader(zip_path: Path, columns: dict[str, pa.DataType]) -> pacsv.CSVStreamingReader:
    return pacsv.open_csv(
        _open_member(zip_path),
        read_options=pacsv.ReadOptions(block_size=32 << 20),
        convert_options=pacsv.ConvertOptions(
            include_columns=list(columns), column_types=columns, strings_can_be_null=True
        ),
    )


def _replace(writer_path: Path, dst: Path) -> None:
    os.replace(writer_path, dst)


def ingest_dated(zip_path: Path, table: str, dst: Path) -> int:
    """Stream ``table`` to Parquet, keeping only rows dated before the holdout. Returns rows."""
    date_column, columns = DATED_TABLES[table]
    seal = pa.scalar(HOLDOUT_START, pa.date32())
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp")
    rows = 0
    writer = None
    for batch in _reader(zip_path, columns):
        kept = pa.Table.from_batches([batch]).filter(pc.less(batch[date_column], seal))
        if table in ROW_FILTERS:
            column, allowed = ROW_FILTERS[table]
            kept = kept.filter(pc.is_in(kept[column], value_set=pa.array(allowed)))
        if writer is None:
            writer = pq.ParquetWriter(tmp, kept.schema, compression="zstd")
        writer.write_table(kept)
        rows += kept.num_rows
    if writer is None:
        raise ValueError(f"{zip_path} is empty")
    writer.close()
    _replace(tmp, dst)
    return rows


def ingest_tickers(zip_path: Path, dst: Path) -> int:
    """The SEP rows of TICKERS, censored at the seal.

    - Names first priced on or after the seal are dropped: they did not exist before it.
    - A last price date on or after the seal becomes null ("still trading at the seal").
    - Snapshot-dated columns (size buckets, related tickers, last update) are not read at all.
    """
    table = _reader(zip_path, TICKER_COLUMNS).read_all()
    seal = pa.scalar(HOLDOUT_START, pa.date32())
    table = table.filter(pc.equal(table["table"], "SEP"))
    table = table.filter(pc.less(table["firstpricedate"], seal))
    last = table["lastpricedate"]
    censored = pc.if_else(pc.less(last, seal), last, pa.scalar(None, pa.date32()))
    table = table.set_column(
        table.schema.get_field_index("lastpricedate"), "lastpricedate", censored
    )
    table = table.drop_columns(["table"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    tmp = dst.with_suffix(".tmp")
    pq.write_table(table, tmp, compression="zstd")
    _replace(tmp, dst)
    return table.num_rows


def read_ticker_changes(zip_path: Path) -> pa.Table:
    """All ``tickerchangefrom`` events as (date, ticker, old_symbol), *including* later ones.

    This is the one place holdout-dated rows are read (decision 0009). Sharadar files a
    company's whole history under its newest ticker, so a rename after the seal is the only way
    to learn which symbol the company traded under before it. The result is used solely by
    ``master.symbol_history`` and nothing dated on or after the seal leaves that function.
    """
    columns = {
        k: DATED_TABLES["ACTIONS"][1][k] for k in ("date", "action", "ticker", "contraticker")
    }
    table = _reader(zip_path, columns).read_all()
    table = table.filter(pc.equal(table["action"], "tickerchangefrom"))
    return table.select(["date", "ticker", "contraticker"]).rename_columns(
        ["date", "ticker", "old_symbol"]
    )
