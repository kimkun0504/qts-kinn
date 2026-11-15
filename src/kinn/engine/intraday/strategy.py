"""What a strategy is, and the check that it does not look ahead.

A strategy is thin: a universe, a list of features, and a function from one session's view to
signals. It owns no data loading, costs or fills.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from kinn.core.types import Signal
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.features.base import Feature, LookaheadError, compute

FeatureValues = Mapping[str, Mapping[str, Any]]  # symbol -> feature name -> value(s)


class Strategy(Protocol):
    name: str
    universe: Universe
    features: Sequence[Feature]

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]: ...


def compute_features(strategy: Strategy, view: DayView) -> dict[str, dict[str, Any]]:
    return {s: compute(strategy.features, sd) for s, sd in view.symbols.items()}


def day_signals(strategy: Strategy, view: DayView) -> list[Signal]:
    signals = strategy.signals(view, compute_features(strategy, view))
    for signal in signals:
        if signal.symbol not in view.symbols:
            raise KeyError(f"{strategy.name}: signal for {signal.symbol}, not in the universe")
    return signals


def check_no_lookahead(
    strategy: Strategy, view: DayView, signals: list[Signal], cut_minutes: Sequence[int]
) -> None:
    """Replay the session cut off at each minute; the earlier signals must not change.

    If the strategy (or any feature it uses) peeks at later bars, the signals it produced up to
    the cut differ once those bars are removed. That raises ``LookaheadError``.
    """
    for cut in cut_minutes:
        replay = day_signals(strategy, view.upto(cut))
        late = [s for s in replay if s.minute > cut]
        if late:
            raise LookaheadError(
                f"{strategy.name} on {view.day}: a signal is stamped minute {late[0].minute} "
                f"but only bars up to {cut} existed ({late[0].symbol})"
            )
        expected = {s for s in signals if s.minute <= cut}
        if set(replay) != expected:
            changed = sorted(set(replay) ^ expected, key=lambda s: (s.minute, s.symbol))[0]
            raise LookaheadError(
                f"{strategy.name} on {view.day}: signals up to minute {cut} change when later "
                f"bars are removed (first difference: {changed.symbol} at {changed.minute}). "
                "The strategy or one of its features uses information before it is available."
            )
