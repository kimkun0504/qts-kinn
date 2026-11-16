"""Verify relative pricing, pre-open selection and synchronous lookahead replay."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals

NAME = "relative_dislocation_reversal"
TARGET = [(585, 10), (599, 8.5), (600, 8.6), (601, 8.0), (910, 14.0)]
EXPECTED = Signal("ABC", 600, expire_minute=601)


def stock(name, perma, rows, cap, adv, volume):
    minute, price = zip(*rows, strict=True)
    return make_symbol_day(
        name,
        perma,
        minute,
        price,
        price,
        price,
        price,
        [volume] * len(minute),
        {"marketcap_prev": cap, "adv20_prev": adv},
    )


def view(
    target=TARGET,
    *,
    peer_count=30,
    peer_at_600=100,
    first_peer_minute=585,
    adv=10e6,
    cap=500e6,
    volume=5_000,
):
    symbols = {
        f"P{i:02d}": stock(
            f"P{i:02d}",
            i + 1,
            [(first_peer_minute, 100), (600, peer_at_600), (620, 20), (910, 200)],
            50e9,
            50e6,
            10_000,
        )
        for i in range(peer_count)
    }
    symbols["ABC"] = stock("ABC", 100, target, cap, adv, volume)
    return DayView(date(2016, 12, 2), 570, 960, symbols)


def test_market_reference_is_available_at_the_same_clock_minute():
    strategy = runner.load_strategy(NAME, {})
    session = view()
    found = day_signals(strategy, session)
    assert found == [EXPECTED]
    assert day_signals(strategy, session.upto(599)) == []
    assert day_signals(strategy, session.upto(600)) == found
    check_no_lookahead(strategy, session, found, [584, 585, 599, 600, 601, 620, 910])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"peer_count": 29},
        {"peer_at_600": 97},  # a -14% stock move is only -11 pp relative to the market
        {"first_peer_minute": 584},  # no stale reference prices
        {"target": [(584, 10), *TARGET[1:]]},  # no stale stock prices either
        {"target": [TARGET[0], (598, 8.5), *TARGET[2:]]},  # no preceding-minute close
        {"target": [TARGET[0], (599, 8.55), *TARGET[2:]]},  # insufficient recovery
        {"adv": 4.9e6},
        {"cap": 2e9},
        {"volume": 4_000},
    ],
)
def test_requires_valid_relative_price_recovery_and_participation(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), view(**kwargs)) == []


def test_configs_differ_only_in_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation


def test_absolute_liquidity_admits_mid_caps_and_does_not_change_price_signal():
    session = view(cap=4e9, adv=10e6)
    assert day_signals(runner.load_strategy(NAME, {}), session) == []
    liquid = runner.load_strategy(NAME, {"liquid_cohort": True})
    found = day_signals(liquid, session)
    assert found == [EXPECTED]
    check_no_lookahead(liquid, session, found, [599, 600, 601, 910])
    assert day_signals(liquid, view(cap=4e9, adv=9.9e6)) == []
    assert day_signals(liquid, view(cap=10e9, adv=10e6)) == []


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_liquid_variant_only_changes_the_cohort(phase):
    _, original = runner.load_config(NAME, phase)
    _, liquid = runner.load_config(NAME, f"{phase}_liquid")
    assert liquid.pop("params") == {"liquid_cohort": True}
    assert liquid == original
