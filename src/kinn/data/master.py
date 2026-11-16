"""Security master: who is who, and which symbol each company traded under on each date.

Sharadar identifies a company by ``permaticker`` and files its whole history under its newest
ticker (delisted names whose ticker was reused get a digit suffix, e.g. ``FB1``). Massive bars
carry the symbol in force on the day. ``symbol_history`` bridges the two.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

import pyarrow as pa

from kinn.core.settings import HOLDOUT_START

_SUFFIXED = re.compile(r"^([A-Z.]+?)\d+$")
_FAR_PAST = date(1900, 1, 1)

SYMBOL_HISTORY_SCHEMA = pa.schema(
    [
        ("permaticker", pa.int64()),
        ("symbol", pa.string()),
        ("valid_from", pa.date32()),
        ("valid_to", pa.date32()),  # exclusive; HOLDOUT_START means "still in force at the seal"
    ]
)


def traded_symbol(sharadar_ticker: str, delisted: bool) -> str:
    """Undo Sharadar's digit suffix on delisted names (``FB1`` traded as ``FB``)."""
    if delisted:
        match = _SUFFIXED.match(sharadar_ticker)
        if match:
            return match.group(1)
    return sharadar_ticker


def symbol_history(
    tickers: pa.Table, changes: pa.Table, *, horizon: date = HOLDOUT_START
) -> pa.Table:
    """Intervals ``[valid_from, valid_to)`` during which ``symbol`` meant ``permaticker``.

    ``tickers`` is the censored table from ``sharadar.ingest_tickers``; ``changes`` comes from
    ``sharadar.read_ticker_changes``. Every interval is clipped to the company's priced life
    and to ``horizon`` (the seal, by default), so no output date is on or after it. Only the
    owner's unsealed build passes a later horizon.
    """
    events: dict[str, list[tuple[date, str]]] = {}
    for when, ticker, old in zip(
        changes["date"].to_pylist(),
        changes["ticker"].to_pylist(),
        changes["old_symbol"].to_pylist(),
        strict=True,
    ):
        if when is not None and ticker and old:
            events.setdefault(ticker, []).append((when, old))

    rows: list[tuple[int, str, date, date]] = []
    for perma, ticker, first, last in zip(
        tickers["permaticker"].to_pylist(),
        tickers["ticker"].to_pylist(),
        tickers["firstpricedate"].to_pylist(),
        tickers["lastpricedate"].to_pylist(),
        strict=True,
    ):
        life_start = first or _FAR_PAST
        life_end = min(last + timedelta(days=1), horizon) if last else horizon
        start = _FAR_PAST
        pieces: list[tuple[str, date, date]] = []
        for when, old in sorted(events.get(ticker, [])):
            pieces.append((old, start, when))
            start = when
        pieces.append((traded_symbol(ticker, delisted=last is not None), start, date.max))
        merged: list[tuple[str, date, date]] = []
        for symbol, piece_start, piece_end in pieces:
            valid_from, valid_to = max(piece_start, life_start), min(piece_end, life_end)
            if valid_from >= valid_to:
                continue
            if merged and merged[-1][0] == symbol and merged[-1][2] == valid_from:
                merged[-1] = (symbol, merged[-1][1], valid_to)
            else:
                merged.append((symbol, valid_from, valid_to))
        rows.extend((perma, symbol, start, end) for symbol, start, end in merged)

    columns = list(zip(*rows, strict=True)) if rows else [[], [], [], []]
    return pa.table(
        [
            pa.array(col, type=field.type)
            for col, field in zip(columns, SYMBOL_HISTORY_SCHEMA, strict=True)
        ],
        schema=SYMBOL_HISTORY_SCHEMA,
    )
