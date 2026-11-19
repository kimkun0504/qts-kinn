"""The stock page: one company's daily prices up to the seal, its 8-K days, and every trade the
run store, the Lab and the paper ledgers hold in it. Prices are read through the sealed
DataStore, so nothing from the holdout is ever served; trades are read from their own files.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Protocol

import duckdb
import pyarrow as pa

from apps.workbench import ledgers
from kinn import swing_paper
from kinn.core.settings import HOLDOUT_START
from kinn.registry import runs as registry

FIRST = date(2000, 1, 1)
LAST = HOLDOUT_START - timedelta(days=1)
COLUMNS = "date, symbol, open, high, low, close, volume, prev_close, marketcap_prev, adv20_prev"
RESULTS_CODE = "22"
FINANCIALS = (
    "revenueusd", "gp", "opinc", "netinccmnusd", "epsusd", "ncfo", "capex", "fcf",
    "cashnequsd", "debtusd", "equityusd", "sharesbas",
)  # fmt: skip
PERIODS = 40
MAX_TRADES = 1_000


class Store(Protocol):
    build_id: str

    def securities(self) -> pa.Table: ...

    def symbol_history(self) -> pa.Table: ...

    def panel_of(
        self, start: date, end: date, *, permatickers: list[int], columns: str
    ) -> pa.Table: ...

    def events_of(self, start: date, end: date, *, permatickers: list[int]) -> pa.Table: ...

    def fundamentals_of(
        self, permaticker: int, *, fields: tuple[str, ...], dimension: str
    ) -> pa.Table: ...

    def daily(self, start: date, end: date, *, symbols: list[str]) -> pa.Table: ...


@dataclass
class Index:
    companies: dict[int, dict]
    history: dict[int, list[dict]] = field(default_factory=dict)
    by_symbol: dict[str, set[int]] = field(default_factory=dict)

    @classmethod
    def of(cls, master: list[dict], history: list[dict]) -> Index:
        index = cls({row["permaticker"]: row for row in master})
        for row in history:
            if not row.get("symbol") or row["permaticker"] not in index.companies:
                continue
            index.history.setdefault(row["permaticker"], []).append(row)
            index.by_symbol.setdefault(row["symbol"].upper(), set()).add(row["permaticker"])
        for perm, row in index.companies.items():
            if row.get("ticker"):
                index.by_symbol.setdefault(row["ticker"].upper(), set()).add(perm)
        for rows in index.history.values():
            rows.sort(key=lambda r: r["valid_from"] or date.min)
        return index

    def symbols(self, perm: int) -> list[str]:
        found = [r["symbol"] for r in self.history.get(perm, [])]
        ticker = self.companies[perm].get("ticker")
        return list(dict.fromkeys([*found, *([ticker] if ticker else [])]))


_INDEX: dict[str, Index] = {}


def index(store: Store) -> Index:
    if store.build_id not in _INDEX:
        _INDEX.clear()
        _INDEX[store.build_id] = Index.of(
            store.securities().to_pylist(), store.symbol_history().to_pylist()
        )
    return _INDEX[store.build_id]


def _day(value) -> date | None:
    return value.date() if isinstance(value, datetime) else value


def _iso(value) -> str | None:
    return _day(value).isoformat() if value else None


def _company(row: dict) -> dict:
    return {
        "permaticker": row["permaticker"], "ticker": row.get("ticker"), "name": row.get("name"),
        "exchange": row.get("exchange"), "category": row.get("category"),
        "sector": row.get("sector"), "industry": row.get("industry"),
        "first": _iso(row.get("first_price_date")), "last": _iso(row.get("last_price_date")),
        "delisted": bool(row.get("delisted")),
    }  # fmt: skip


def _recency(row: dict) -> tuple:
    return (bool(row.get("delisted")), -(row.get("last_price_date") or date.min).toordinal())


def search(store: Store, query: str, limit: int = 12) -> list[dict]:
    q = query.strip().upper()
    if not q:
        return []
    idx = index(store)
    scored = []
    for perm, row in idx.companies.items():
        ticker = (row.get("ticker") or "").upper()
        name = (row.get("name") or "").upper()
        past = q in (s.upper() for s in idx.symbols(perm))
        rank = (
            0 if ticker == q
            else 1 if past
            else 2 if ticker.startswith(q)
            else 3 if name.startswith(q)
            else 4 if len(q) >= 3 and q in name
            else None
        )  # fmt: skip
        if rank is not None:
            scored.append((rank, *_recency(row), ticker, perm))
    scored.sort()
    out = []
    for rank, *_, perm in scored[:limit]:
        item = _company(idx.companies[perm])
        if rank == 1:
            item["matched"] = q
        out.append(item)
    return out


def resolve(store: Store, symbol: str) -> list[int]:
    idx = index(store)
    perms = idx.by_symbol.get(symbol.upper(), set())
    current = [p for p in perms if (idx.companies[p].get("ticker") or "").upper() == symbol.upper()]
    past = [p for p in perms if p not in current]
    key = lambda p: _recency(idx.companies[p])  # noqa: E731
    return sorted(current, key=key) + sorted(past, key=key)


def _number(value, digits: int = 4):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return None
    return round(float(value), digits)


def prices(table: pa.Table) -> dict:
    rows = table.to_pylist()
    factors = [1.0] * len(rows)
    for t in range(len(rows) - 1, 0, -1):
        prev, close = rows[t].get("prev_close"), rows[t - 1].get("close")
        ratio = prev / close if prev and close and prev > 0 and close > 0 else 1.0
        factors[t - 1] = factors[t] * (ratio if 0.02 < ratio < 50 else 1.0)
    return {
        "date": [r["date"].isoformat() for r in rows],
        "open": [_number(r["open"]) for r in rows],
        "high": [_number(r["high"]) for r in rows],
        "low": [_number(r["low"]) for r in rows],
        "close": [_number(r["close"]) for r in rows],
        "factor": [_number(f, 6) for f in factors],
        "volume": [_number(r["volume"], 0) for r in rows],
        "market_cap": [_number(r["marketcap_prev"], 0) for r in rows],
        "adv20": [_number(r["adv20_prev"], 0) for r in rows],
        "symbol": [r["symbol"] for r in rows],
    }


def _parquet_glob(folder: Path, pattern: str) -> str:
    return str(folder / pattern).replace("'", "''")


def run_trades(runs_dir: Path, perm: int) -> list[dict]:
    if not any(runs_dir.glob("*/trades.parquet")):
        return []
    manifests = {m["run_id"]: m for m in registry.read_manifests(runs_dir)}
    con = duckdb.connect()
    try:
        rows = con.sql(
            f"""select filename, day, symbol, entry_price, exit_price, exit_reason, net, notional,
                       tag
                from read_parquet('{_parquet_glob(runs_dir, "*/trades.parquet")}',
                                  filename=true, union_by_name=true)
                where permaticker = ? order by day desc limit {MAX_TRADES}""",
            params=[perm],
        ).fetchall()
    finally:
        con.close()
    out = []
    for filename, day, symbol, entry, exit_, reason, net, notional, tag in rows:
        run_id = Path(filename).parent.name
        m = manifests.get(run_id) or {}
        if m.get("status") == "abandoned":
            continue
        out.append({
            "source": "run", "id": run_id, "label": m.get("strategy") or run_id,
            "detail": m.get("config"), "kind": m.get("kind"), "symbol": symbol,
            "signal_day": None, "entry_day": _iso(day), "entry": _number(entry),
            "exit_day": None, "exit": _number(exit_),
            "net": _number(net / notional, 6) if net is not None and notional else None,
            "note": reason or tag or None, "side": "long",
        })  # fmt: skip
    return out


def lab_trades(
    lab_dir: Path, symbols: list[str], spans: list[tuple[str, date, date]]
) -> list[dict]:
    if not symbols or not any(lab_dir.glob("runs/*/trades.parquet")):
        return []
    con = duckdb.connect()
    try:
        rows = con.sql(
            f"""select filename, ticker, signal_date, entry_date, exit_date, entry_price,
                       exit_price, net, reason, taken
                from read_parquet('{_parquet_glob(lab_dir, "runs/*/trades.parquet")}',
                                  filename=true, union_by_name=true)
                where ticker in (select unnest(?)) order by entry_date desc
                limit {MAX_TRADES}""",
            params=[symbols],
        ).fetchall()
    finally:
        con.close()
    names: dict[str, str] = {}
    out = []
    for filename, ticker, signal, entry_day, exit_day, entry, exit_, net, reason, taken in rows:
        when = _day(entry_day or signal)
        if spans and not any(s == ticker and lo <= when <= hi for s, lo, hi in spans):
            continue
        run_dir = Path(filename).parent
        if run_dir.name not in names:
            try:
                manifest = json.loads((run_dir / "manifest.json").read_text())
                names[run_dir.name] = manifest["algorithm"]
            except (OSError, ValueError, KeyError):
                names[run_dir.name] = run_dir.name
        out.append({
            "source": "lab", "id": run_dir.name, "label": names[run_dir.name],
            "detail": "taken by the book" if taken else "not taken by the book", "kind": "lab",
            "symbol": ticker, "signal_day": _iso(signal), "entry_day": _iso(entry_day),
            "entry": _number(entry), "exit_day": _iso(exit_day), "exit": _number(exit_),
            "net": _number(net, 6), "note": reason, "side": "long",
        })  # fmt: skip
    return out


def paper_trades(runs_dir: Path, symbols: list[str]) -> list[dict]:
    wanted = {s.upper() for s in symbols}
    out = []
    for name in ledgers.LEDGERS:
        page = ledgers.ledger(runs_dir, name)
        for r in (page or {}).get("rows", []):
            if r["symbol"].upper() in wanted:
                out.append({
                    "source": "paper", "id": name, "label": page["title"],
                    "detail": "set aside" if r["set_aside"] else r["status"], "kind": "paper",
                    "symbol": r["symbol"], "signal_day": r["day"], "entry_day": r["entry_day"],
                    "entry": r["entry"], "exit_day": r["exit_day"], "exit": r["exit"],
                    "net": r["net"], "note": None, "side": page["side"],
                })  # fmt: skip
    state_path = swing_paper.paper_dir(runs_dir, "earnings_drift") / "state.json"
    try:
        tracks = json.loads(state_path.read_text()).get("tracks", [])
    except (OSError, ValueError):
        tracks = []
    for t in tracks:
        if t.get("symbol", "").upper() in wanted:
            out.append({
                "source": "paper", "id": "earnings_drift", "label": "Earnings drift",
                "detail": t.get("status"), "kind": "paper", "symbol": t["symbol"],
                "signal_day": t.get("signal_day"), "entry_day": t.get("entry_day"),
                "entry": t.get("entry_open"), "exit_day": t.get("exit_day"), "exit": None,
                "net": t.get("gross_return"), "note": "before costs", "side": "long",
            })  # fmt: skip
    return out


def financials(store: Store, perm: int, currency: str | None) -> dict:
    periods = {}
    for name, dimension in (("quarterly", "ARQ"), ("trailing", "ART")):
        rows = store.fundamentals_of(perm, fields=FINANCIALS, dimension=dimension).to_pylist()
        periods[name] = [
            {"period": _iso(r["calendardate"]), "filed": _iso(r["datekey"]),
             **{f: _number(r[f], 6) for f in FINANCIALS}}
            for r in rows[-PERIODS:]
        ]  # fmt: skip
    return {"currency": currency or "USD", **periods}


MAX_CLOSES = 4


def closes(store: Store, symbols: list[str]) -> dict:
    idx = index(store)
    found, missing = [], []
    for symbol in [s.strip().upper() for s in symbols if s.strip()][:MAX_CLOSES]:
        perms = resolve(store, symbol)
        if perms:
            company = idx.companies[perms[0]]
            p = prices(store.panel_of(FIRST, LAST, permatickers=perms[:1], columns=COLUMNS))
            close = [
                None if c is None else _number(c * (f or 1.0))
                for c, f in zip(p["close"], p["factor"], strict=True)
            ]
            found.append({"symbol": symbol, "name": company.get("name"), "date": p["date"],
                          "close": close})  # fmt: skip
            continue
        rows = store.daily(FIRST, LAST, symbols=[symbol]).to_pylist()
        if not rows:
            missing.append(symbol)
            continue
        found.append({"symbol": symbol, "name": symbol,
                      "date": [r["date"].isoformat() for r in rows],
                      "close": [_number(r["close"]) for r in rows]})  # fmt: skip
    return {"series": found, "missing": missing, "sealed_from": HOLDOUT_START.isoformat()}


def held(idx: Index, perm: int, symbol: str, on: date) -> bool:
    return any(
        h["symbol"].upper() == symbol.upper()
        and (h["valid_from"] or FIRST) <= on <= (h["valid_to"] or LAST)
        for h in idx.history.get(perm, [])
    )


def stock(store: Store, runs_dir: Path, lab_dir: Path, symbol: str,
          permaticker: int | None = None, on: date | None = None) -> dict | None:  # fmt: skip
    idx = index(store)
    candidates = resolve(store, symbol)
    holders = [p for p in candidates if on and held(idx, p, symbol, on)]
    if permaticker in idx.companies:
        chosen = permaticker
    elif holders:
        chosen = holders[0]
    elif candidates:
        chosen = candidates[0]
    else:
        return None
    company = idx.companies[chosen]
    history = idx.history.get(chosen, [])
    spans = [(h["symbol"], h["valid_from"] or FIRST, h["valid_to"] or LAST) for h in history]
    symbols = idx.symbols(chosen)
    table = store.panel_of(FIRST, LAST, permatickers=[chosen], columns=COLUMNS)
    events = store.events_of(FIRST, LAST, permatickers=[chosen]).to_pylist()
    trades = run_trades(runs_dir, chosen) + lab_trades(lab_dir, symbols, spans)
    trades += paper_trades(runs_dir, [company.get("ticker") or symbol])
    trades.sort(key=lambda t: t["entry_day"] or t["signal_day"] or "", reverse=True)
    others = [_company(idx.companies[p]) for p in candidates if p != chosen]
    return {
        "schema": "stock-1", "query": symbol.upper(), **_company(company),
        "location": company.get("location"), "siccode": company.get("siccode"),
        "symbols": [{"symbol": h["symbol"], "from": _iso(h["valid_from"]),
                     "to": _iso(h["valid_to"])} for h in history],
        "others": others, "sealed_from": HOLDOUT_START.isoformat(),
        "prices": prices(table),
        "events": [{"date": e["date"].isoformat(), "codes": e["eventcodes"] or "",
                    "results": RESULTS_CODE in (e["eventcodes"] or "").split("|")}
                   for e in events],
        "trades": trades,
        "financials": financials(store, chosen, company.get("currency")),
    }  # fmt: skip
