"""What a strategy is, and the check that it does not look ahead.

A strategy is thin: a universe, a list of features, and a function from one session's view to
signals. It owns no data loading, costs or fills.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from kinn.core.types import Signal
from kinn.data.inputs import NAMES as INPUT_NAMES
from kinn.data.universe import Universe
from kinn.engine.intraday.data import DayView
from kinn.features.base import Feature, LookaheadError, compute

FeatureValues = Mapping[str, Mapping[str, Any]]  # symbol -> feature name -> value(s)


class Strategy(Protocol):
    """``inputs`` is optional: a strategy that reads a versioned input declares it, e.g.
    ``inputs = {"form4": {"sessions": 5}}`` for five sessions of insider disclosures in
    ``view.disclosures``, or ``inputs = {"form8k": {"sessions": 1}}`` for the 8-K filings that
    became usable this morning in ``view.reports``. The run records each input's version in
    its manifest."""

    name: str
    universe: Universe
    features: Sequence[Feature]

    def signals(self, view: DayView, features: FeatureValues) -> list[Signal]: ...


def input_sessions(strategy: Strategy, name: str) -> int:
    """How many sessions of a versioned input the strategy asked for (0: none)."""
    wanted = getattr(strategy, "inputs", None) or {}
    unknown = set(wanted) - set(INPUT_NAMES)
    if unknown:
        raise ValueError(f"unknown inputs {sorted(unknown)}; there are {list(INPUT_NAMES)}")
    if name in ("form8k_timed", "nbbo_replenishment") and name in wanted:
        options = wanted[name] or {}
        value = options.get("sessions", 1)
        if set(options) - {"sessions"} or type(value) is not int or value != 1:
            raise ValueError(f"{name} supports only sessions=1 (current session)")
    return int((wanted[name] or {}).get("sessions", 1)) if name in wanted else 0


def form4_sessions(strategy: Strategy) -> int:
    """How many sessions of Form 4 disclosures the strategy asked for (0: none)."""
    return input_sessions(strategy, "form4")


def form8k_sessions(strategy: Strategy) -> int:
    """How many sessions of 8-K filings the strategy asked for (0: none)."""
    return input_sessions(strategy, "form8k")


def form8k_timed_sessions(strategy: Strategy) -> int:
    """Current-session original 8-K timestamps, with per-minute availability."""
    return input_sessions(strategy, "form8k_timed")


def nbbo_replenishment_sessions(strategy: Strategy) -> int:
    """Current-session snapshot pairs for the complete registered price population."""
    return input_sessions(strategy, "nbbo_replenishment")


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
        expected = {s for s in signals if s.minute <= cut}
        # Signals the replay stamps after the cut are plans made without seeing those bars
        # (a scheduled entry, say); only the ones up to the cut are compared.
        if {s for s in replay if s.minute <= cut} != expected:
            changed = sorted(
                {s for s in replay if s.minute <= cut} ^ expected,
                key=lambda s: (s.minute, s.symbol),
            )[0]
            raise LookaheadError(
                f"{strategy.name} on {view.day}: signals up to minute {cut} change when later "
                f"bars are removed (first difference: {changed.symbol} at {changed.minute}). "
                "The strategy or one of its features uses information before it is available."
            )
