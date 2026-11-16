"""Buy an emerging recovery from a large intraday loss relative to liquid peers."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features import library as f


def observed_closes(view: DayView, bars: SymbolDay) -> np.ndarray:
    close = np.full(view.close_minute - view.open_minute, np.nan)
    regular = (bars.minute >= view.open_minute) & (bars.minute < view.close_minute)
    close[bars.minute[regular] - view.open_minute] = bars.close[regular]
    return close


def quarter_hour_return(close: np.ndarray) -> np.ndarray:
    result = np.full_like(close, np.nan)
    np.divide(close[15:], close[:-15], out=result[15:], where=close[:-15] > 0)
    return result - 1


class RelativeDislocationReversal:
    name = "relative_dislocation_reversal"
    universe = Universe(name, min_prev_close=2, min_adv20=1_000_000)
    features = (f.MARKETCAP, f.ADV20)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        peer_returns = []
        candidates = []
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            cap = prior[f.MARKETCAP.name]
            adv = prior[f.ADV20.name]
            if cap >= 10e9 and adv >= 20e6:
                peer_returns.append(quarter_hour_return(observed_closes(view, bars)))
            if 0 < cap < 2e9 and adv >= 0.01 * cap:
                candidates.append((symbol, bars))
        if len(peer_returns) < 30:
            return []

        peers = np.stack(peer_returns)
        available = np.isfinite(peers).sum(axis=0) >= 30
        if not available.any():
            return []
        market = np.full(peers.shape[1], np.nan)
        market[available] = np.nanmedian(peers[:, available], axis=0)

        found = []
        for symbol, bars in candidates:
            in_window = (
                (bars.minute >= 590) & (bars.minute <= 885) & (bars.minute < view.close_minute)
            )
            minute = bars.minute[in_window]
            close = observed_closes(view, bars)
            current = minute - view.open_minute
            excess = quarter_hour_return(close)[current] - market[current]
            recovered = close[current] >= 1.01 * close[current - 1]
            turnover = close[current] * bars.volume[in_window]
            hits = np.flatnonzero((excess <= -0.12) & recovered & (turnover >= 40_000))
            if len(hits):
                decision = int(minute[hits[0]])
                found.append(Signal(symbol, decision, expire_minute=decision + 1))
        return found


def build(params: dict) -> RelativeDislocationReversal:
    if params:
        raise ValueError("relative_dislocation_reversal accepts no parameters")
    return RelativeDislocationReversal()
