"""A fixed early price trigger and an optional pre-decision quote-size transition."""

from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.quotes import minute_ns
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, MARKETCAP


def replenishes(early, late) -> bool:
    """Displayed size ratios are unit-invariant; they do not identify executable shares."""
    try:
        prices = [early.bid_price, early.ask_price, late.bid_price, late.ask_price]
        sizes = [early.bid_size, early.ask_size, late.bid_size, late.ask_size]
        if not all(isfinite(x) and x > 0 for x in prices + sizes):
            return False
        if not all(x == int(x) for x in sizes):
            return False
    except (TypeError, ValueError, OverflowError):
        return False
    if early.ask_price <= early.bid_price or late.ask_price <= late.bid_price:
        return False
    b0, a0, b1, a1 = map(int, sizes)
    midpoint = late.ask_price / 2 + late.bid_price / 2
    return (
        b0 <= a0
        and b1 >= 3 * a1
        and b1 >= 2 * b0
        and late.bid_price >= early.bid_price
        and late.ask_price - late.bid_price <= np.nextafter(0.005 * midpoint, np.inf)
    )


def valid_pair(pair, day, symbol: str, company: int, minute: int) -> bool:
    if (
        pair.day != day
        or pair.symbol != symbol
        or pair.permaticker != company
        or pair.minute != minute
        or pair.status != "available"
    ):
        return False
    end = minute_ns(day, minute + 1)
    for quote, target in ((pair.early, end - 5_000_000_000), (pair.late, end - 1)):
        if not 0 <= target - quote.sip_timestamp <= 1_000_000_000:
            return False
    return replenishes(pair.early, pair.late)


def observed_closes(view: DayView, bars: SymbolDay) -> np.ndarray:
    close = np.full(view.close_minute - view.open_minute, np.nan)
    regular = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    close[bars.minute[regular] - view.open_minute] = bars.close[regular]
    return close


def lagged_return(close: np.ndarray, minutes: int) -> np.ndarray:
    result = np.full_like(close, np.nan)
    prior = close[..., :-minutes]
    np.divide(close[..., minutes:], prior, out=result[..., minutes:], where=prior > 0)
    return result - 1


def median_peer_return(returns: np.ndarray) -> np.ndarray:
    available = np.isfinite(returns).sum(axis=0) >= 31
    median = np.full(returns.shape[1], np.nan)
    if available.any():
        median[available] = np.nanmedian(returns[:, available], axis=0)
    return median


class BidReplenishmentReversal:
    name = "bid_replenishment_reversal"
    universe = Universe(name, min_prev_close=2, min_adv20=10e6)
    features = (MARKETCAP, ADV20)

    def __init__(self, use_quotes: bool):
        self.use_quotes = use_quotes
        self.inputs = {"nbbo_replenishment": {"sessions": 1}} if use_quotes else {}

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        peer_closes: list[list[np.ndarray]] = [[], []]
        candidates = []
        for symbol, bars in view.symbols.items():
            cap = features[symbol][MARKETCAP.name]
            if 0 < cap < 10e9 and features[symbol][ADV20.name] >= 10e6:
                close = observed_closes(view, bars)
                group = int(cap >= 2e9)
                candidates.append((symbol, bars, close, group))
                peer_closes[group].append(close)
        benchmarks = {}
        for group, closes in enumerate(peer_closes):
            if len(closes) >= 31:
                peers = np.stack(closes)
                benchmarks[group] = (
                    median_peer_return(lagged_return(peers, 15)),
                    median_peer_return(lagged_return(peers, 1)),
                )
        found = []
        for symbol, bars, close, group in candidates:
            if group not in benchmarks:
                continue
            market, recovery = benchmarks[group]
            mask = (bars.minute >= 590) & (bars.minute <= 885) & (bars.minute < view.close_minute)
            minute = bars.minute[mask]
            current = minute - view.open_minute
            hits = np.flatnonzero(
                (lagged_return(close, 15)[current] - market[current] <= -0.06)
                & (close[current] >= 1.01 * close[current - 1])
                & (lagged_return(close, 1)[current] - recovery[current] >= 0.01)
                & (close[current] * bars.volume[mask] >= 40_000)
            )
            if not len(hits):
                continue
            decision = int(minute[hits[0]])
            if self.use_quotes:
                pairs = getattr(view, "book_pairs", None)
                if pairs is None:
                    raise RuntimeError("primary requires the native nbbo_replenishment adapter")
                matching = [p for p in pairs.get(symbol, ()) if p.minute == decision]
                if len(matching) != 1:
                    raise ValueError("snapshot input must cover the exact first parent event")
                if not valid_pair(matching[0], view.day, symbol, bars.permaticker, decision):
                    continue
            found.append(Signal(symbol, decision, expire_minute=decision + 1, max_hold_minutes=120))
        return found


def build(params: dict) -> BidReplenishmentReversal:
    if set(params) - {"use_quotes"} or type(params.get("use_quotes", True)) is not bool:
        raise ValueError("only the frozen boolean use_quotes parameter is supported")
    return BidReplenishmentReversal(params.get("use_quotes", True))
