"""Standard features. Add one here only when a strategy needs it."""

from __future__ import annotations

import numpy as np

from kinn.features.base import Availability, Feature, prior

PREV_CLOSE = prior("prev_close")
ADV20 = prior("adv20", "adv20_prev")
MARKETCAP = prior("marketcap", "marketcap_prev")


def _return_from_prev_close(sd) -> np.ndarray:
    prev = sd.prior.get("prev_close")
    if not prev:
        return np.full(sd.minute.shape, np.nan)
    return sd.close / prev - 1.0


RETURN_FROM_PREV_CLOSE = Feature(
    "return_from_prev_close", Availability.BAR_CLOSE, _return_from_prev_close
)
CUM_VOLUME = Feature("cum_volume", Availability.BAR_CLOSE, lambda sd: np.cumsum(sd.volume))
CUM_DOLLAR_VOLUME = Feature(
    "cum_dollar_volume", Availability.BAR_CLOSE, lambda sd: np.cumsum(sd.close * sd.volume)
)
LOW_SO_FAR = Feature(
    "low_so_far",
    Availability.BAR_CLOSE,
    lambda sd: np.minimum.accumulate(sd.low) if len(sd.low) else sd.low,
)


def _premarket_dollar_volume(sd) -> np.ndarray:
    early = sd.minute < 570
    return np.cumsum(np.where(early, sd.close * sd.volume, 0.0))


def _session_open(sd) -> np.ndarray:
    out = np.full(sd.minute.shape, np.nan)
    regular = np.flatnonzero(sd.minute >= 570)
    if len(regular):
        out[regular[0] :] = sd.open[regular[0]]
    return out


FILINGS_SINCE_PRIOR_SESSION = prior("filings_prev")
PREMARKET_DOLLAR_VOLUME = Feature(
    "premarket_dollar_volume", Availability.BAR_CLOSE, _premarket_dollar_volume
)
SESSION_OPEN = Feature("session_open", Availability.BAR_CLOSE, _session_open)
