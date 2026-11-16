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


def lagged_return(close: np.ndarray, minutes: int) -> np.ndarray:
    result = np.full_like(close, np.nan)
    prior = close[..., :-minutes]
    np.divide(close[..., minutes:], prior, out=result[..., minutes:], where=prior > 0)
    return result - 1


def median_peer_return(returns: np.ndarray, minimum_members: int) -> np.ndarray:
    available = np.isfinite(returns).sum(axis=0) >= minimum_members
    median = np.full(returns.shape[1], np.nan)
    if available.any():
        median[available] = np.nanmedian(returns[:, available], axis=0)
    return median


def has_quiet_baseline(close: np.ndarray, current: int) -> bool:
    if current < 25:
        return False
    baseline = close[current - 25 : current - 14]
    valid = baseline[np.isfinite(baseline) & (baseline > 0)]
    return len(valid) >= 9 and valid.max() <= 1.03 * valid.min()


class RelativeDislocationReversal:
    name = "relative_dislocation_reversal"
    features = (f.MARKETCAP, f.ADV20)

    def __init__(
        self,
        *,
        liquid_cohort: bool = False,
        one_hour_exit: bool = False,
        peer_recovery: bool = False,
        quiet_baseline: bool = False,
        two_hour_exit: bool = False,
        min_dislocation_pp: int = 12,
        size_peers: bool = False,
        quiet_hold: bool = False,
    ):
        self.liquid_cohort = liquid_cohort
        self.max_hold_minutes = 60 if one_hour_exit else None
        if two_hour_exit:
            self.max_hold_minutes = 120
        self.peer_recovery = peer_recovery
        self.quiet_baseline = quiet_baseline
        self.min_dislocation_return = min_dislocation_pp / 100
        self.size_peers = size_peers
        self.quiet_hold = quiet_hold
        min_adv = 10_000_000 if liquid_cohort else 1_000_000
        self.universe = Universe(self.name, min_prev_close=2, min_adv20=min_adv)

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        peer_closes: list[list[np.ndarray]] = [[], []]
        candidates = []
        cap_ceiling = 10e9 if self.liquid_cohort else 2e9
        for symbol, bars in view.symbols.items():
            prior = features[symbol]
            cap = prior[f.MARKETCAP.name]
            adv = prior[f.ADV20.name]
            if not self.size_peers and cap >= 10e9 and adv >= 20e6:
                peer_closes[0].append(observed_closes(view, bars))
            min_turnover = 10e6 if self.liquid_cohort else 0.01 * cap
            if 0 < cap < cap_ceiling and adv >= min_turnover:
                close = observed_closes(view, bars)
                group = int(self.size_peers and cap >= 2e9)
                candidates.append((symbol, bars, close, group))
                if self.size_peers:
                    peer_closes[group].append(close)

        benchmarks = {}
        minimum = 31 if self.size_peers else 30
        for group, closes in enumerate(peer_closes):
            if len(closes) < minimum:
                continue
            peers = np.stack(closes)
            market = median_peer_return(lagged_return(peers, 15), minimum)
            if np.isfinite(market).any():
                recovery = (
                    median_peer_return(lagged_return(peers, 1), minimum)
                    if self.peer_recovery
                    else None
                )
                benchmarks[group] = (market, recovery)

        found = []
        for symbol, bars, close, group in candidates:
            if group not in benchmarks:
                continue
            market, market_recovery = benchmarks[group]
            in_window = (
                (bars.minute >= 590) & (bars.minute <= 885) & (bars.minute < view.close_minute)
            )
            minute = bars.minute[in_window]
            current = minute - view.open_minute
            excess = lagged_return(close, 15)[current] - market[current]
            recovered = close[current] >= 1.01 * close[current - 1]
            if market_recovery is not None:
                excess_recovery = lagged_return(close, 1)[current] - market_recovery[current]
                recovered &= excess_recovery >= 0.01
            turnover = close[current] * bars.volume[in_window]
            hits = np.flatnonzero(
                (excess <= -self.min_dislocation_return) & recovered & (turnover >= 40_000)
            )
            for hit in hits:
                quiet = (self.quiet_baseline or self.quiet_hold) and has_quiet_baseline(
                    close, int(current[hit])
                )
                if self.quiet_baseline and not quiet:
                    continue
                decision = int(minute[hit])
                hold_minutes, tag = self.max_hold_minutes, ""
                if self.quiet_hold:
                    hold_minutes = 120 if quiet else 60
                    tag = f"hold_{hold_minutes}"
                found.append(
                    Signal(
                        symbol,
                        decision,
                        expire_minute=decision + 1,
                        max_hold_minutes=hold_minutes,
                        tag=tag,
                    )
                )
                break
        return found


def build(params: dict) -> RelativeDislocationReversal:
    allowed = {
        "liquid_cohort",
        "one_hour_exit",
        "peer_recovery",
        "quiet_baseline",
        "two_hour_exit",
        "min_dislocation_pp",
        "size_peers",
        "quiet_hold",
    }
    if params.keys() - allowed:
        raise ValueError("unrecognised relative_dislocation_reversal parameter")
    liquid_cohort = params.get("liquid_cohort", False)
    one_hour_exit = params.get("one_hour_exit", False)
    peer_recovery = params.get("peer_recovery", False)
    quiet_baseline = params.get("quiet_baseline", False)
    two_hour_exit = params.get("two_hour_exit", False)
    min_dislocation_pp = params.get("min_dislocation_pp", 12)
    size_peers = params.get("size_peers", False)
    quiet_hold = params.get("quiet_hold", False)
    if not all(
        isinstance(p, bool)
        for p in (
            liquid_cohort,
            one_hour_exit,
            peer_recovery,
            quiet_baseline,
            two_hour_exit,
            size_peers,
            quiet_hold,
        )
    ):
        raise ValueError("relative dislocation parameters must be booleans")
    if one_hour_exit and not liquid_cohort:
        raise ValueError("one_hour_exit requires the liquid cohort")
    if two_hour_exit and (one_hour_exit or not liquid_cohort or not peer_recovery):
        raise ValueError("two_hour_exit requires the liquid cohort and peer recovery")
    if peer_recovery and not (one_hour_exit or two_hour_exit):
        raise ValueError("peer_recovery requires a timed exit")
    if quiet_baseline and (not one_hour_exit or peer_recovery):
        raise ValueError("quiet_baseline requires the one-hour exit with absolute recovery")
    if type(min_dislocation_pp) is not int or min_dislocation_pp not in (10, 12):
        raise ValueError("min_dislocation_pp must be 10 or 12")
    if min_dislocation_pp == 10 and not quiet_baseline:
        raise ValueError("a ten-point dislocation requires the quiet baseline")
    if size_peers and not two_hour_exit:
        raise ValueError("size_peers requires the two-hour peer recovery variant")
    if quiet_hold and not (peer_recovery and one_hour_exit):
        raise ValueError("quiet_hold requires the one-hour peer recovery variant")
    return RelativeDislocationReversal(
        liquid_cohort=liquid_cohort,
        one_hour_exit=one_hour_exit,
        peer_recovery=peer_recovery,
        quiet_baseline=quiet_baseline,
        two_hour_exit=two_hour_exit,
        min_dislocation_pp=min_dislocation_pp,
        size_peers=size_peers,
        quiet_hold=quiet_hold,
    )
