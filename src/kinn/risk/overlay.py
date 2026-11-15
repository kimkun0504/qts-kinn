"""Risk rules that act across sessions, applied to a finished run's trades.

Sessions are simulated independently, so a rule that only decides *whether to trade a session*
can be applied afterwards without changing any trade inside the sessions it keeps.
"""

from __future__ import annotations

from datetime import date

from kinn.core.types import Trade


def circuit_breaker(
    sessions: list[date], trades: list[Trade], *, loss: float, window: int = 20, pause: int = 10
) -> tuple[list[Trade], int]:
    """Stop trading for ``pause`` sessions after the last ``window`` traded sessions lost at
    least ``loss`` dollars (net, 1x slippage). Decided at each close for the following sessions,
    so it uses only past results. Returns (trades kept, sessions paused)."""
    by_day: dict[date, list[Trade]] = {}
    for trade in trades:
        by_day.setdefault(trade.day, []).append(trade)
    kept: list[Trade] = []
    history: list[float] = []
    pause_left = paused = 0
    for day in sorted(sessions):
        if pause_left > 0:
            pause_left -= 1
            paused += 1
            continue
        todays = by_day.get(day, [])
        kept.extend(todays)
        history.append(sum(t.net for t in todays))
        if sum(history[-window:]) <= -loss:
            pause_left = pause
            history = []  # start again from a clean record after the pause
    return kept, paused
