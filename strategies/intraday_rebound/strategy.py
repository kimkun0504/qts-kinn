"""Intraday rebound after a no-news drop. The definition is fixed in HYPOTHESIS.md."""

from __future__ import annotations

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.features import library as f


class IntradayRebound:
    name = "intraday_rebound"
    features = (
        f.RETURN_FROM_PREV_CLOSE,
        f.SESSION_OPEN,
        f.PREMARKET_DOLLAR_VOLUME,
        f.FILINGS_SINCE_PRIOR_SESSION,
        f.PREV_CLOSE,
        f.ADV20,
    )

    def __init__(self, params: dict):
        self.drop = float(params["drop"])  # 0.10: close at least 10% below the prior close
        self.max_gap = float(params["max_gap"])  # 0.05: opened no lower than 5% down
        self.max_premarket = float(params["max_premarket_share_of_adv"])  # 0.05
        self.first_minute = int(params["first_minute"])  # 575 = 09:35
        self.last_minute = int(params["last_minute"])  # 900 = 15:00
        self.universe = Universe(
            "rebound",
            min_prev_close=float(params["min_price"]),
            min_adv20=float(params["min_adv"]),
            min_sessions_prior=20,
        )

    def signals(self, view, features):
        out = []
        for symbol, sd in view.symbols.items():
            values = features[symbol]
            if values["filings_prev"] != 0:
                continue
            regular = sd.minute >= view.open_minute
            crossed = np.flatnonzero(regular & (values["return_from_prev_close"] <= -self.drop))
            if not len(crossed):
                continue
            i = int(crossed[0])  # the first regular-session bar that closes below the line
            minute = int(sd.minute[i])
            if not self.first_minute <= minute <= self.last_minute:
                continue
            if values["session_open"][i] < values["prev_close"] * (1 - self.max_gap):
                continue
            if values["premarket_dollar_volume"][i] >= self.max_premarket * values["adv20"]:
                continue
            out.append(Signal(symbol, minute))
        return out


def build(params: dict) -> IntradayRebound:
    return IntradayRebound(params)
