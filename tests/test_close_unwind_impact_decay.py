"""Test the after-hours score independently of the pending execution adapter."""

from importlib.util import module_from_spec, spec_from_file_location
from math import log
from pathlib import Path

import numpy as np
import pytest

from kinn.engine.intraday.data import make_symbol_day

SOURCE = Path(__file__).resolve().parents[1] / "strategies/close_unwind_impact_decay/formula.py"
SPEC = spec_from_file_location("close_unwind_formula", SOURCE)
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
WINDOW = np.array([9.8, 9.6, 9.4, 9.0, 8.98, 8.95, 8.97])
VOLUME = np.full(7, 10_000)
REGULAR = [(570, 9.4, 10_000), (900, 10.3, 10_000), (959, 10.0, 10_000)]


def stock(rows=None):
    after = [(961 + i, price, 10_000) for i, price in enumerate(WINDOW)]
    selected = [*REGULAR, *after, (968, 8.98, 10_000), (1015, 9.9, 10_000)]
    minute, price, shares = zip(*(selected if rows is None else rows), strict=True)
    return make_symbol_day("ABC", 1, minute, price, price, price, price, shares)


def test_score_matches_its_discount_and_impact_definition():
    old_dollars = 10_000 * (9.6 + 9.4 + 9.0)
    new_dollars = 10_000 * (8.98 + 8.95)
    old_impact = log(9.8 / 9.0) / old_dollars
    new_impact = log(9.0 / 8.97) / new_dollars
    expected = (1 - 8.97 / 10.0) * (1 - new_impact / old_impact)
    result = MODULE.impact_decay_score(WINDOW, VOLUME, 10.0)
    assert result == pytest.approx(expected)
    assert result > 0.04
    assert MODULE.impact_decay_score(WINDOW, 2 * VOLUME, 10.0) == pytest.approx(result)


@pytest.mark.parametrize(
    ("prices", "shares", "reference"),
    [
        (np.r_[WINDOW[:-1], float("nan")], VOLUME, 10.0),
        (WINDOW, np.r_[VOLUME[:-1], 0], 10.0),
        (WINDOW, VOLUME, float("nan")),
        (WINDOW, VOLUME, 0),
        (np.array([9.1, 9.05, 9.02, 9.0, 8.98, 8.95, 8.97]), VOLUME, 10.0),
        (WINDOW, VOLUME, 9.5),
        (np.r_[WINDOW[:-1], 8.955], VOLUME, 10.0),
        (WINDOW, np.r_[VOLUME[:-1], 1_000], 10.0),
        (WINDOW, np.array([10_000, 10_000, 10_000, 10_000, 1_000, 1_000, 10_000]), 10.0),
        (np.array([9.8, 9.6, 9.4, 9.0, 9.01, 9.02, 9.04]), VOLUME, 10.0),
    ],
)
def test_rejects_missing_prices_inactive_turnover_and_unconfirmed_pressure(
    prices, shares, reference
):
    assert MODULE.impact_decay_score(prices, shares, reference) is None


def test_shape_errors_identify_an_incomplete_window():
    with pytest.raises(ValueError, match="seven"):
        MODULE.impact_decay_score(WINDOW[:-1], VOLUME[:-1], 10.0)


def test_first_candidate_is_stable_when_later_bars_are_removed():
    bars = stock()
    expected = MODULE.first_candidate(bars, 8.5, 960)
    assert expected is not None and expected[0] == 967
    for cut in (570, 900, 959, 961, 966):
        assert MODULE.first_candidate(bars.upto(cut), 8.5, 960) is None
    for cut in (967, 968, 1015):
        assert MODULE.first_candidate(bars.upto(cut), 8.5, 960) == expected


def test_future_after_hours_rally_cannot_satisfy_regular_rally_screen():
    rows = [(570, 8.5, 10_000), (959, 8.6, 10_000)]
    rows.extend((961 + i, price, 10_000) for i, price in enumerate(WINDOW))
    rows.append((1015, 15.0, 100_000))
    assert MODULE.first_candidate(stock(rows), 8.5, 960) is None


def test_rejects_early_close_and_missing_minute():
    assert MODULE.first_candidate(stock(), 8.5, 780) is None
    after = [(961 + i, price, 10_000) for i, price in enumerate(WINDOW) if i != 2]
    assert MODULE.first_candidate(stock([*REGULAR, *after]), 8.5, 960) is None


def test_boundary_auction_bar_and_late_window_cannot_enter():
    for shift in (-1, 54):
        after = [(961 + i + shift, price, 10_000) for i, price in enumerate(WINDOW)]
        assert MODULE.first_candidate(stock([*REGULAR, *after]), 8.5, 960) is None
