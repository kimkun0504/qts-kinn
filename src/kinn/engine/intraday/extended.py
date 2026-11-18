"""Explicit extended_v1 execution, with no closing-auction fallback.

Bars proxy liquidity; there are no quotes. Both cost cases must respect each cap.
The same conservative fills are then costed at baseline and doubled slippage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from kinn.core.types import Fill, Signal
from kinn.costs.model import CostModel
from kinn.engine.intraday.data import SymbolDay

if TYPE_CHECKING:
    from kinn.engine.intraday.simulator import FillConfig

OPEN_PROXY_ASSUMPTIONS = {
    "model": "minute_open_proxy-1",
    "quotes_observed": False,
    "execution_bar_statistics_affect_cap_feasibility": True,
    "signal_replay_certifies_fills": False,
}


def simulate_extended(
    sd: SymbolDay,
    signal: Signal,
    quantity: int,
    *,
    config: FillConfig,
    costs: CostModel,
) -> tuple[list[Fill], list[Fill], str, int]:
    if (
        signal.limit_price is None
        or not np.isfinite(signal.limit_price)
        or signal.limit_price <= 0
        or signal.expire_minute is None
        or signal.max_hold_minutes is None
        or signal.max_hold_minutes < 1
        or signal.stop_pct is not None
        or signal.target_pct is not None
    ):
        raise ValueError(
            "extended_v1 requires a positive limit, expiry and timed exit; no stop/target"
        )
    live = max(signal.minute + 1, config.entry_start_minute)
    expiry = min(signal.expire_minute, config.entry_end_minute)
    entry: list[Fill] = []
    exits: list[Fill] = []
    position, remaining, first_fill = 0, quantity, None
    exiting = False
    for i in range(int(np.searchsorted(sd.minute, live)), len(sd.minute)):
        m = int(sd.minute[i])
        if m >= 1200:
            break
        if m > expiry:
            remaining = 0
        valid = (
            np.isfinite([sd.open[i], sd.high[i], sd.low[i], sd.close[i]]).all()
            and 0 < sd.low[i] <= min(sd.open[i], sd.close[i])
            and max(sd.open[i], sd.close[i]) <= sd.high[i]
            and sd.volume[i] > 0
        )
        cap = int(config.participation * int(sd.volume[i])) if valid else 0
        if position and m >= first_fill + signal.max_hold_minutes:
            exiting, remaining = True, 0
        side = "sell" if exiting and position else "buy"
        shares = min(position if side == "sell" else remaining, cap)
        if shares > 0:
            if side == "buy":
                limit = signal.limit_price
            else:
                # The previous observed completed close is known before this opening.
                # No current-bar close or future bar can set a liquidation limit.
                previous = i - 1
                while previous >= 0 and not (
                    np.isfinite(sd.close[previous])
                    and sd.close[previous] > 0
                    and sd.volume[previous] > 0
                ):
                    previous -= 1
                if previous < 0:
                    continue
                limit = float(sd.close[previous]) * (1 - config.liquidation_limit_pct)
            price = float(sd.open[i])
            slip = config.extended_slippage_multiplier * costs.marketable_slippage(
                price=price,
                shares=shares,
                adv=sd.prior.get("adv20_prev"),
                bar_high=float(sd.high[i]),
                bar_low=float(sd.low[i]),
                bar_volume=int(sd.volume[i]),
            )
            # Use 2x feasibility too: stress cannot execute outside the broker limit.
            executable = price + (2 * slip / shares) * (1 if side == "buy" else -1)
            within_cap = executable <= limit if side == "buy" else executable >= limit
            if within_cap:
                fill = Fill(sd.symbol, side, "marketable_limit", m, price, shares, slip)
                if side == "buy":
                    entry.append(fill)
                    position += shares
                    remaining -= shares
                    first_fill = m if first_fill is None else first_fill
                else:
                    exits.append(fill)
                    position -= shares
        if position == 0 and (remaining == 0 or m >= expiry):
            return (
                entry,
                exits,
                "time" if entry else "",
                min(m + 1, expiry + 1) if not entry else m + 1,
            )
    if position:
        return entry, exits, "unresolved", 1200
    return entry, exits, "", max(live, expiry + 1)
