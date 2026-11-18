"""Exclude newly usable typed filings from a size-peer price reversal."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20, MARKETCAP


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


class FilingAwareDislocation:
    name = "filing_aware_dislocation"
    universe = Universe(name, min_prev_close=2, min_adv20=10e6)
    features = (MARKETCAP, ADV20)
    inputs = {"form8k": {"sessions": 1}}

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        peer_closes: list[list[np.ndarray]] = [[], []]
        candidates = []
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            cap = prior[MARKETCAP.name]
            if 0 < cap < 10e9 and prior[ADV20.name] >= 10e6:
                close = observed_closes(view, bars)
                group = int(cap >= 2e9)
                candidates.append((symbol, bars, close, group))
                peer_closes[group].append(close)

        benchmarks = {}
        for group, closes in enumerate(peer_closes):
            if len(closes) < 31:
                continue
            peers = np.stack(closes)
            benchmarks[group] = (
                median_peer_return(lagged_return(peers, 15)),
                median_peer_return(lagged_return(peers, 1)),
            )

        found = []
        for symbol, bars, close, group in candidates:
            has_filing = any(
                report.items
                and report.filed < view.day
                and report.symbol == symbol
                and report.permaticker == bars.permaticker
                for report in view.reports.get(symbol, ())
            )
            if has_filing or group not in benchmarks:
                continue
            market, recovery = benchmarks[group]
            in_window = (
                (bars.minute >= 590) & (bars.minute <= 885) & (bars.minute < view.close_minute)
            )
            minute = bars.minute[in_window]
            current = minute - view.open_minute
            relative_drop = lagged_return(close, 15)[current] - market[current]
            relative_recovery = lagged_return(close, 1)[current] - recovery[current]
            hits = np.flatnonzero(
                (relative_drop <= -0.12)
                & (close[current] >= 1.01 * close[current - 1])
                & (relative_recovery >= 0.01)
                & (close[current] * bars.volume[in_window] >= 40_000)
            )
            if len(hits):
                decision = int(minute[hits[0]])
                found.append(
                    Signal(symbol, decision, expire_minute=decision + 1, max_hold_minutes=120)
                )
        return found


def build(params: dict) -> FilingAwareDislocation:
    if params:
        raise ValueError("filing_aware_dislocation accepts no parameters")
    return FilingAwareDislocation()
