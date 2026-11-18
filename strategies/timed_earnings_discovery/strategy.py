"""Prepared rule for the proposed, owner-authorized form8k_timed contract."""

from datetime import date
from decimal import ROUND_DOWN, Decimal
from zoneinfo import ZoneInfo

import numpy as np

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.engine.intraday.strategy import FeatureValues
from kinn.features.library import ADV20

NEW_YORK = ZoneInfo("America/New_York")


def first_report(reports, symbol: str, company: int, day: date):
    """Select the first original after-close earnings filing, never a later rescue."""
    eligible = []
    for report in reports:
        accepted = report.accepted
        if accepted.tzinfo is None or accepted.utcoffset() is None:
            raise ValueError("timed filing acceptance must be timezone-aware")
        local = accepted.astimezone(NEW_YORK)
        minute = local.hour * 60 + local.minute
        if (
            report.symbol != symbol
            or report.permaticker != company
            or report.form != "8-K"
            or not report.accession
            or "2.02" not in report.items
            or not report.earnings
            or local.date() != day
            or not 960 <= minute < 1020
        ):
            continue
        if report.usable_minute != minute + 1:
            raise ValueError("timed filing must use the frozen one-complete-minute delay")
        eligible.append(report)
    return min(eligible, key=lambda r: (r.accepted, r.accession)) if eligible else None


class TimedEarningsDiscovery:
    name = "timed_earnings_discovery"
    universe = Universe(
        name,
        min_prev_close=3,
        min_adv20=2e6,
        min_marketcap=50e6,
        max_marketcap=2e9,
        min_sessions_prior=20,
    )
    features = (ADV20,)
    inputs = {"form8k_timed": {"sessions": 1}}

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]:
        reports = getattr(view, "timed_reports", None)
        if reports is None:
            raise RuntimeError(
                "form8k_timed requires the scoped platform/input authorization and adapter"
            )
        if view.open_minute != 570 or view.close_minute != 960:
            return []
        signals = []
        for symbol, bars in view.symbols.items():
            report = first_report(reports.get(symbol, ()), symbol, bars.permaticker, view.day)
            if report is None:
                continue
            local = report.accepted.astimezone(NEW_YORK)
            m = local.hour * 60 + local.minute
            wanted = np.array([m - 1, m + 1, m + 2, m + 3])
            indices = np.searchsorted(bars.minute, wanted)
            if np.any(indices >= len(bars.minute)) or not np.array_equal(
                bars.minute[indices], wanted
            ):
                continue
            p, v = bars.close[indices], bars.volume[indices]
            adv = features[symbol][ADV20.name]
            if (
                not (np.isfinite(p) & (p > 0) & np.isfinite(v) & (v > 0) & (v == np.floor(v))).all()
                or not np.isfinite(adv)
                or adv <= 0
            ):
                continue
            turnover = p[1:] * v[1:]
            if (
                p[-1] < np.nextafter(1.05 * p[0], -np.inf)
                or p[-1] > np.nextafter(1.15 * p[0], np.inf)
                or turnover.sum() < max(100_000, 0.05 * adv)
                or np.any(turnover < 10_000)
                or turnover[-1] < 40_000
            ):
                continue
            limit = float(
                (Decimal(str(p[-1])) * Decimal("1.01")).quantize(
                    Decimal("0.01"), rounding=ROUND_DOWN
                )
            )
            signals.append(
                Signal(symbol, m + 3, limit_price=limit, expire_minute=m + 4, max_hold_minutes=30)
            )
        return signals


def build(params: dict) -> TimedEarningsDiscovery:
    if params:
        raise ValueError("timed_earnings_discovery has no tunable parameters")
    return TimedEarningsDiscovery()
