"""Compare turnover at the first confirmed regular-session VWAP cross."""

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.strategy import FeatureValues


def first_cross(
    bars: SymbolDay, session_open: int, block_ends: np.ndarray
) -> tuple[int, float] | None:
    start = int(bars.minute.searchsorted(session_open))
    stop = int(bars.minute.searchsorted(block_ends[-1], side="right"))
    minutes = bars.minute[start:stop]
    closes = bars.close[start:stop]
    volumes = bars.volume[start:stop]
    valid = np.isfinite(closes) & (closes > 0) & (volumes > 0)
    clock = minutes[valid] - session_open
    shares = volumes[valid]
    price = closes[valid]
    turnover = price * shares
    blocks = clock // 5
    n = len(block_ends)
    block_turnover = np.bincount(blocks, weights=turnover, minlength=n)
    block_shares = np.bincount(blocks, weights=shares, minlength=n)
    cumulative_shares = np.cumsum(block_shares)
    vwap = np.full(n, np.nan)
    np.divide(np.cumsum(block_turnover), cumulative_shares, out=vwap, where=cumulative_shares > 0)

    last_bar = clock % 5 == 4
    block_close = np.full(n, np.nan)
    closing_turnover = np.zeros(n)
    block_close[blocks[last_bar]] = price[last_bar]
    closing_turnover[blocks[last_bar]] = turnover[last_bar]

    cross = np.arange(6, n - 1)
    reference = vwap[cross - 1]
    eligible = cross[
        (block_close[cross - 1] < reference)
        & (block_close[cross] >= 1.02 * reference)
        & (block_close[cross + 1] > reference)
        & (closing_turnover[cross + 1] >= 40_000)
    ]
    if not len(eligible):
        return None
    first = int(eligible[0])
    baseline = float(np.median(block_turnover[first - 6 : first]))
    if baseline <= 0:
        return None
    return int(block_ends[first + 1]), float(block_turnover[first] / baseline)


class VwapVolumeCross:
    name = "vwap_volume_cross"
    universe = Universe(
        name, min_prev_close=2, min_adv20=1e6, min_marketcap=50e6, max_marketcap=2e9
    )
    features = ()

    def __init__(self, turnover_group: str):
        self.minimum_ratio, self.maximum_ratio = (
            (3.0, float("inf")) if turnover_group == "surge" else (1.0, 1.5)
        )

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        last_confirmation = min(14 * 60 + 4, view.close_minute - 75)
        block_ends = np.arange(view.open_minute + 4, last_confirmation + 1, 5)
        if len(block_ends) < 8:
            return []
        found = []
        for symbol, bars in view.symbols.items():
            cross = first_cross(bars, view.open_minute, block_ends)
            if cross is None:
                continue
            minute, ratio = cross
            if self.minimum_ratio <= ratio <= self.maximum_ratio:
                found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60))
        return found


def first_minute_cross(
    bars: SymbolDay, session_open: int, last_minute: int
) -> tuple[int, float] | None:
    start = int(bars.minute.searchsorted(session_open))
    stop = int(bars.minute.searchsorted(last_minute, side="right"))
    minutes = bars.minute[start:stop]
    prices = bars.close[start:stop]
    shares = bars.volume[start:stop]
    valid = np.isfinite(prices) & (prices > 0) & (shares > 0)
    clock = minutes[valid] - session_open
    length = last_minute - session_open + 1
    close = np.full(length, np.nan)
    volume = np.zeros(length)
    turnover = np.zeros(length)
    close[clock] = prices[valid]
    volume[clock] = shares[valid]
    turnover[clock] = prices[valid] * shares[valid]
    cumulative_volume = np.cumsum(volume)
    vwap = np.full(length, np.nan)
    np.divide(np.cumsum(turnover), cumulative_volume, out=vwap, where=cumulative_volume > 0)

    candidates = 30 + np.flatnonzero(
        (close[29:-1] <= vwap[29:-1]) & (close[30:] > vwap[30:]) & (turnover[30:] >= 40_000)
    )
    if not len(candidates):
        return None
    first = int(candidates[0])
    baseline = float(np.median(turnover[first - 30 : first]))
    if baseline <= 0:
        return None
    return session_open + first, float(turnover[first] / baseline)


class ImmediateVwapVolumeCross(VwapVolumeCross):
    def __init__(self, turnover_group: str):
        super().__init__("surge")
        if turnover_group == "all":
            self.minimum_ratio = 0.0

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        last_minute = min(13 * 60 + 59, view.close_minute - 75)
        if last_minute < view.open_minute + 30:
            return []
        found = []
        for symbol, bars in view.symbols.items():
            cross = first_minute_cross(bars, view.open_minute, last_minute)
            if cross is None:
                continue
            minute, ratio = cross
            if ratio >= self.minimum_ratio:
                found.append(Signal(symbol, minute, expire_minute=minute + 1, max_hold_minutes=60))
        return found


def build(params: dict) -> VwapVolumeCross:
    group = params.get("turnover_group")
    if set(params) == {"turnover_group"} and group in ("surge", "ordinary"):
        return VwapVolumeCross(group)
    if (
        set(params) == {"turnover_group", "entry_mode"}
        and params["entry_mode"] == "immediate"
        and group in ("surge", "all")
    ):
        return ImmediateVwapVolumeCross(group)
    raise ValueError("vwap_volume_cross requires one of its registered parameter sets")
