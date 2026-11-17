"""Shared value types. Times are minutes after midnight in New York (570 = 09:30).

A bar with ``minute = m`` covers ``[m, m + 1)`` and is known only at ``m + 1``. A signal whose
``minute`` is ``m`` was decided on bars up to and including ``m``, so it may act from ``m + 1``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

RTH_OPEN = 570  # 09:30
RTH_CLOSE = 960  # 16:00


@dataclass(frozen=True, slots=True)
class Bar:
    minute: int
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass(frozen=True, slots=True)
class Event:
    """Something that happened to a symbol at a minute; the unit of an event study."""

    day: date
    symbol: str
    minute: int
    kind: str


@dataclass(frozen=True, slots=True)
class Signal:
    """A request to buy. Long only for now (short selling is deferred, decision 0010)."""

    symbol: str
    minute: int  # last bar the decision used; the order is live from minute + 1
    limit_price: float | None = None  # None means a market order
    expire_minute: int | None = None  # last minute the entry order may fill
    target_pct: float | None = None  # take profit, as a fraction of the entry price
    stop_pct: float | None = None  # stop loss, as a fraction of the entry price
    max_hold_minutes: int | None = None
    weight: float = 1.0  # multiplies the position size; also the priority when capital is short
    tag: str = ""


@dataclass(frozen=True, slots=True)
class Disclosure:
    """One line of an insider's Form 4: a filing, a transaction code and a direction.

    ``amount`` is shares times price, summed, in dollars (None when no price was reported);
    ``purchase_amount`` is that amount for an open-market purchase (code P, acquired) and
    None otherwise. ``filed`` is the SEC filing date; a strategy sees the disclosure from the
    first session after it.
    """

    accession: str
    issuer_cik: str
    issuer_name: str
    symbol: str
    filed: date
    document_type: str  # "4" or "4/A"
    transaction_code: str  # P purchase, S sale, A award, M option exercise, F tax, G gift, ...
    acquired: str  # "A" acquired, "D" disposed
    shares: float | None
    amount: float | None
    purchase_amount: float | None
    owner_cik: str | None
    owner_name: str | None
    officer: bool
    director: bool
    ten_percent_owner: bool
    title: str | None


@dataclass(frozen=True, slots=True)
class Order:
    symbol: str
    side: str  # "buy" | "sell"
    kind: str  # "market" | "limit" | "stop" | "auction"
    quantity: int
    live_from: int
    limit_price: float | None = None
    stop_price: float | None = None


@dataclass(frozen=True, slots=True)
class Fill:
    symbol: str
    side: str
    kind: str  # "market" | "limit" | "stop" | "auction"
    minute: int
    price: float
    quantity: int
    slippage: float  # dollars, at 1x; zero for passive limit fills


@dataclass(frozen=True, slots=True)
class Trade:
    """One round trip. Money in dollars. ``net`` uses 1x slippage, ``net_2x`` twice that."""

    day: date
    symbol: str
    permaticker: int
    quantity: int
    signal_minute: int
    entry_minute: int
    entry_price: float
    exit_minute: int
    exit_price: float
    exit_reason: str  # target | stop | time | flatten | auction | forced
    notional: float
    gross: float
    commission: float
    fees: float
    slippage: float
    net: float
    net_2x: float
    tag: str = ""


@dataclass(frozen=True, slots=True)
class BookFill:
    """One auction fill in a multi-day book. ``shares`` is signed: negative sells or shorts."""

    day: date
    permaticker: int
    symbol: str
    shares: float
    price: float
    value: float
    commission: float
    fees: float
    slippage: float
    reason: str  # rebalance | delisted
