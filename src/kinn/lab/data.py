"""The data an algorithm sees: wide tables (sessions × stocks) read through the sealed store.

Everything comes from :class:`kinn.data.store.DataStore`, so no date on or after the holdout
start can be read. Prices and the universe are loaded when the run starts; trade counts, filing
days and fundamentals load the first time the algorithm asks for them.

Every derived field depends only on its own row and earlier rows (``adj_close`` is anchored at
each stock's first price in the window, not its last), so the lookahead test can cut the data
at any session and get the same values up to the cut.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc

from kinn.data.store import MAX_GAP_DAYS, DataStore
from kinn.data.universe import Universe
from kinn.lab.settings import FIRST_DAY, Settings

LAST_DATA_DAY = date(2023, 11, 8)  # the day before the holdout starts
WARM_UP_DAYS = 400  # calendar days loaded before the period, so a 252-session window is full

PRICE_FIELDS = ("open", "high", "low", "close", "volume", "dollar_volume")
FUNDAMENTALS = {
    "revenue": "revenueusd", "gross_profit": "gp", "operating_income": "opinc",
    "net_income": "netinccmnusd", "operating_cash_flow": "ncfo", "capex": "capex",
    "free_cash_flow": "fcf", "eps": "epsusd", "dividends_per_share": "dps",
    "equity": "equityusd", "assets": "assets", "liabilities": "liabilities", "debt": "debtusd",
    "cash": "cashnequsd", "shares": "sharesbas", "book_value_per_share": "bvps",
}  # fmt: skip

FIELDS: dict[str, tuple[str, str]] = {
    "open": ("The day's opening price, as traded that day", "that day"),
    "high": ("The day's high", "that day"),
    "low": ("The day's low", "that day"),
    "close": ("The day's closing price, as traded that day", "that day"),
    "adj_close": (
        "Close adjusted for splits (anchored at the stock's first price in the run); "
        "use it for returns across days",
        "that day",
    ),  # fmt: skip
    "returns": ("Close-to-close return, split-adjusted", "that day"),
    "volume": ("Shares traded", "that day"),
    "dollar_volume": ("Close × volume", "that day"),
    "transactions": ("Number of trades (Massive day bars)", "that day"),
    "trade_size": ("Shares per trade: volume ÷ transactions", "that day"),
    "market_cap": ("Market value at the previous close", "before the open"),
    "adv20": ("Median dollar volume of the previous 20 sessions", "before the open"),
    "eligible": ("In the universe chosen in the settings", "before the open"),
    "earnings": ("A results 8-K (item 2.02) was filed that day", "that day"),
    "filing": ("Any 8-K was filed that day", "that day"),
    **{
        name: (
            f"As reported ({source}), trailing twelve months or latest quarter",
            "the session after filing",
        )
        for name, source in FUNDAMENTALS.items()
    },  # fmt: skip
    "sector": ("Sector (one value per stock; a pandas Series)", "static"),
    "industry": ("Industry (one value per stock; a pandas Series)", "static"),
    "exchange": ("Exchange (one value per stock; a pandas Series)", "static"),
    "name": ("Company name (one value per stock; a pandas Series)", "static"),
    "spy": ("SPY's close (a pandas Series by session)", "that day"),
    "universe_return": (
        "Equal-weight average daily return of the eligible stocks (a Series)",
        "that day",
    ),  # fmt: skip
}
STATIC = ("sector", "industry", "exchange", "name")
SERIES = ("spy", "universe_return")
BLANK_CHECK_SIC = "6770"
BYTES_PER_CELL = 42  # the arrays a run holds before any field the algorithm asks for
CACHE_SCHEMA = "lab-prices-1"
CACHED = ("open", "high", "low", "close", "volume", "dollar_volume", "adv20", "market_cap",
          "returns", "adj_close", "eligible")  # fmt: skip
DEFAULT_CACHE_GB = 6.0
# Fields read only when the code asks for them, kept in the cache entry once read; a group is
# loaded (and kept) together.
_GROUPS = {"transactions": ("transactions", "trade_size"),
           "trade_size": ("transactions", "trade_size"),
           "earnings": ("earnings", "filing"), "filing": ("earnings", "filing")}  # fmt: skip
_LOADED_ON_ASK = {"transactions", "trade_size", "earnings", "filing", "spy", *FUNDAMENTALS}
MEMORY_SHARE = 0.6  # refuse a run whose base arrays need more than this share of the RAM


class DataError(ValueError):
    """The data cannot be loaded as asked, with a message for the page."""


def physical_memory() -> int | None:
    """Bytes of RAM on this machine, or None where the system will not say."""
    try:
        return int(os.sysconf("SC_PHYS_PAGES")) * int(os.sysconf("SC_PAGE_SIZE"))
    except (ValueError, OSError, AttributeError):
        return None


def _read_only(values: np.ndarray) -> np.ndarray:
    values.flags.writeable = False
    return values


def cache_limit() -> float:
    """Bytes the price cache may hold (``KINN_LAB_CACHE_GB``, default 6)."""
    try:
        gigabytes = float(os.environ.get("KINN_LAB_CACHE_GB", DEFAULT_CACHE_GB))
    except ValueError:
        gigabytes = DEFAULT_CACHE_GB
    return max(gigabytes, 0.0) * 1e9


def _evict(folder: Path, keep: str) -> None:
    """Drop the least recently used entries until the cache fits its limit."""
    entries = []
    for entry in folder.iterdir():
        meta = entry / "meta.json"
        if entry.is_dir() and meta.exists():
            size = sum(f.stat().st_size for f in entry.iterdir())
            entries.append((meta.stat().st_mtime, entry, size))
    total = sum(size for _, _, size in entries)
    for _, entry, size in sorted(entries, key=lambda e: e[0]):
        if total <= cache_limit():
            break
        if entry.name != keep:
            shutil.rmtree(entry, ignore_errors=True)
            total -= size


def catalog() -> list[dict]:
    return [{"name": n, "description": d, "known": k} for n, (d, k) in FIELDS.items()]


class LabData:
    """The fields of one run, as pandas objects. Use ``data.close`` and so on."""

    def __init__(self, store: DataStore, settings: Settings,
                 progress: Callable[[str, float], None] | None = None,
                 cache_dir: Path | None = None) -> None:  # fmt: skip
        self._store = store
        self._cache_dir = cache_dir
        self.cache_state = "off"  # "hit", "miss" or "off": where the prices came from
        self._settings = settings
        self._progress = progress or (lambda stage, pct: None)
        self._arrays: dict[str, np.ndarray] = {}
        self._frames: dict[str, pd.DataFrame | pd.Series] = {}  # one shared object per field
        self._rows: int | None = None  # set on a cut-off view
        self.not_found: list[str] = []
        first, last_entry = settings.window()
        span = int(settings.exit.hold_days * 1.6) + 20
        self.load_start = max(first - timedelta(days=WARM_UP_DAYS), FIRST_DAY)
        self.load_end = min(last_entry + timedelta(days=span), LAST_DATA_DAY)
        sessions = store.sessions(self.load_start, self.load_end)
        if not sessions:
            raise DataError("No sessions in this period.")
        self.sessions = np.array(sessions, dtype="datetime64[D]")
        self.index = pd.DatetimeIndex(self.sessions, name="date")
        # Signals may fire from the first session of the period to the last entry day's eve.
        self.first_row = int(np.searchsorted(self.sessions, np.datetime64(first)))
        last = int(np.searchsorted(self.sessions, np.datetime64(last_entry), "right"))
        self.last_signal_row = last - 2  # its entry, the next session, is the last entry day
        self._load_universe()

    # -- loading ----------------------------------------------------------------------------
    def _universe(self) -> Universe:
        u = self._settings.universe
        return Universe(
            name="lab", min_prev_close=u.min_price, min_adv20=u.min_dollar_volume,
            min_marketcap=u.min_market_cap, max_marketcap=u.max_market_cap,
        )  # fmt: skip

    def _load_universe(self) -> None:
        self._progress("Finding the stocks in the universe", 0.02)
        first, last_entry = self._settings.window()
        members = self._store.universe_members(first, last_entry, self._universe())
        master = self._store.securities()
        info = {
            row["permaticker"]: row
            for row in master.select(
                ["permaticker", "ticker", "name", "sector", "industry", "exchange", "siccode"]
            ).to_pylist()  # fmt: skip
        }
        if self._settings.universe.exclude_blank_checks:
            members = [p for p in members
                       if (info.get(p, {}).get("siccode") or "") != BLANK_CHECK_SIC]  # fmt: skip
        named = set(self._settings.universe.tickers)
        if named:
            members = [p for p in members if (info.get(p, {}).get("ticker") or "") in named]
            found = {info[p]["ticker"] for p in members}
            self.not_found = sorted(named - found)
        if not members:
            raise DataError(
                "None of these tickers is in the universe in this period. Check the tickers, "
                "or loosen the universe's other filters."
                if named
                else "No stock is in this universe in this period. Loosen the universe."
            )
        self.permatickers = np.array(sorted(members), dtype=np.int64)
        self._check_memory()
        tickers = [str((info.get(int(p)) or {}).get("ticker") or p) for p in self.permatickers]
        seen: dict[str, int] = {}
        for ticker in tickers:
            seen[ticker] = seen.get(ticker, 0) + 1
        # Tickers are unique in the master; if one ever is not, the columns still are.
        pairs = zip(tickers, self.permatickers, strict=True)
        tickers = [t if seen[t] == 1 else f"{t}.{p}" for t, p in pairs]
        self.columns = pd.Index(tickers, name="stock")
        self._static = {
            key: pd.Series(
                [(info.get(int(p)) or {}).get(key) for p in self.permatickers],
                index=self.columns,
                name=key,
            )  # fmt: skip
            for key in STATIC
        }
        self._load_prices()

    def _check_memory(self) -> None:
        cells = len(self.sessions) * len(self.permatickers)
        need = cells * BYTES_PER_CELL
        ram = physical_memory()
        if ram and need > MEMORY_SHARE * ram:
            raise DataError(
                f"This run needs about {need / 1e9:.1f} GB for prices alone "
                f"({len(self.permatickers):,} stocks × {len(self.sessions):,} sessions), more than "
                f"this machine can spare ({ram / 1e9:.0f} GB of RAM). Use a shorter period or "
                "raise the universe's minimum market cap or dollar volume."
            )  # fmt: skip

    def _empty(self, dtype=np.float32, fill=np.nan) -> np.ndarray:
        return np.full((len(self.sessions), len(self.permatickers)), fill, dtype=dtype)

    def _cells(self, table: pa.Table) -> tuple[np.ndarray, np.ndarray]:
        days = table["date"].to_numpy().astype("datetime64[D]")
        rows = np.searchsorted(self.sessions, days)
        cols = np.searchsorted(self.permatickers, table["permaticker"].to_numpy())
        return rows, cols

    def _load_prices(self) -> None:
        key = self._cache_key()
        arrays = self._from_cache(key) if key else None
        if arrays is None:
            arrays = self._read_prices()
            if key:
                self._to_cache(key, arrays)
        # The universe opens with the period and closes the day after the last signal.
        eligible = np.array(arrays.pop("eligible"), dtype=bool, copy=True)
        eligible[: self.first_row] = False
        eligible[self.last_signal_row + 2 :] = False
        for name, values in arrays.items():
            self._arrays[name] = _read_only(values)
        self._arrays["eligible"] = _read_only(eligible)
        self._progress("Prices loaded", 0.3)

    def _read_prices(self) -> dict[str, np.ndarray]:
        """The price arrays from the store, the universe flag not yet cut to the period."""
        names = ("open", "high", "low", "close", "volume", "dollar_volume", "adv20_prev",
                 "marketcap_prev")  # fmt: skip
        arrays = {name: self._empty() for name in names}
        returns = self._empty()
        eligible = self._empty(bool, False)
        where = self._universe().where()
        years = range(self.load_start.year, self.load_end.year + 1)
        for i, year in enumerate(years):
            self._progress(f"Loading prices for {year}", 0.03 + 0.25 * i / len(years))
            start = max(date(year, 1, 1), self.load_start)
            end = min(date(year, 12, 31), self.load_end)
            table = self._store.panel_of(
                start, end, permatickers=self.permatickers.tolist(),
                columns=f"date, permaticker, {', '.join(names)}, prev_close, "
                        f"coalesce(({where}) and date - prev_date <= {MAX_GAP_DAYS}, false) "
                        "as eligible",
            )  # fmt: skip
            if not table.num_rows:
                continue
            rows, cols = self._cells(table)
            for name in names:
                values = table[name].to_numpy(zero_copy_only=False)
                arrays[name][rows, cols] = values.astype(np.float32)
            close = table["close"].to_numpy(zero_copy_only=False).astype(np.float64)
            prev = table["prev_close"].to_numpy(zero_copy_only=False).astype(np.float64)
            with np.errstate(divide="ignore", invalid="ignore"):
                change = np.where((prev > 0) & (close > 0), close / prev - 1, np.nan)
            returns[rows, cols] = change.astype(np.float32)
            eligible[rows, cols] = table["eligible"].to_numpy(zero_copy_only=False).astype(bool)
            del table
        out = {name: arrays.pop(name) for name in PRICE_FIELDS}
        out["adv20"] = arrays.pop("adv20_prev")
        out["market_cap"] = arrays.pop("marketcap_prev")
        out["returns"] = returns
        out["adj_close"] = self._adjusted(out["close"], returns)
        out["eligible"] = eligible
        return out

    # -- the price cache: the same universe and window loads from disk the next time ---------
    def _cache_key(self) -> str | None:
        if "_key" in self.__dict__:
            return self.__dict__["_key"]
        self.__dict__["_key"] = key = self._make_key()
        return key

    def _make_key(self) -> str | None:
        build = getattr(self._store, "build_id", None)
        if self._cache_dir is None or not build:
            return None
        ident = {
            "schema": CACHE_SCHEMA, "build": str(build), "where": self._universe().where(),
            "gap": MAX_GAP_DAYS, "start": str(self.load_start), "end": str(self.load_end),
            "stocks": hashlib.sha256(self.permatickers.tobytes()).hexdigest(),
            "sessions": hashlib.sha256(self.sessions.astype("int64").tobytes()).hexdigest(),
        }  # fmt: skip
        return hashlib.sha256(json.dumps(ident, sort_keys=True).encode()).hexdigest()[:24]

    def _from_cache(self, key: str) -> dict[str, np.ndarray] | None:
        folder = self._cache_dir / key
        if not (folder / "meta.json").exists():
            return None
        shape = (len(self.sessions), len(self.permatickers))
        try:
            arrays = {name: np.load(folder / f"{name}.npy", mmap_mode="r") for name in CACHED}
            if any(a.shape != shape for a in arrays.values()):
                raise ValueError("shape")
            os.utime(folder / "meta.json")  # most recently used
        except (OSError, ValueError):
            shutil.rmtree(folder, ignore_errors=True)  # damaged: read it again from the store
            return None
        self._progress("Prices loaded from the cache", 0.28)
        self.cache_state = "hit"
        return arrays

    def _to_cache(self, key: str, arrays: dict[str, np.ndarray]) -> None:
        """Keep the arrays for the next run. A cache that cannot be written never fails a run."""
        self.cache_state = "miss"
        folder = self._cache_dir / key
        tmp = self._cache_dir / f".{key}.{os.getpid()}.tmp"
        try:
            tmp.mkdir(parents=True, exist_ok=False)
            for name in CACHED:
                np.save(tmp / f"{name}.npy", arrays[name], allow_pickle=False)
            meta = {"schema": CACHE_SCHEMA, "shape": list(arrays["close"].shape),
                    "bytes": sum(int(arrays[n].nbytes) for n in CACHED),
                    "made": datetime.now(UTC).isoformat()}  # fmt: skip
            (tmp / "meta.json").write_text(json.dumps(meta))
            try:
                os.replace(tmp, folder)
            except OSError:  # another run made it first
                shutil.rmtree(tmp, ignore_errors=True)
            _evict(self._cache_dir, keep=key)
        except OSError:
            shutil.rmtree(tmp, ignore_errors=True)
            self.cache_state = "unavailable"

    @staticmethod
    def _adjusted(close: np.ndarray, returns: np.ndarray, block: int = 512) -> np.ndarray:
        """Split-adjusted closes, anchored at each stock's first close in the window, so no row
        depends on a later one. Worked in blocks of columns to bound the float64 scratch."""
        out = np.full(close.shape, np.nan, dtype=np.float32)
        for lo in range(0, close.shape[1], block):
            hi = min(lo + block, close.shape[1])
            c = close[:, lo:hi]
            cum = np.cumsum(np.log1p(np.nan_to_num(returns[:, lo:hi], nan=0.0), dtype=np.float64),
                            axis=0)  # fmt: skip
            has = np.isfinite(c)
            firsts = np.where(has.any(axis=0), has.argmax(axis=0), 0)
            cols = np.arange(hi - lo)
            anchor = c[firsts, cols].astype(np.float64) / np.exp(cum[firsts, cols])
            out[:, lo:hi] = np.where(has, np.exp(cum) * anchor, np.nan)
        return out

    def _load_trades(self) -> None:
        """Trade counts from the vendor's day bars, matched to each company by the symbol it
        traded under that day."""
        self._progress("Loading trade counts", 0.32)
        transactions = self._empty()
        perms = self.permatickers.tolist()
        for year in range(self.load_start.year, self.load_end.year + 1):
            start = max(date(year, 1, 1), self.load_start)
            end = min(date(year, 12, 31), self.load_end)
            names = self._store.panel_of(start, end, permatickers=perms,
                                         columns="date, permaticker, symbol")  # fmt: skip
            if not names.num_rows:
                continue
            symbols = pc.unique(names["symbol"]).to_pylist()
            bars = self._store.daily(start, end, symbols=symbols)
            bars = bars.select(["date", "symbol", "transactions"])
            joined = names.join(bars, keys=["date", "symbol"], join_type="inner")
            joined = joined.filter(pc.greater(joined["transactions"], 0))
            if joined.num_rows:
                rows, cols = self._cells(joined)
                transactions[rows, cols] = joined["transactions"].to_numpy(zero_copy_only=False)
        volume = self._arrays["volume"]
        with np.errstate(divide="ignore", invalid="ignore"):
            size = np.where(transactions > 0, volume / transactions, np.nan)
        self._arrays["transactions"] = _read_only(transactions)
        self._arrays["trade_size"] = _read_only(size.astype(np.float32))

    def _load_events(self) -> None:
        self._progress("Loading 8-K filing days", 0.33)
        table = self._store.events(self.load_start, self.load_end)
        keep = pc.is_in(table["permaticker"], value_set=pa.array(self.permatickers))
        table = table.filter(keep)
        earnings, filing = self._empty(bool, False), self._empty(bool, False)
        if table.num_rows:
            days = table["date"].to_numpy().astype("datetime64[D]")
            rows = np.searchsorted(self.sessions, days)  # a filing on a holiday counts next session
            ok = rows < len(self.sessions)
            cols = np.searchsorted(self.permatickers, table["permaticker"].to_numpy())
            codes = table["eventcodes"].to_pylist()
            results = np.array(["22" in (c or "").split("|") for c in codes])
            filing[rows[ok], cols[ok]] = True
            earnings[rows[ok & results], cols[ok & results]] = True
        self._arrays["earnings"] = _read_only(earnings)
        self._arrays["filing"] = _read_only(filing)

    def _load_fundamental(self, name: str) -> None:
        """One as-reported field, usable from the session after its filing date."""
        self._progress(f"Loading {name}", 0.34)
        source = FUNDAMENTALS[name]
        table = self._store.fundamentals(self.load_end, fields=(source,))
        keep = pc.is_in(table["permaticker"], value_set=pa.array(self.permatickers))
        table = table.filter(keep)
        days = table["datekey"].to_numpy().astype("datetime64[D]")
        rows = np.searchsorted(self.sessions, days, side="right")  # usable the session after
        ok = rows < len(self.sessions)
        cols = np.searchsorted(self.permatickers, table["permaticker"].to_numpy())
        values = table[source].to_numpy(zero_copy_only=False).astype(np.float32)
        grid = self._empty()
        grid[rows[ok], cols[ok]] = values[ok]  # rows come ordered by filing date: last wins
        filled = pd.DataFrame(grid, copy=False).ffill().to_numpy(dtype=np.float32)
        self._arrays[name] = _read_only(np.ascontiguousarray(filled))

    def _load_spy(self) -> np.ndarray:
        table = self._store.daily(self.load_start, self.load_end, symbols=["SPY"])
        spy = np.full(len(self.sessions), np.nan, dtype=np.float32)
        if table.num_rows:
            rows = np.searchsorted(self.sessions, table["date"].to_numpy().astype("datetime64[D]"))
            spy[rows] = table["close"].to_numpy(zero_copy_only=False)
        return spy

    def array(self, name: str) -> np.ndarray:
        """The full array of a field (no cut-off), loading it if needed."""
        if name not in self._arrays:
            group = _GROUPS.get(name, (name,))
            if name in _LOADED_ON_ASK and self._cached_fields(group):
                pass
            elif name in ("transactions", "trade_size"):
                self._load_trades()
            elif name in ("earnings", "filing"):
                self._load_events()
            elif name in FUNDAMENTALS:
                self._load_fundamental(name)
            elif name == "spy":
                self._arrays["spy"] = _read_only(self._load_spy())
            elif name == "universe_intraday":
                with np.errstate(divide="ignore", invalid="ignore"):
                    day = self._arrays["close"] / self._arrays["open"] - 1
                day = np.where(self._arrays["eligible"] & np.isfinite(day), day, np.nan)
                counts = np.isfinite(day).sum(axis=1)
                mean = np.where(counts > 0, np.nansum(day, axis=1) / np.maximum(counts, 1), np.nan)
                self._arrays["universe_intraday"] = _read_only(mean.astype(np.float32))
            elif name == "universe_return":
                returns = np.where(self._arrays["eligible"], self._arrays["returns"], np.nan)
                with np.errstate(invalid="ignore"):
                    counts = np.isfinite(returns).sum(axis=1)
                    total = np.nansum(returns, axis=1)
                mean = np.where(counts > 0, total / np.maximum(counts, 1), np.nan)
                self._arrays["universe_return"] = _read_only(mean.astype(np.float32))
            else:
                raise AttributeError(name)
            if name in _LOADED_ON_ASK:
                self._keep_fields(group)
        return self._arrays[name]

    def _entry(self) -> Path | None:
        """This run's folder in the price cache, once it exists."""
        key = self._cache_key()
        folder = self._cache_dir / key if key else None
        return folder if folder is not None and (folder / "meta.json").exists() else None

    def _cached_fields(self, names: tuple[str, ...]) -> bool:
        folder = self._entry()
        if folder is None or not all((folder / f"{n}.npy").exists() for n in names):
            return False
        try:
            found = {n: np.load(folder / f"{n}.npy", mmap_mode="r") for n in names}
        except (OSError, ValueError):
            return False
        rows = len(self.sessions)
        if any(a.shape[0] != rows for a in found.values()):
            return False
        for n, values in found.items():
            self._arrays[n] = _read_only(values)
        return True

    def _keep_fields(self, names: tuple[str, ...]) -> None:
        folder = self._entry()
        if folder is None:
            return
        for n in names:
            target = folder / f"{n}.npy"
            if target.exists() or n not in self._arrays:
                continue
            tmp = folder / f".{n}.{os.getpid()}.npy"
            try:
                np.save(tmp, np.asarray(self._arrays[n]), allow_pickle=False)
                os.replace(tmp, target)
            except OSError:
                tmp.unlink(missing_ok=True)
                return

    # -- what the algorithm sees ---------------------------------------------------------------
    def __getattr__(self, name: str):
        if name.startswith("_") or name not in FIELDS:
            raise AttributeError(f"data has no field '{name}'. data.fields() lists them.")
        if name in STATIC:
            return self._static[name].copy()
        # Every call gets its own object over shared, read-only memory. pandas copies on the
        # first write (copy-on-write), so the algorithm can change what it gets without
        # touching the data or another field.
        if name not in self._frames:
            rows = self._rows if self._rows is not None else len(self.sessions)
            values = self.array(name)[:rows]
            if name in SERIES:
                frame = pd.Series(values, index=self.index[:rows], name=name, copy=False)
            else:
                frame = pd.DataFrame(values, index=self.index[:rows], columns=self.columns,
                                     copy=False)  # fmt: skip
            self._frames[name] = frame
        return self._frames[name].copy(deep=False)

    def fields(self) -> list[str]:
        return list(FIELDS)

    @property
    def dates(self) -> pd.DatetimeIndex:
        rows = self._rows if self._rows is not None else len(self.sessions)
        return self.index[:rows]

    @property
    def stocks(self) -> pd.Index:
        return self.columns

    def cut(self, rows: int) -> LabData:
        """A view that ends at row ``rows - 1``: what the algorithm would have seen that day."""
        view = object.__new__(LabData)
        view.__dict__.update(self.__dict__)
        view._rows = rows
        view._frames = {}
        return view

    def __repr__(self) -> str:
        return f"<LabData {len(self.dates)} sessions × {len(self.columns)} stocks>"
