from dataclasses import replace
from datetime import date, timedelta

from kinn.core.types import Trade
from kinn.risk.overlay import circuit_breaker

BASE = Trade(
    day=date(2020, 1, 1),
    symbol="A",
    permaticker=1,
    quantity=1,
    signal_minute=600,
    entry_minute=601,
    entry_price=10.0,
    exit_minute=960,
    exit_price=10.0,
    exit_reason="auction",
    notional=10.0,
    gross=0.0,
    commission=0.0,
    fees=0.0,
    slippage=0.0,
    net=0.0,
    net_2x=0.0,
)
DAYS = [date(2020, 1, 1) + timedelta(days=i) for i in range(12)]


def trades(nets):
    return [replace(BASE, day=d, net=n) for d, n in zip(DAYS, nets, strict=True)]


def test_breaker_pauses_after_a_losing_window_and_resumes():
    nets = [10, -60, -50, 5, 5, 5, 5, 5, 5, 5, 5, 5]
    kept, paused = circuit_breaker(DAYS, trades(nets), loss=100, window=3, pause=4)
    # Down 100 over the last three sessions at the close of day 3: days 4-7 are skipped.
    assert [t.day for t in kept] == DAYS[:3] + DAYS[7:] and paused == 4


def test_breaker_uses_only_past_sessions_and_can_stay_quiet():
    nets = [10] * 12
    kept, paused = circuit_breaker(DAYS, trades(nets), loss=100, window=3, pause=4)
    assert len(kept) == 12 and paused == 0
    # A loss on the last day cannot remove that day's own trades.
    late = [10] * 11 + [-500]
    kept, paused = circuit_breaker(DAYS, trades(late), loss=100, window=3, pause=4)
    assert len(kept) == 12 and paused == 0
