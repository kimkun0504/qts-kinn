"""Fixed relative reversal, conditional on a coherent public financial snapshot.

The declared native input is not implemented yet. No private data loader or daily-field
forward-fill is an alternative to that contract.
"""

from datetime import date
from math import isfinite

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, MARKETCAP


def usable_snapshot(snapshot, view: DayView, symbol: str, company: int) -> bool:
    if snapshot is None:
        raise ValueError(
            "native snapshot must represent the exact company, including missing status"
        )
    if snapshot.symbol != symbol or snapshot.permaticker != company or snapshot.dimension != "ART":
        raise ValueError("financial snapshot identity or dimension mismatch")
    if snapshot.status not in ("available", "missing", "conflict", "invalid"):
        raise ValueError("unknown financial snapshot status")
    if snapshot.status != "available":
        return False
    if type(snapshot.filed) is not date or type(snapshot.reportperiod) is not date:
        return False
    if not snapshot.reportperiod <= snapshot.filed < view.day:
        return False
    if not 0 <= (view.day - snapshot.reportperiod).days <= 180:
        return False
    try:
        return all(not isinstance(v, bool) and isfinite(v) for v in (snapshot.opinc, snapshot.ncfo))
    except (TypeError, ValueError, OverflowError):
        return False


def observed(view: DayView, bars: SymbolDay) -> np.ndarray:
    values = np.full(view.close_minute - view.open_minute, np.nan)
    inside = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    inside &= np.isfinite(bars.close) & (bars.close > 0)
    values[bars.minute[inside] - view.open_minute] = bars.close[inside]
    return values


def lag_return(prices: np.ndarray, lag: int) -> np.ndarray:
    result = np.full_like(prices, np.nan)
    np.divide(
        prices[..., lag:], prices[..., :-lag], out=result[..., lag:], where=prices[..., :-lag] > 0
    )
    return result - 1


def reference(group: list[np.ndarray]):
    if len(group) < 31:
        return None
    matrix = np.stack(group)
    refs = []
    for lag in (15, 1):
        changes = lag_return(matrix, lag)
        valid = np.isfinite(changes).sum(axis=0) >= 31
        median = np.full(matrix.shape[1], np.nan)
        median[valid] = np.nanmedian(changes[:, valid], axis=0)
        refs.append(median)
    return tuple(refs)


class CashProfitReversal:
    name = "cash_profit_reversal"
    universe = Universe(name, min_prev_close=2, min_adv20=10e6, max_marketcap=10e9)
    features = (MARKETCAP, ADV20)
    inputs = {"fundamentals_art": {"sessions": 1}}

    def __init__(self, require_positive: bool):
        self.require_positive = require_positive

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        records = getattr(view, "fundamentals", None)
        if records is None:
            raise RuntimeError("requires the native coherent fundamentals_art snapshot adapter")
        groups: list[list[np.ndarray]] = [[], []]
        candidates = []
        for symbol, bars in view.symbols.items():
            cap = features[symbol][MARKETCAP.name]
            if 0 < cap < 10e9 and features[symbol][ADV20.name] >= 10e6:
                group = int(cap >= 2e9)
                prices = observed(view, bars)
                groups[group].append(prices)
                candidates.append((symbol, bars, group, prices))
        refs = [reference(g) for g in groups]
        found = []
        for symbol, bars, group, prices in candidates:
            if refs[group] is None:
                continue
            market15, market1 = refs[group]
            valid = (bars.minute >= 590) & (bars.minute <= 885) & (bars.minute < view.close_minute)
            minutes = bars.minute[valid]
            indices = minutes - view.open_minute
            r15, r1 = lag_return(prices, 15), lag_return(prices, 1)
            hits = np.flatnonzero(
                (r15[indices] - market15[indices] <= np.nextafter(-0.08, np.inf))
                & (prices[indices] >= np.nextafter(1.01 * prices[indices - 1], -np.inf))
                & (r1[indices] - market1[indices] >= np.nextafter(0.01, -np.inf))
                & (prices[indices] * bars.volume[valid] >= 40_000)
            )
            if not len(hits):
                continue
            snapshot = records.get(symbol)
            if not usable_snapshot(snapshot, view, symbol, bars.permaticker):
                continue
            if self.require_positive and not (snapshot.opinc > 0 and snapshot.ncfo > 0):
                continue
            minute = int(minutes[hits[0]])
            found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=120))
        return found


def build(params: dict) -> CashProfitReversal:
    if set(params) - {"require_positive"} or type(params.get("require_positive", True)) is not bool:
        raise ValueError("only the frozen boolean require_positive is supported")
    return CashProfitReversal(params.get("require_positive", True))
