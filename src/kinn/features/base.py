"""Features, and the rule that each declares when its value becomes available.

- ``PRIOR_DAY``: known before today's open. Computed from the prior-session columns only; the
  function never receives today's bars.
- ``BAR_CLOSE``: one value per bar, known when that bar closes and usable from the next bar.
  The function must be causal: its value at bar *i* may depend only on bars up to *i*.
  ``check_causal`` enforces that by recomputing on truncated days; the engine runs it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import numpy as np


class Availability(StrEnum):
    PRIOR_DAY = "prior_day"
    BAR_CLOSE = "bar_close"


class LookaheadError(RuntimeError):
    """A feature or strategy used information before it was available."""


@dataclass(frozen=True)
class Feature:
    name: str
    availability: Availability
    fn: Callable[[Any], Any]


def compute(features: Iterable[Feature], symbol_day: Any) -> dict[str, Any]:
    """Feature values for one symbol-day (``kinn.engine.intraday.data.SymbolDay``)."""
    values: dict[str, Any] = {}
    for feature in features:
        if feature.availability is Availability.PRIOR_DAY:
            values[feature.name] = feature.fn(symbol_day.prior)
        else:
            out = np.asarray(feature.fn(symbol_day), dtype=float)
            if out.shape != symbol_day.minute.shape:
                raise ValueError(f"feature {feature.name} must return one value per bar")
            values[feature.name] = out
    return values


def check_causal(feature: Feature, symbol_day: Any, cut_minutes: Iterable[int]) -> None:
    """Raise ``LookaheadError`` if a BAR_CLOSE feature changes when later bars are removed."""
    if feature.availability is not Availability.BAR_CLOSE:
        return
    full = np.asarray(feature.fn(symbol_day), dtype=float)
    for cut in cut_minutes:
        part_day = symbol_day.upto(cut)
        part = np.asarray(feature.fn(part_day), dtype=float)
        if not np.array_equal(full[: len(part)], part, equal_nan=True):
            raise LookaheadError(
                f"feature '{feature.name}' is not causal: its values up to minute {cut} change "
                f"when later bars are removed ({symbol_day.symbol})"
            )


def prior(name: str, column: str | None = None) -> Feature:
    """A PRIOR_DAY feature that reads one prior-session column."""
    key = column or name
    return Feature(name, Availability.PRIOR_DAY, lambda p, k=key: _get(p, k))


def _get(prior_columns: Mapping[str, float], key: str) -> float:
    value = prior_columns.get(key)
    return float("nan") if value is None else float(value)
