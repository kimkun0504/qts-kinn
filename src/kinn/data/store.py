"""The only way to read processed data. Every read passes the holdout seal."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb
import pyarrow as pa

from kinn.core.settings import HOLDOUT_START, Settings
from kinn.data import seal
from kinn.data.universe import Universe

CURRENT_NAME = "CURRENT"


class DataStore:
    def __init__(self, settings: Settings, *, build_id: str | None = None, unseal: bool = False):
        builds = settings.data_dir / "builds"
        if build_id is None:
            pointer = builds / CURRENT_NAME
            if not pointer.exists():
                raise FileNotFoundError(f"no data build yet under {builds}; run `kinn data build`")
            build_id = pointer.read_text().strip()
        self.build_id = build_id
        self.root = builds / build_id
        self.info = json.loads((self.root / "build.json").read_text())
        self.bars_root = settings.data_dir / "bars" / self.info["bars_id"]
        self._unseal = unseal
        self._log_dir = settings.data_dir

    # -- helpers -------------------------------------------------------------------------
    def _check(self, start: date, end: date, source: str) -> None:
        seal.check_range(start, end, source=source, unseal=self._unseal, log_dir=self._log_dir)

    def _query(self, sql: str, params: list | None = None) -> pa.Table:
        con = duckdb.connect()
        try:
            return con.sql(sql, params=params or []).to_arrow_table()
        finally:
            con.close()

    def _date_guard(self, column: str = "date") -> str:
        # Defence in depth: even a mis-built file cannot leak holdout rows through a query.
        return "true" if self._unseal else f"{column} < DATE '{HOLDOUT_START.isoformat()}'"

    # -- tables --------------------------------------------------------------------------
    def table_path(self, name: str) -> Path:
        """Path of a small undated table: security_master, symbol_history, splits."""
        path = self.root / "master" / f"{name}.parquet"
        if not path.exists():
            raise KeyError(name)
        return path

    def calendar(self, start: date, end: date) -> pa.Table:
        self._check(start, end, "calendar")
        return self._query(
            f"""select * from read_parquet('{self.bars_root}/calendar/*.parquet')
                where date between ? and ? and {self._date_guard()} order by date""",
            [start, end],
        )

    def sessions(self, start: date, end: date) -> list[date]:
        return self.calendar(start, end)["date"].to_pylist()

    def panel(
        self, start: date, end: date, *, universe: Universe | None = None, columns: str = "*"
    ) -> pa.Table:
        self._check(start, end, "panel")
        where = universe.where() if universe else "true"
        return self._query(
            f"""select {columns} from read_parquet('{self.root}/panel/*.parquet')
                where date between ? and ? and {self._date_guard()} and {where}
                order by date, symbol""",
            [start, end],
        )

    def events(self, start: date, end: date) -> pa.Table:
        """Sharadar EVENTS (8-K event codes) by company and filing date."""
        self._check(start, end, "events")
        return self._query(
            f"""select s.permaticker, e.date, e.eventcodes
                from '{self.root}/sharadar/events.parquet' e
                join '{self.root}/master/security_master.parquet' s using (ticker)
                where e.date between ? and ? and {self._date_guard("e.date")}
                order by e.date, s.permaticker""",
            [start, end],
        )

    def minute(
        self, day: date, *, symbols: list[str] | None = None, columns: str = "*"
    ) -> pa.Table:
        self._check(day, day, "minute")
        path = self.bars_root / "minute" / f"year={day.year}" / f"{day.isoformat()}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"no minute bars for {day} (not a session, or not built)")
        if symbols is None:
            return self._query(f"select {columns} from '{path}' order by symbol, bar_start")
        return self._query(
            f"select {columns} from '{path}' where symbol in (select unnest(?)) "
            "order by symbol, bar_start",
            [symbols],
        )

    def daily(self, start: date, end: date, *, symbols: list[str]) -> pa.Table:
        """Raw daily bars by symbol (for ETFs and other names outside the security master)."""
        self._check(start, end, "daily")
        return self._query(
            f"""select * from read_parquet('{self.bars_root}/daily/*.parquet')
                where date between ? and ? and {self._date_guard()}
                  and symbol in (select unnest(?)) order by date, symbol""",
            [start, end, symbols],
        )
