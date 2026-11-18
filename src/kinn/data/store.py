"""The only way to read processed data. Every read passes the holdout seal."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import HOLDOUT_START, Settings
from kinn.data import inputs as inputs_module
from kinn.data import seal
from kinn.data.sharadar import SF1_DIMENSIONS, SF1_FIELDS
from kinn.data.universe import Universe

CURRENT_NAME = "CURRENT"
# A company whose previous bar is older than this has a hole in its history (a halt, or a
# ticker change dated wrongly at the source). Its "previous close" is then stale, so for daily
# research it has no return that day and is not in any universe.
MAX_GAP_DAYS = 10


class DataStore:
    def __init__(
        self,
        settings: Settings,
        *,
        build_id: str | None = None,
        unseal: bool = False,
        inputs: Mapping[str, str] | None = None,
    ):
        # ``inputs`` pins versioned inputs by id ({"form4": "<input_id>"}); an input that is
        # not pinned is read at its current version.
        self._settings = settings
        self._inputs = dict(inputs or {})
        # ``unseal=True`` opens the owner's unsealed build (kinn.data.holdout). It needs the
        # owner's token even to open, and every read of a holdout date is logged.
        if unseal:
            seal.check_range(
                HOLDOUT_START, HOLDOUT_START, source="open the unsealed build", unseal=True,
                log_dir=settings.data_dir,
            )  # fmt: skip
        builds = settings.data_dir / ("holdout/builds" if unseal else "builds")
        if build_id is None:
            pointer = builds / CURRENT_NAME
            if not pointer.exists():
                raise FileNotFoundError(f"no data build yet under {builds}; run `kinn data build`")
            build_id = pointer.read_text().strip()
        self.build_id = build_id
        self.root = builds / build_id
        self.info = json.loads((self.root / "build.json").read_text())
        self.bars_root = settings.data_dir / "bars" / self.info["bars_id"]
        self.bars_roots = [self.bars_root]
        if unseal:
            self.bars_roots.append(
                settings.data_dir / "holdout" / "bars" / self.info["sealed_bars_id"]
            )
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

    def _bars(self, kind: str) -> str:
        """SQL list of the Parquet files of ``kind`` ('calendar' or 'daily') in every bars root."""
        return "[" + ", ".join(f"'{root}/{kind}/*.parquet'" for root in self.bars_roots) + "]"

    def _date_guard(self, column: str = "date") -> str:
        # Defence in depth: even a mis-built file cannot leak holdout rows through a query.
        return "true" if self._unseal else f"{column} < DATE '{HOLDOUT_START.isoformat()}'"

    # -- tables --------------------------------------------------------------------------
    def panel_columns(self) -> list[str]:
        """Column names of this build's panel (older builds have fewer)."""
        first = sorted((self.root / "panel").glob("*.parquet"))[0]
        return pq.read_schema(first).names

    def table_path(self, name: str) -> Path:
        """Path of a small undated table: security_master, symbol_history, splits."""
        path = self.root / "master" / f"{name}.parquet"
        if not path.exists():
            raise KeyError(name)
        return path

    def calendar(self, start: date, end: date) -> pa.Table:
        self._check(start, end, "calendar")
        return self._query(
            f"""select * from read_parquet({self._bars("calendar")})
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

    def universe_members(self, start: date, end: date, universe: Universe) -> list[int]:
        """Every company in ``universe`` on at least one session from ``start`` to ``end``."""
        self._check(start, end, "panel")
        table = self._query(
            f"""select distinct permaticker from read_parquet('{self.root}/panel/*.parquet')
                where date between ? and ? and {self._date_guard()} and {universe.where()}
                order by 1""",
            [start, end],
        )
        return table["permaticker"].to_pylist()

    def panel_of(
        self, start: date, end: date, *, permatickers: list[int], columns: str
    ) -> pa.Table:
        """The panel's rows for the given companies only (what the Lab loads)."""
        self._check(start, end, "panel")
        return self._query(
            f"""select {columns} from read_parquet('{self.root}/panel/*.parquet')
                where date between ? and ? and {self._date_guard()}
                  and permaticker in (select unnest(?)) order by date, permaticker""",
            [start, end, permatickers],
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

    def input_id(self, name: str) -> str:
        """The version of a versioned input this store reads."""
        if name == "form8k":  # read from the data build, so the build pins it
            return inputs_module.form8k_id(self.build_id)
        return self._inputs.get(name) or inputs_module.current(self._settings, name)

    def _filed_since(self, day: date, sessions: int) -> date:
        """The first filing date a strategy asking for ``sessions`` sessions sees on ``day``:
        the ``sessions``-th session before it (filings dated then became usable the session
        after)."""
        earlier = [
            d for d in self.sessions(day - timedelta(days=14 + 3 * sessions), day) if d < day
        ]
        return earlier[-sessions] if len(earlier) >= sessions else day - timedelta(days=7)

    def form8k(self, day: date, *, sessions: int = 1) -> pa.Table:
        """8-K filings a strategy may use on session ``day``: one row per company and filing
        date (``permaticker``, ``filed``, ``eventcodes`` as Sharadar writes them, "22|91").

        The rule is the one :meth:`form4` follows: a filing is available from the first
        session after its filing date, so this returns filings dated before ``day`` and on or
        after the ``sessions``-th session before it. Nothing filed on ``day`` or later is ever
        returned, whatever time of day it was filed.
        """
        self._check(day, day, "form8k")
        return self._query(
            f"""select s.permaticker, e.date as filed, e.eventcodes
                from '{self.root}/sharadar/events.parquet' e
                join '{self.root}/master/security_master.parquet' s using (ticker)
                where e.date >= ? and e.date < ? and {self._date_guard("e.date")}
                order by e.date, s.permaticker""",
            [self._filed_since(day, sessions), day],
        )

    def form8k_info(self) -> dict:
        """What a run records about the form8k input: its id and version, and what the build
        holds (filings before the seal only)."""
        rows, first, last = (
            self._query(
                f"""select count(*), min(e.date)::varchar, max(e.date)::varchar
                from '{self.root}/sharadar/events.parquet' e
                join '{self.root}/master/security_master.parquet' s using (ticker)
                where {self._date_guard("e.date")}"""
            )
            .to_pylist()[0]
            .values()
        )
        return {
            "input": "form8k", "input_id": self.input_id("form8k"),
            "version": inputs_module.FORM8K_VERSION, "data_build_id": self.build_id,
            "rows": rows, "first_filed": first, "last_filed": last,
        }  # fmt: skip

    def form4(self, day: date, *, sessions: int = 1) -> pa.Table:
        """Insider (Form 4) transactions a strategy may use on session ``day``.

        A filing is available from the first session after its filing date, so this returns
        filings dated before ``day`` and on or after the ``sessions``-th session before it:
        ``sessions=1`` is what became available this morning. Nothing filed on ``day`` or
        later is ever returned.
        """
        self._check(day, day, "form4")
        input_id = self.input_id("form4")
        meta = inputs_module.info(self._settings, "form4", input_id)
        if day > date.fromisoformat(meta["last_filed"]) + timedelta(days=7):
            raise inputs_module.InputError(
                f"the form4 input {input_id} ends at {meta['last_filed']}; it has nothing to "
                f"say about {day}. End the run earlier or build a newer input."
            )
        first = self._filed_since(day, sessions)
        path = inputs_module.root(self._settings, "form4") / input_id / "transactions.parquet"
        return self._query(
            f"""select * from '{path}'
                where filed >= ? and filed < ? and {self._date_guard("filed")}
                order by filed, accession, transaction_code, acquired""",
            [first, day],
        )

    def minute(
        self, day: date, *, symbols: list[str] | None = None, columns: str = "*"
    ) -> pa.Table:
        self._check(day, day, "minute")
        name = Path("minute") / f"year={day.year}" / f"{day.isoformat()}.parquet"
        path = next((r / name for r in self.bars_roots if (r / name).exists()), None)
        if path is None:
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
            f"""select * from read_parquet({self._bars("daily")})
                where date between ? and ? and {self._date_guard()}
                  and symbol in (select unnest(?)) order by date, symbol""",
            [start, end, symbols],
        )

    # -- daily research (multi-day books) ------------------------------------------------
    def _eligibility(self, where: str, top_by_marketcap: int | None) -> str:
        """SQL for the panel with an ``eligible`` column: the universe filter and, optionally,
        the largest ``top_by_marketcap`` names by the previous session's market cap."""
        top = "true" if top_by_marketcap is None else f"rk <= {int(top_by_marketcap)}"
        return f"""with base as (
                select date, permaticker, open, close, split_ratio, dollar_volume, adv20_prev,
                       marketcap_prev, fresh, case when fresh then prev_close end as prev_close,
                       coalesce(({where}), false) and fresh as ok
                from (select *, coalesce(date - prev_date <= {MAX_GAP_DAYS}, false) as fresh
                      from read_parquet('{self.root}/panel/*.parquet')
                      where date between ? and ? and {self._date_guard()})),
            ranked as (
                select *, row_number() over (partition by date, ok
                    order by marketcap_prev desc nulls last, permaticker) as rk from base)
            select * exclude (ok, rk, fresh), (ok and {top}) as eligible from ranked"""

    def daily_candidates(
        self, start: date, end: date, *, universe: Universe, top_by_marketcap: int | None = None
    ) -> list[int]:
        """Companies in the universe on at least one session of the period."""
        self._check(start, end, "panel")
        sql = self._eligibility(universe.where(), top_by_marketcap)
        table = self._query(
            f"select distinct permaticker from ({sql}) where eligible order by 1", [start, end]
        )
        return table["permaticker"].to_pylist()

    def daily_long(
        self,
        start: date,
        end: date,
        *,
        universe: Universe,
        permatickers: list[int],
        top_by_marketcap: int | None = None,
    ) -> pa.Table:
        """Panel rows of the given companies, with their eligibility on each session."""
        self._check(start, end, "panel")
        sql = self._eligibility(universe.where(), top_by_marketcap)
        return self._query(
            f"select * from ({sql}) where permaticker in (select unnest(?))",
            [start, end, permatickers],
        )

    def dividends(self, start: date, end: date) -> pa.Table:
        """Cash per share by company and ex-date: dividends and the cash value of spinoffs."""
        self._check(start, end, "dividends")
        return self._query(
            f"""select permaticker, date, amount from '{self.root}/master/dividends.parquet'
                where date between ? and ? and {self._date_guard()}""",
            [start, end],
        )

    def securities(self) -> pa.Table:
        return self._query(f"select * from '{self.root}/master/security_master.parquet'")

    def last_symbols(self, start: date, end: date, permatickers: list[int]) -> dict[int, str]:
        self._check(start, end, "panel")
        table = self._query(
            f"""select permaticker, arg_max(symbol, date) as symbol
                from read_parquet('{self.root}/panel/*.parquet')
                where date between ? and ? and {self._date_guard()}
                  and permaticker in (select unnest(?)) group by 1""",
            [start, end, permatickers],
        )
        return dict(zip(table["permaticker"].to_pylist(), table["symbol"].to_pylist(), strict=True))

    def fundamentals(
        self, end: date, *, fields: tuple[str, ...], dimension: str = "ART"
    ) -> pa.Table:
        """As-reported fundamentals filed up to ``end``: (permaticker, datekey, fields...).

        ``datekey`` is the filing date. A value is usable from the session *after* it."""
        self._check(end, end, "fundamentals")
        unknown = set(fields) - set(SF1_FIELDS)
        if unknown or dimension not in SF1_DIMENSIONS:
            raise KeyError(f"unknown fundamentals: {sorted(unknown)} / {dimension}")
        columns = ", ".join(f"f.{name}" for name in fields)
        return self._query(
            f"""select s.permaticker, f.datekey, {columns}
                from '{self.root}/sharadar/sf1.parquet' f
                join '{self.root}/master/security_master.parquet' s using (ticker)
                where f.dimension = ? and f.datekey <= ? and {self._date_guard("f.datekey")}
                order by f.datekey, f.calendardate""",
            [dimension, end],
        )
