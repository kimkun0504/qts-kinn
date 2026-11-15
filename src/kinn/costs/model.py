"""The platform's cost model. Strategies cannot bring their own (decision 0004).

Fees are exact arithmetic from a calibration file. Slippage is a model: a half-spread that
depends on liquidity and price (a fallback, because the data has no quotes) plus a square-root
impact term. Passive limit fills pay no spread; their risk is priced by the fill rule
(trade-through) instead. Every report shows results at 1x and 2x slippage.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import yaml

CALIBRATIONS = Path(__file__).parent / "calibrations"


@dataclass(frozen=True)
class CostModel:
    name: str
    commission_per_share: float
    commission_min: float
    commission_max_fraction: float
    clearing_per_share: float
    pass_through_fraction: float
    cat_per_share: float
    exchange_remove_per_share: float
    exchange_remove_fraction_under_1: float
    exchange_add_per_share: float
    auction_per_share: float
    sec_fee_fraction: float
    taf_per_share: float
    taf_max: float
    tick: float
    half_spread_table: tuple[tuple[float, float], ...]
    half_spread_unknown: float
    under_5_multiplier: float
    impact_coefficient: float
    auction_bps: float
    forced_exit_bps: float

    # -- fees ----------------------------------------------------------------------------
    def commission(self, shares: int, value: float) -> float:
        """IBKR commission for one order."""
        if shares <= 0:
            return 0.0
        raw = max(shares * self.commission_per_share, self.commission_min)
        return min(raw, value * self.commission_max_fraction)

    def order_fees(
        self, *, side: str, value: float, marketable: int, passive: int, auction: int
    ) -> tuple[float, float]:
        """(commission, other fees) for one order, split by how its shares executed."""
        shares = marketable + passive + auction
        if shares <= 0:
            return 0.0, 0.0
        commission = self.commission(shares, value)
        price = value / shares
        if price < 1.0:
            remove = value * marketable / shares * self.exchange_remove_fraction_under_1
        else:
            remove = marketable * self.exchange_remove_per_share
        fees = (
            remove
            + passive * self.exchange_add_per_share
            + auction * self.auction_per_share
            + shares * (self.clearing_per_share + self.cat_per_share)
            + commission * self.pass_through_fraction
        )
        if side == "sell":
            fees += value * self.sec_fee_fraction + min(shares * self.taf_per_share, self.taf_max)
        return commission, fees

    # -- slippage (1x) -------------------------------------------------------------------
    def half_spread_bps(self, price: float, adv: float | None) -> float:
        if adv is None or adv != adv:  # None or NaN
            bps = self.half_spread_unknown
        else:
            bps = next(value for floor, value in self.half_spread_table if adv >= floor)
        if price < 5.0:
            bps *= self.under_5_multiplier
        return max(bps, 0.5 * self.tick / price * 1e4)

    def marketable_slippage(
        self,
        *,
        price: float,
        shares: int,
        adv: float | None,
        bar_high: float,
        bar_low: float,
        bar_volume: int,
    ) -> float:
        """Dollars lost to the spread and to impact on a marketable fill."""
        spread = self.half_spread_bps(price, adv) / 1e4 * price
        participation = shares / bar_volume if bar_volume > 0 else 1.0
        impact = self.impact_coefficient * (bar_high - bar_low) * math.sqrt(min(participation, 1))
        return shares * (spread + impact)

    def auction_slippage(self, *, price: float, shares: int, forced: bool = False) -> float:
        bps = self.forced_exit_bps if forced else self.auction_bps
        return shares * price * bps / 1e4


def load(name: str) -> CostModel:
    raw = yaml.safe_load((CALIBRATIONS / f"{name}.yaml").read_text())
    com, third, reg, slip = (
        raw["commission"],
        raw["third_party"],
        raw["regulatory"],
        raw["slippage"],
    )
    table = tuple(
        sorted(((float(a), float(b)) for a, b in slip["half_spread_bps_by_adv"]), reverse=True)
    )
    return CostModel(
        name=raw["name"],
        commission_per_share=com["per_share"],
        commission_min=com["min_per_order"],
        commission_max_fraction=com["max_fraction_of_value"],
        clearing_per_share=third["clearing_per_share"],
        pass_through_fraction=third["pass_through_fraction_of_commission"],
        cat_per_share=third["cat_per_share"],
        exchange_remove_per_share=third["exchange_remove_per_share"],
        exchange_remove_fraction_under_1=third["exchange_remove_fraction_under_1"],
        exchange_add_per_share=third["exchange_add_per_share"],
        auction_per_share=third["auction_per_share"],
        sec_fee_fraction=reg["sec_fee_fraction_of_proceeds"],
        taf_per_share=reg["finra_taf_per_share"],
        taf_max=reg["finra_taf_max_per_trade"],
        tick=slip["tick"],
        half_spread_table=table,
        half_spread_unknown=slip["half_spread_bps_unknown_adv"],
        under_5_multiplier=slip["under_5_multiplier"],
        impact_coefficient=slip["impact_coefficient"],
        auction_bps=slip["auction_bps"],
        forced_exit_bps=slip["forced_exit_bps"],
    )
