"""The intraday simulator: turns one session's signals into trades.

Execution rules (ARCHITECTURE.md rule 3), all in this file:

- **Next bar at the earliest.** A signal from bar *m* can fill from bar *m + 1*.
- **Regular session only.** Fills happen in bars from the open to the close.
- **Limit orders fill only on a trade-through**: the bar's low must be below the limit by the
  trade-through margin. The fill price is the limit (no price improvement) unless configured.
- **Stops honour gaps.** A stop gapped through fills at the bar's open, not at the stop price.
  If a stop and a target are both touched in one bar, the stop is assumed to come first, and
  a position cannot take profit in the bar it was opened in.
- **No bar, no fill.** A halt and a minute without trades look the same in the data.
- **Participation cap.** Each bar fills at most a share of its volume; the rest keeps working.
- **Flat before the close.** From the flatten minute the position is sold at market; what is
  left at the end goes to the closing auction at the official close.

A resting entry order reserves buying power from the moment it is live. Sizes are fixed-dollar,
and the book is flat every night, so sessions are independent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from kinn.core.types import Fill, Signal, Trade
from kinn.costs.model import CostModel
from kinn.engine.intraday.data import DayData, SymbolDay
from kinn.risk.sizing import BuyingPower, RiskConfig


@dataclass(frozen=True)
class FillConfig:
    participation: float = 0.05  # share of a bar's volume one order may take
    limit_through_ticks: int = 1  # price must trade this many ticks through a limit
    limit_through_bps: float = 0.0  # ... or this far, whichever is larger
    limit_fills_at_limit: bool = True  # False: a bar opening through the limit fills at its open
    flatten_before_close: int = 5  # minutes before the close when positions are sold
    no_entry_before_close: int = 10  # no new entries in the last minutes


@dataclass
class DayResult:
    trades: list[Trade] = field(default_factory=list)
    signals: int = 0
    rejected_capital: int = 0  # not enough buying power, position slots, or a duplicate symbol
    rejected_size: int = 0  # one share costs more than the position size
    unfilled: int = 0  # entry order never filled
    rejected_risk: int = 0  # refused by the entry cap or the daily loss limit


@dataclass
class _Path:
    signal: Signal
    quantity: int
    reserve: float
    live_from: int
    release: int
    entry: list[Fill]
    exit: list[Fill]
    exit_reason: str


def _through(price: float, config: FillConfig, tick: float) -> float:
    return max(config.limit_through_ticks * tick, price * config.limit_through_bps / 1e4)


def simulate_signal(
    sd: SymbolDay,
    signal: Signal,
    quantity: int,
    *,
    config: FillConfig,
    costs: CostModel,
    open_minute: int,
    close_minute: int,
    official_close: float | None,
) -> tuple[list[Fill], list[Fill], str, int]:
    """Walk one order through the session. Returns (entry fills, exit fills, exit reason,
    the minute its capital is released)."""
    live_from = max(signal.minute + 1, open_minute)
    last_entry = close_minute - config.no_entry_before_close - 1
    if signal.expire_minute is not None:
        last_entry = min(last_entry, signal.expire_minute)
    flatten = close_minute - config.flatten_before_close
    adv = sd.prior.get("adv20_prev")
    minute, open_, high, low, volume = sd.minute, sd.open, sd.high, sd.low, sd.volume
    first = int(np.searchsorted(minute, live_from, side="left"))
    end = int(np.searchsorted(minute, close_minute, side="left"))

    entry: list[Fill] = []
    exit_: list[Fill] = []
    remaining, position = quantity, 0
    exiting, reason = False, ""
    stop_price = target_price = None
    entry_minute = None

    def market_fill(side: str, kind: str, i: int, price: float, shares: int) -> Fill:
        slip = costs.marketable_slippage(
            price=price, shares=shares, adv=adv, bar_high=float(high[i]), bar_low=float(low[i]),
            bar_volume=int(volume[i]),
        )  # fmt: skip
        return Fill(sd.symbol, side, kind, int(minute[i]), price, shares, slip)

    for i in range(first, end):
        m = int(minute[i])
        o, h, lo = float(open_[i]), float(high[i]), float(low[i])
        cap = int(config.participation * int(volume[i]))

        if position > 0:
            if exiting:
                price, kind = o, "market"
            elif stop_price is not None and lo <= stop_price:
                exiting, reason = True, "stop"
                price, kind = min(stop_price, o), "stop"  # a gap through the stop fills at the open
            elif target_price is not None and h >= target_price + _through(
                target_price, config, costs.tick
            ):
                shares = min(position, cap)
                if shares > 0:
                    exit_.append(Fill(sd.symbol, "sell", "limit", m, target_price, shares, 0.0))
                    position -= shares
                    reason = "target"
                    remaining = 0
                price, kind = o, ""
            elif (
                signal.max_hold_minutes is not None and m >= entry_minute + signal.max_hold_minutes
            ):
                exiting, reason, price, kind = True, "time", o, "market"
            elif m >= flatten:
                exiting, reason, price, kind = True, "flatten", o, "market"
            else:
                price, kind = o, ""
            if exiting:
                remaining = 0
                shares = min(position, cap)
                if shares > 0:
                    exit_.append(market_fill("sell", kind, i, price, shares))
                    position -= shares

        if remaining > 0 and not exiting:
            if m > last_entry:
                remaining = 0
            else:
                if signal.limit_price is None:
                    fills, price, passive = True, o, False
                else:
                    limit = signal.limit_price
                    fills = lo <= limit - _through(limit, config, costs.tick)
                    price = limit if config.limit_fills_at_limit else min(limit, o)
                    passive = True
                shares = min(remaining, cap) if fills else 0
                if shares > 0:
                    if passive:
                        entry.append(Fill(sd.symbol, "buy", "limit", m, price, shares, 0.0))
                    else:
                        entry.append(market_fill("buy", "market", i, price, shares))
                    position += shares
                    remaining -= shares
                    if entry_minute is None:
                        entry_minute = m
                        if signal.stop_pct is not None:
                            stop_price = price * (1 - signal.stop_pct)
                        if signal.target_pct is not None:
                            target_price = price * (1 + signal.target_pct)
                    # The bar went on trading after our fill: a stop inside it is hit.
                    if stop_price is not None and lo <= stop_price:
                        exiting, reason, remaining = True, "stop", 0
                        sold = min(position, max(cap - shares, 0))
                        if sold > 0:
                            exit_.append(market_fill("sell", "stop", i, stop_price, sold))
                            position -= sold

        if position == 0 and remaining == 0:
            release = m + 1
            break
    else:
        release = close_minute

    if not entry:  # an order that never filled frees its capital when it expires
        release = max(live_from, min(release, last_entry + 1))

    if position > 0:  # the closing auction takes whatever is left
        if official_close is not None:
            price, forced = official_close, False
        else:
            price = float(sd.close[end - 1]) if end > 0 else entry[-1].price
            forced = True
        slip = costs.auction_slippage(price=price, shares=position, forced=forced)
        exit_.append(Fill(sd.symbol, "sell", "auction", close_minute, price, position, slip))
        reason = "forced" if forced else (reason or "auction")
        release = close_minute
    return entry, exit_, reason, release


def _trade(day, sd: SymbolDay, path: _Path, costs: CostModel) -> Trade:
    def split(fills: list[Fill]) -> dict:
        shares = sum(f.quantity for f in fills)
        value = sum(f.quantity * f.price for f in fills)
        return {
            "shares": shares,
            "value": value,
            "marketable": sum(f.quantity for f in fills if f.kind in ("market", "stop")),
            "passive": sum(f.quantity for f in fills if f.kind == "limit"),
            "auction": sum(f.quantity for f in fills if f.kind == "auction"),
            "slippage": sum(f.slippage for f in fills),
        }

    buy, sell = split(path.entry), split(path.exit)
    commission = fees = 0.0
    for side, part in (("buy", buy), ("sell", sell)):
        c, f = costs.order_fees(
            side=side, value=part["value"], marketable=part["marketable"],
            passive=part["passive"], auction=part["auction"],
        )  # fmt: skip
        commission, fees = commission + c, fees + f
    gross = sell["value"] - buy["value"]
    slippage = buy["slippage"] + sell["slippage"]
    net = gross - commission - fees - slippage
    return Trade(
        day=day,
        symbol=sd.symbol,
        permaticker=sd.permaticker,
        quantity=buy["shares"],
        signal_minute=path.signal.minute,
        entry_minute=path.entry[0].minute,
        entry_price=buy["value"] / buy["shares"],
        exit_minute=path.exit[-1].minute,
        exit_price=sell["value"] / sell["shares"],
        exit_reason=path.exit_reason,
        notional=buy["value"],
        gross=gross,
        commission=commission,
        fees=fees,
        slippage=slippage,
        net=net,
        net_2x=net - slippage,
        tag=path.signal.tag,
    )


def trade_from_fills(
    day, sd: SymbolDay, signal: Signal, quantity: int, entry: list[Fill], exit_: list[Fill],
    reason: str, costs: CostModel,
) -> Trade:  # fmt: skip
    """The round trip the simulator would record for these fills. For callers that walk orders
    themselves (the paper book), so their trades are costed exactly like a backtest's."""
    live_from = signal.minute + 1
    path = _Path(signal, quantity, 0.0, live_from, live_from, entry, exit_, reason)
    return _trade(day, sd, path, costs)


def reference_price(sd: SymbolDay, signal: Signal) -> float:
    """The price an order is sized against: its limit, or the last known close."""
    return _reference_price(sd, signal)


def _reference_price(sd: SymbolDay, signal: Signal) -> float:
    if signal.limit_price is not None:
        return signal.limit_price
    known = int(np.searchsorted(sd.minute, signal.minute, side="right"))
    if known > 0:
        return float(sd.close[known - 1])
    return float(sd.prior.get("prev_close") or 0.0)


def simulate_day(
    data: DayData,
    signals: list[Signal],
    *,
    risk: RiskConfig,
    config: FillConfig,
    costs: CostModel,
) -> DayResult:
    """Simulate every signal, then admit them in time order subject to buying power."""
    view = data.view
    result = DayResult(signals=len(signals))
    paths: list[tuple[SymbolDay, _Path]] = []
    for signal in signals:
        sd = view.symbols.get(signal.symbol)
        if sd is None:
            raise KeyError(f"signal for {signal.symbol}, which is not in today's universe")
        reference = _reference_price(sd, signal)
        quantity = risk.shares(signal.weight, reference)
        if quantity <= 0:
            result.rejected_size += 1
            continue
        entry, exit_, reason, release = simulate_signal(
            sd, signal, quantity, config=config, costs=costs, open_minute=view.open_minute,
            close_minute=view.close_minute, official_close=data.official_close.get(sd.symbol),
        )  # fmt: skip
        live_from = max(signal.minute + 1, view.open_minute)
        paths.append(
            (sd, _Path(signal, quantity, quantity * reference, live_from, release, entry, exit_,
                       reason))
        )  # fmt: skip

    power = BuyingPower(risk)
    admitted: list[tuple[SymbolDay, _Path, Trade]] = []
    paths.sort(key=lambda p: (p[1].live_from, -p[1].signal.weight, p[1].signal.symbol))
    for sd, path in paths:
        if path.entry and _risk_refuses(risk, admitted, path.entry[0].minute):
            result.rejected_risk += 1
            continue
        if not power.try_reserve(
            symbol=sd.symbol, start=path.live_from, release=path.release, dollars=path.reserve
        ):
            result.rejected_capital += 1
        elif not path.entry:
            result.unfilled += 1
        else:
            trade = _trade(view.day, sd, path, costs)
            admitted.append((sd, path, trade))
            result.trades.append(trade)
    return result


def _risk_refuses(
    risk: RiskConfig, admitted: list[tuple[SymbolDay, _Path, Trade]], minute: int
) -> bool:
    """Session-level risk rules, judged at the moment a new entry would fill."""
    if risk.max_entries_per_session is not None and len(admitted) >= risk.max_entries_per_session:
        return True
    if risk.daily_loss_limit is None:
        return False
    return _marked_pnl(admitted, minute) <= -risk.daily_loss_limit


def _marked_pnl(admitted: list[tuple[SymbolDay, _Path, Trade]], minute: int) -> float:
    """The session's P&L as it stood before ``minute``: closed trades at their net result, open
    positions at the last traded price."""
    total = 0.0
    for sd, path, trade in admitted:
        if path.exit[-1].minute < minute:
            total += trade.net
            continue
        bought = [f for f in path.entry if f.minute < minute]
        if not bought:
            continue
        sold = [f for f in path.exit if f.minute < minute]
        held = sum(f.quantity for f in bought) - sum(f.quantity for f in sold)
        known = int(np.searchsorted(sd.minute, minute, side="left"))
        mark = float(sd.close[known - 1]) if known > 0 else bought[-1].price
        total += (
            sum(f.quantity * f.price for f in sold)
            + held * mark
            - sum(f.quantity * f.price for f in bought)
        )
    return total
