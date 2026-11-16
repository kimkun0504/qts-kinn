"""The paper session: one trading day, stepped a minute at a time.

It is the backtest run incrementally. Signals come from the strategy's own code on the bars
known so far; fills come from the simulator's own fill function on those same bars; capital is
admitted by the same rule. Replaying a past day therefore gives exactly the backtest's trades
for that day (a test holds it to that). Nothing here talks to a broker.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date

from kinn.core.types import Fill, Signal, Trade
from kinn.costs.model import CostModel
from kinn.engine.intraday.data import DayView, SymbolDay
from kinn.engine.intraday.simulator import (
    FillConfig,
    reference_price,
    simulate_signal,
    trade_from_fills,
)
from kinn.engine.intraday.strategy import Strategy, day_signals
from kinn.risk.sizing import RiskConfig


@dataclass
class Rung:
    """One resting order: a strategy signal, sized and admitted (or refused)."""

    signal: Signal
    quantity: int
    reserve: float
    live_from: int
    last_entry: int
    status: str = "working"  # working | filled | partial | expired | cancelled | refused
    note: str = ""
    entry: list[Fill] = field(default_factory=list)
    sold: int = 0  # shares already sold by an intraday exit (stop, target, time)
    trade: Trade | None = None
    event_price: float | None = None  # the close of the bar that raised the signal
    prev_close: float | None = None
    marketcap: float | None = None

    @property
    def symbol(self) -> str:
        return self.signal.symbol

    @property
    def filled(self) -> int:
        return sum(f.quantity for f in self.entry)

    @property
    def held(self) -> int:
        return self.filled - self.sold

    @property
    def entry_value(self) -> float:
        return sum(f.quantity * f.price for f in self.entry)


class Session:
    def __init__(
        self, *, day: date, strategy: Strategy, risk: RiskConfig, fills: FillConfig,
        costs: CostModel, open_minute: int, close_minute: int,
    ):  # fmt: skip
        self.day, self.strategy, self.risk, self.fills, self.costs = (
            day,
            strategy,
            risk,
            fills,
            costs,
        )
        self.open_minute, self.close_minute = open_minute, close_minute
        self.rungs: list[Rung] = []
        self.events: list[dict] = []
        self.curve: list[tuple[int, float]] = []
        self.trades: list[Trade] = []
        self.minute: int | None = None
        self.halted = False
        self.finished = False
        self._seen: set[Signal] = set()
        self._last: dict[str, float] = {}
        self.signals = 0

    # -- one bar ---------------------------------------------------------------------------
    def step(self, minute: int, view: DayView) -> None:
        """Bar ``minute`` has closed; ``view`` holds every bar up to and including it."""
        self.minute = minute
        for rung in self.rungs:
            if rung.status != "refused":
                self._walk(rung, view.symbols[rung.symbol], minute)
        fresh = [s for s in day_signals(self.strategy, view) if s not in self._seen]
        # Admit in the simulator's order: by the minute an order goes live, larger weight
        # first, then symbol. The sort is stable, so a ladder's rungs keep the strategy's order.
        for signal in sorted(fresh, key=lambda s: (s.minute, -s.weight, s.symbol)):
            self._seen.add(signal)
            self.signals += 1
            self._place(signal, view.symbols[signal.symbol])
        self.curve.append((minute, self.marked_pnl()))

    def _place(self, signal: Signal, sd: SymbolDay) -> None:
        live_from = max(signal.minute + 1, self.open_minute)
        last_entry = self.close_minute - self.fills.no_entry_before_close - 1
        if signal.expire_minute is not None:
            last_entry = min(last_entry, signal.expire_minute)
        reference = reference_price(sd, signal)
        quantity = self.risk.shares(signal.weight, reference)
        rung = Rung(signal, quantity, quantity * reference, live_from, last_entry)
        known = sd.minute <= signal.minute
        rung.event_price = float(sd.close[known][-1]) if known.any() else None
        rung.prev_close, rung.marketcap = sd.prior.get("prev_close"), sd.prior.get("marketcap_prev")
        self.rungs.append(rung)
        refusal = self._refusal(rung)
        if refusal:
            rung.status, rung.note = "refused", refusal
            self._log(signal.minute, "refused", signal.symbol, tag=signal.tag, reason=refusal)
            return
        self._log(signal.minute, "order", signal.symbol, tag=signal.tag, limit=signal.limit_price,
                  quantity=quantity, expires=last_entry)  # fmt: skip

    def _refusal(self, rung: Rung) -> str:
        if self.halted:
            return "trading is halted"
        if rung.quantity <= 0:
            return "one share costs more than the position size"
        active = [r for r in self.rungs if r is not rung and self._reserves(r, rung.live_from)]
        if any(r.symbol == rung.symbol and r.live_from != rung.live_from for r in active):
            return "already an order or position in this stock"
        if self.risk.max_positions is not None and len(active) >= self.risk.max_positions:
            return "position limit reached"
        if sum(r.reserve for r in active) + rung.reserve > self.risk.buying_power + 1e-9:
            return "not enough buying power"
        return ""

    def _reserves(self, rung: Rung, start: int) -> bool:
        """Does this order still hold capital when another goes live at ``start``? A filled
        order holds it to the close; an unfilled one until the minute after it expires."""
        if rung.status == "refused":
            return False
        if rung.filled > 0:
            return True
        if rung.status == "cancelled":
            return False
        return max(rung.live_from, rung.last_entry + 1) > start

    def _walk(self, rung: Rung, sd: SymbolDay, minute: int) -> None:
        """Bring one order up to ``minute`` with the simulator's own fill function."""
        if len(sd.close):
            self._last[rung.symbol] = float(sd.close[-1])
        if rung.status == "cancelled":
            return
        entry, exits, _, _ = simulate_signal(
            sd, rung.signal, rung.quantity, config=self.fills, costs=self.costs,
            open_minute=self.open_minute, close_minute=self.close_minute, official_close=None,
        )  # fmt: skip
        for fill in entry[len(rung.entry) :]:
            rung.entry.append(fill)
            self._log(fill.minute, "fill", rung.symbol, tag=rung.signal.tag, price=fill.price,
                      quantity=fill.quantity)  # fmt: skip
        rung.sold = sum(f.quantity for f in exits if f.kind != "auction" and f.minute <= minute)
        if rung.filled >= rung.quantity:
            rung.status = "filled"
        elif minute >= rung.last_entry and rung.status == "working":
            rung.status = "partial" if rung.filled else "expired"
            self._log(rung.last_entry, "expired", rung.symbol, tag=rung.signal.tag,
                      filled=rung.filled, quantity=rung.quantity)  # fmt: skip

    # -- controls --------------------------------------------------------------------------
    def halt(self) -> None:
        """Stop trading: cancel what is still resting and take no new orders. Positions already
        held stay until the close."""
        if self.halted:
            return
        self.halted = True
        for rung in self.rungs:
            if rung.status == "working":
                rung.status, rung.note = "cancelled", "cancelled by the halt"
        self._log(self.minute or self.open_minute, "halt", "", reason="halted by the operator")

    def resume(self) -> None:
        if self.halted and not self.finished:
            self.halted = False
            self._log(self.minute or self.open_minute, "resume", "")

    # -- the close -------------------------------------------------------------------------
    def finish(self, view: DayView, official_close: Mapping[str, float]) -> list[Trade]:
        """The session is over: every position is sold in the closing auction."""
        for rung in self.rungs:
            if not rung.entry:
                if rung.status == "working":
                    rung.status = "expired"
                continue
            sd = view.symbols[rung.symbol]
            close = official_close.get(rung.symbol)
            if rung.status == "cancelled":
                entry, exits, reason = rung.entry, [self._auction(rung, sd, close)], "auction"
            else:
                entry, exits, reason, _ = simulate_signal(
                    sd, rung.signal, rung.quantity, config=self.fills, costs=self.costs,
                    open_minute=self.open_minute, close_minute=self.close_minute,
                    official_close=close,
                )  # fmt: skip
                rung.entry = entry
                rung.status = "filled" if rung.filled >= rung.quantity else "partial"
            rung.sold = rung.filled
            rung.trade = trade_from_fills(
                self.day, sd, rung.signal, rung.quantity, entry, exits, reason, self.costs
            )
            self.trades.append(rung.trade)
            self._log(self.close_minute, "closed", rung.symbol, tag=rung.signal.tag,
                      price=rung.trade.exit_price, net=rung.trade.net)  # fmt: skip
        self.finished = True
        self.minute = self.close_minute
        self.curve.append((self.close_minute, sum(t.net for t in self.trades)))
        self._log(self.close_minute, "session", "", trades=len(self.trades),
                  net=sum(t.net for t in self.trades))  # fmt: skip
        return self.trades

    def _auction(self, rung: Rung, sd: SymbolDay, close: float | None) -> Fill:
        forced = close is None
        price = close if close is not None else float(sd.close[-1])
        slip = self.costs.auction_slippage(price=price, shares=rung.filled, forced=forced)
        return Fill(rung.symbol, "sell", "auction", self.close_minute, price, rung.filled, slip)

    # -- reading the book ------------------------------------------------------------------
    def last_price(self, symbol: str) -> float | None:
        return self._last.get(symbol)

    def marked_pnl(self) -> float:
        """Open positions at the last traded price, before exit costs."""
        if self.finished:
            return sum(t.net for t in self.trades)
        total = 0.0
        for rung in self.rungs:
            last = self._last.get(rung.symbol)
            if rung.held > 0 and last is not None:
                total += rung.held * last - rung.entry_value * rung.held / rung.filled
        return total

    def capital_in_use(self) -> float:
        start = (self.minute or self.open_minute) + 1
        return sum(r.reserve for r in self.rungs if self._reserves(r, start))

    def _log(self, minute: int, kind: str, symbol: str, **details) -> None:
        self.events.append({"minute": minute, "kind": kind, "symbol": symbol, **details})
