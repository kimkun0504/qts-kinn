"""Small hand-made daily data for engine tests."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from kinn.data.daily import DailyData


def weekdays(n: int, first: date = date(2020, 1, 1)) -> list[date]:
    days, day = [], first
    while len(days) < n:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def make_data(close, *, split=None, dividend=None, eligible=None, marketcap=5e9, adv=1e8,
              sector=None, open_=None) -> DailyData:  # fmt: skip
    close = np.asarray(close, dtype=np.float64)
    t, n = close.shape
    split = np.ones((t, n)) if split is None else np.asarray(split, dtype=np.float64)
    dividend = np.zeros((t, n)) if dividend is None else np.asarray(dividend, dtype=np.float64)
    prev = np.full((t, n), np.nan)
    last = np.full(n, np.nan)
    for i in range(t):
        last = last / split[i]
        prev[i] = last
        last = np.where(np.isfinite(close[i]), close[i], last)
    prev = np.where(np.isfinite(close), prev, np.nan)  # the panel has a row only with a bar
    with np.errstate(invalid="ignore"):
        ret = (close + dividend) / prev - 1
    full = np.ones((t, n))
    return DailyData(
        dates=weekdays(t), permatickers=np.arange(1, n + 1, dtype=np.int64),
        symbols=[f"S{j}" for j in range(n)],
        sector=np.zeros(n, dtype=np.int32) if sector is None else np.asarray(sector, np.int32),
        sector_names=["A", "B", "C", "D"], open=close if open_ is None else np.asarray(open_),
        close=close, ret=ret.astype(np.float32), dollar_volume=(full * adv).astype(np.float32),
        prev_close=prev, split=split.astype(np.float32), dividend=dividend.astype(np.float32),
        adv_prev=(full * adv).astype(np.float32),
        marketcap_prev=(full * marketcap).astype(np.float32),
        eligible=np.ones((t, n), dtype=bool) if eligible is None else np.asarray(eligible, bool),
    )  # fmt: skip


class Fixed:
    """An alpha with the same score for each company every session."""

    name, lookback = "fixed", 1

    def __init__(self, scores):
        self._scores = np.asarray(scores, dtype=np.float64)

    def scores(self, view):
        return self._scores


class Trailing:
    """Mean return over the last ``sessions``: a real, lookahead-free alpha."""

    name = "trailing"

    def __init__(self, sessions=5):
        self.lookback = sessions

    def scores(self, view):
        r = view.history("ret", self.lookback)
        return r.mean(axis=0) if len(r) == self.lookback else np.full(r.shape[1], np.nan)
