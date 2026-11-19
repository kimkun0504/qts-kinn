"""A public disclosed-purchase selector on a fixed intraday relative reversal."""

from datetime import date
from math import isfinite

import numpy as np

from kinn.core.types import Disclosure, Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues

FIRST_ELIGIBLE = date(2006, 2, 1)


def positive(value) -> bool:
    try:
        return not isinstance(value, bool) and value is not None and isfinite(value) and value > 0
    except (TypeError, ValueError, OverflowError):
        return False


def material_purchase(view: DayView, symbol: str, filings: tuple[Disclosure, ...]) -> bool:
    """The store supplies the twenty-session slice; only known valid original records count."""
    purchases: dict[str, tuple[str, float, float]] = {}
    issuers = set()
    for row in filings:
        if (
            row.filed >= view.day
            or row.symbol != symbol
            or row.document_type != "4"
            or row.transaction_code != "P"
            or row.acquired != "A"
            or not (row.officer or row.director)
            or not row.accession
            or not row.accession.strip()
            or not row.issuer_cik
            or not row.issuer_cik.strip()
            or not positive(row.purchase_amount)
            or not positive(row.shares)
        ):
            continue
        record = row.issuer_cik, row.purchase_amount, row.shares
        if purchases.setdefault(row.accession, record) != record:
            return False
        issuers.add(row.issuer_cik)
    return len(issuers) == 1 and any(amount >= 100_000 for _, amount, _ in purchases.values())


def observed(view: DayView, bars: SymbolDay) -> np.ndarray:
    prices = np.full(view.close_minute - view.open_minute, np.nan)
    valid = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    valid &= np.isfinite(bars.close) & (bars.close > 0)
    prices[bars.minute[valid] - view.open_minute] = bars.close[valid]
    return prices


def lag_return(prices: np.ndarray, lag: int) -> np.ndarray:
    result = np.full_like(prices, np.nan)
    np.divide(
        prices[..., lag:], prices[..., :-lag], out=result[..., lag:], where=prices[..., :-lag] > 0
    )
    return result - 1


def reference(prices: list[np.ndarray]):
    matrix = np.stack(prices)
    refs = []
    for lag in (15, 1):
        changes = lag_return(matrix, lag)
        enough = np.isfinite(changes).sum(axis=0) >= 31
        median = np.full(matrix.shape[1], np.nan)
        median[enough] = np.nanmedian(changes[:, enough], axis=0)
        refs.append(median)
    return tuple(refs)


class DisclosedValueReversal:
    name = "disclosed_value_reversal"
    universe = Universe(
        name, min_prev_close=2, min_adv20=1e6, min_marketcap=50e6, max_marketcap=2e9
    )
    features = ()
    inputs = {"form4": {"sessions": 20}}

    def __init__(self, require_purchase: bool):
        self.require_purchase = require_purchase

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        if view.day < FIRST_ELIGIBLE or len(view.symbols) < 31:
            return []
        prices = {symbol: observed(view, bars) for symbol, bars in view.symbols.items()}
        market15, market1 = reference(list(prices.values()))
        found = []
        for symbol, bars in view.symbols.items():
            if self.require_purchase and not material_purchase(
                view, symbol, view.disclosures.get(symbol, ())
            ):
                continue
            close = prices[symbol]
            valid = (bars.minute >= 590) & (bars.minute <= 885) & (bars.minute < view.close_minute)
            minutes = bars.minute[valid]
            indices = minutes - view.open_minute
            r15, r1 = lag_return(close, 15), lag_return(close, 1)
            hits = np.flatnonzero(
                (r15[indices] - market15[indices] <= np.nextafter(-0.08, np.inf))
                & (close[indices] >= np.nextafter(1.01 * close[indices - 1], -np.inf))
                & (r1[indices] - market1[indices] >= np.nextafter(0.01, -np.inf))
                & (close[indices] * bars.volume[valid] >= 40_000)
            )
            if len(hits):
                minute = int(minutes[hits[0]])
                found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=120))
        return found


def build(params: dict) -> DisclosedValueReversal:
    if set(params) - {"require_purchase"} or type(params.get("require_purchase", True)) is not bool:
        raise ValueError("only the frozen boolean require_purchase is supported")
    return DisclosedValueReversal(params.get("require_purchase", True))
