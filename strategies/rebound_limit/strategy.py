"""Rebound with a limit-order entry. Definition, variants and protocol: HYPOTHESIS.md."""

from __future__ import annotations

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.features import library as f


class ReboundLimit:
    name = "rebound_limit"
    features = (
        f.RETURN_FROM_PREV_CLOSE,
        f.RETURN_15M,
        f.SESSION_OPEN,
        f.PREMARKET_DOLLAR_VOLUME,
        f.FILINGS_SINCE_PRIOR_SESSION,
        f.PREV_CLOSE,
        f.ADV20,
    )
    # Every variant shares one universe, so a sweep loads each session once.
    universe = Universe("rebound", min_prev_close=1.0, min_adv20=250_000.0, min_sessions_prior=20)

    def __init__(self, params: dict):
        self.drop = float(params.get("drop", 0.10))
        self.offset = float(params.get("limit_offset", 0.0))
        self.rest = int(params.get("rest_minutes", 10))
        self.min_adv = float(params.get("min_adv", 0.0))
        self.max_prior_events = params.get("max_prior_events")  # None: no calm-session filter
        self.min_drop_15m = params.get("min_drop_15m")  # None: no speed filter
        self.last_minute = int(params.get("last_minute", 900))
        self.min_price = float(params.get("min_price", 0.0))  # on the previous close
        self.target_pct = params.get("target_pct")  # None: no resting sell
        self.stop_pct = params.get("stop_pct")  # None: no stop
        self.max_hold = params.get("max_hold_minutes")  # None: hold to the close
        self.first_minute = 575
        self.max_gap = 0.05
        self.max_premarket = 0.05

    def _events(self, view, features) -> list[tuple[int, str, float, float, float, float]]:
        """(minute, symbol, bar close, 15-minute return, ADV, previous close) of every base
        event, 09:35–15:00."""
        found = []
        for symbol, sd in view.symbols.items():
            values = features[symbol]
            if values["filings_prev"] != 0:
                continue
            regular = sd.minute >= view.open_minute
            crossed = np.flatnonzero(regular & (values["return_from_prev_close"] <= -self.drop))
            if not len(crossed):
                continue
            i = int(crossed[0])
            minute = int(sd.minute[i])
            if not self.first_minute <= minute <= 900:
                continue
            if values["session_open"][i] < values["prev_close"] * (1 - self.max_gap):
                continue
            if values["premarket_dollar_volume"][i] >= self.max_premarket * values["adv20"]:
                continue
            found.append((minute, symbol, float(sd.close[i]), float(values["return_15m"][i]),
                          float(values["adv20"]), float(values["prev_close"])))  # fmt: skip
        return sorted(found)

    def signals(self, view, features):
        out = []
        events = self._events(view, features)
        for rank, (minute, symbol, close, ret15, adv, prev_close) in enumerate(events):
            # `rank` counts the session's earlier events (ties broken by symbol): known by then.
            if self.max_prior_events is not None and rank > int(self.max_prior_events):
                continue
            if minute > self.last_minute or adv < self.min_adv or prev_close < self.min_price:
                continue
            if self.min_drop_15m is not None and not ret15 <= -float(self.min_drop_15m):
                continue
            limit = round(close * (1 - self.offset), 2 if close >= 1 else 4)
            out.append(
                Signal(
                    symbol, minute, limit_price=limit, expire_minute=minute + self.rest,
                    target_pct=None if self.target_pct is None else float(self.target_pct),
                    stop_pct=None if self.stop_pct is None else float(self.stop_pct),
                    max_hold_minutes=None if self.max_hold is None else int(self.max_hold),
                )
            )  # fmt: skip
        return out


def build(params: dict) -> ReboundLimit:
    return ReboundLimit(params)
