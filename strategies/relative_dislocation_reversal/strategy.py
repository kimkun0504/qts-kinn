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
    features = (f.MARKETCAP, f.ADV20)

    def __init__(self, *, liquid_cohort: bool = False):
        self.liquid_cohort = liquid_cohort
        min_adv = 10_000_000 if liquid_cohort else 1_000_000
        self.universe = Universe(self.name, min_prev_close=2, min_adv20=min_adv)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        peer_returns = []
        candidates = []
        cap_ceiling = 10e9 if self.liquid_cohort else 2e9
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            cap = prior[f.MARKETCAP.name]
            adv = prior[f.ADV20.name]
            if cap >= 10e9 and adv >= 20e6:
                peer_returns.append(quarter_hour_return(observed_closes(view, bars)))
            min_turnover = 10e6 if self.liquid_cohort else 0.01 * cap
            if 0 < cap < cap_ceiling and adv >= min_turnover:
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
    if params.keys() - {"liquid_cohort"}:
        raise ValueError("relative_dislocation_reversal only accepts liquid_cohort")
    liquid_cohort = params.get("liquid_cohort", False)
    if not isinstance(liquid_cohort, bool):
        raise ValueError("liquid_cohort must be a boolean")
    return RelativeDislocationReversal(liquid_cohort=liquid_cohort)
