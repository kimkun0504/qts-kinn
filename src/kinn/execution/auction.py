"""Execution in the opening or the closing auction.

Order sizes are decided before the open, from the previous close, and sent as market-on-open or
market-on-close orders. At this account size an order is a tiny fraction of the auction, so the
auction is both the cheapest and the most honestly simulated way to trade (decision 0014).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AuctionExecution:
    at: str = "close"  # "open" | "close"
    max_adv_fraction: float = 0.01  # of the 20-day median dollar volume
    min_trade: float = 200.0  # dollars; smaller changes are skipped, except full exits

    def __post_init__(self) -> None:
        if self.at not in ("open", "close"):
            raise ValueError("execution.at must be 'open' or 'close'")

    def orders(
        self,
        *,
        target: np.ndarray,
        shares: np.ndarray,
        equity: float,
        ref_price: np.ndarray,
        adv: np.ndarray,
        tradable: np.ndarray,
    ) -> np.ndarray:
        """Signed share changes. ``ref_price`` is the previous close on today's share basis."""
        ok = tradable & np.isfinite(ref_price) & (ref_price > 0)
        price = np.where(ok, ref_price, 1.0)
        wanted = np.trunc(np.where(ok, target * equity / price, shares))
        delta = wanted - shares
        exits = (wanted == 0) & (shares != 0)
        small = (np.abs(delta) * price < self.min_trade) & ~exits
        cap = np.floor(self.max_adv_fraction * np.nan_to_num(adv) / price)
        delta = np.clip(delta, -cap, cap)
        return np.where(ok & ~small, delta, 0.0)
