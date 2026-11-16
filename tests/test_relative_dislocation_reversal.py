"""Verify relative pricing, pre-open selection and synchronous lookahead replay."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

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
    peer_at_599=None,
    first_peer_minute=585,
    adv=10e6,
    cap=500e6,
    volume=5_000,
):
    peer_rows = [(first_peer_minute, 100)]
    if peer_at_599 is not None:
        peer_rows.append((599, peer_at_599))
    peer_rows.extend([(600, peer_at_600), (620, 20), (910, 200)])
    symbols = {
        f"P{i:02d}": stock(
            f"P{i:02d}",
            i + 1,
            peer_rows,
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


def test_one_hour_exit_uses_the_first_fill_clock():
    meta, config = runner.load_config(NAME, "development_liquid_one_hour")
    strategy = runner.load_strategy(NAME, config["params"])
    session = view(target=[*TARGET[:-1], (660, 9.0), (661, 9.1), TARGET[-1]])
    found = day_signals(strategy, session)
    assert found == [Signal("ABC", 600, expire_minute=601, max_hold_minutes=60)]
    check_no_lookahead(strategy, session, found, [599, 600, 601, 660, 661])
    result = simulate_day(
        DayData(session, {"ABC": 14.0}),
        found,
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (601, 661, "time")
    assert trade.exit_price == pytest.approx(9.1)


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_one_hour_config_only_changes_the_exit(phase):
    _, close_variant = runner.load_config(NAME, f"{phase}_liquid")
    _, one_hour = runner.load_config(NAME, f"{phase}_liquid_one_hour")
    assert one_hour["params"].pop("one_hour_exit") is True
    assert one_hour == close_variant


def test_peer_recovery_demands_relative_strength_and_synchronous_endpoints():
    kwargs = {"liquid_cohort": True, "one_hour_exit": True}
    baseline = runner.load_strategy(NAME, kwargs)
    strategy = runner.load_strategy(NAME, {**kwargs, "peer_recovery": True})
    gate = {"cap": 4e9, "adv": 10e6}
    expected = Signal("ABC", 600, expire_minute=601, max_hold_minutes=60)
    flat = view(**gate, peer_at_599=100)
    found = day_signals(strategy, flat)
    assert found == [expected]
    check_no_lookahead(strategy, flat, found, [585, 599, 600, 601, 910])
    common_bounce = view(**gate, peer_at_599=99)
    assert day_signals(baseline, common_bounce) == [expected]
    assert day_signals(strategy, common_bounce) == []
    assert day_signals(strategy, view(**gate)) == []


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_peer_recovery_config_only_changes_the_confirmation(phase):
    _, base = runner.load_config(NAME, f"{phase}_liquid_one_hour")
    _, variant = runner.load_config(NAME, f"{phase}_liquid_peer_recovery")
    assert variant["params"].pop("peer_recovery") is True
    assert variant == base


def test_quiet_baseline_uses_only_closes_before_the_dislocation():
    strategy = runner.load_strategy(
        NAME, {"liquid_cohort": True, "one_hour_exit": True, "quiet_baseline": True}
    )
    earlier = [(m, 10.0) for m in range(575, 586)]
    expected = Signal("ABC", 600, expire_minute=601, max_hold_minutes=60)
    quiet = view([*earlier, *TARGET[1:]])
    found = day_signals(strategy, quiet)
    assert found == [expected]
    check_no_lookahead(strategy, quiet, found, [575, 585, 599, 600, 601, 910])
    assert day_signals(strategy, view([(575, 9.5), *earlier[1:], *TARGET[1:]])) == []
    assert day_signals(strategy, view([*earlier[3:], *TARGET[1:]])) == []


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_quiet_baseline_config_only_changes_the_pre_shock_condition(phase):
    _, base = runner.load_config(NAME, f"{phase}_liquid_one_hour")
    _, variant = runner.load_config(NAME, f"{phase}_liquid_quiet_baseline")
    assert variant["params"].pop("quiet_baseline") is True
    assert variant == base


@pytest.mark.parametrize(
    ("close_minute", "exit_minute", "exit_reason", "exit_price"),
    [(960, 721, "time", 9.1), (700, 700, "auction", 14.0)],
)
def test_two_hour_peer_recovery_exit_uses_the_entry_clock_and_stays_intraday(
    close_minute, exit_minute, exit_reason, exit_price
):
    meta, config = runner.load_config(NAME, "development_liquid_peer_recovery_two_hour")
    strategy = runner.load_strategy(NAME, config["params"])
    full = view(target=[*TARGET[:-1], (720, 9.0), (721, 9.1), TARGET[-1]], peer_at_599=100)
    session = DayView(full.day, full.open_minute, close_minute, full.symbols)
    found = day_signals(strategy, session)
    assert found == [Signal("ABC", 600, expire_minute=601, max_hold_minutes=120)]
    check_no_lookahead(strategy, session, found, [599, 600, 601, close_minute - 1])
    result = simulate_day(
        DayData(session, {"ABC": 14.0}),
        found,
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (
        601,
        exit_minute,
        exit_reason,
    )
    assert trade.exit_price == pytest.approx(exit_price)


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_two_hour_peer_recovery_config_only_changes_the_exit(phase):
    _, base = runner.load_config(NAME, f"{phase}_liquid_peer_recovery")
    _, variant = runner.load_config(NAME, f"{phase}_liquid_peer_recovery_two_hour")
    assert base["params"].pop("one_hour_exit") is True
    assert variant["params"].pop("two_hour_exit") is True
    assert variant == base


def test_ten_point_quiet_baseline_changes_only_the_shock_threshold():
    _, standard = runner.load_config(NAME, "development_liquid_quiet_baseline")
    _, lower = runner.load_config(NAME, "development_liquid_quiet_ten_point")
    base = runner.load_strategy(NAME, standard["params"])
    variant = runner.load_strategy(NAME, lower["params"])
    earlier = [(m, 10.0) for m in range(575, 586)]
    medium = view([*earlier, (599, 8.82), (600, 8.95), *TARGET[3:]])
    found = day_signals(variant, medium)
    assert found == [Signal("ABC", 600, expire_minute=601, max_hold_minutes=60)]
    assert day_signals(base, medium) == []
    small = view([*earlier, (599, 8.90), (600, 9.02), *TARGET[3:]])
    assert day_signals(variant, small) == []
    turbulent = view([(575, 10.4), *earlier[1:], (599, 8.82), (600, 8.95), *TARGET[3:]])
    assert day_signals(variant, turbulent) == []
    check_no_lookahead(variant, medium, found, [575, 585, 599, 600, 601, 910])


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_ten_point_config_is_otherwise_identical_to_quiet_baseline(phase):
    _, base = runner.load_config(NAME, f"{phase}_liquid_quiet_baseline")
    _, variant = runner.load_config(NAME, f"{phase}_liquid_quiet_ten_point")
    assert variant["params"].pop("min_dislocation_pp") == 10
    assert variant == base


@pytest.mark.parametrize(
    ("count", "previous", "current", "qualifies"),
    [
        (30, 100, 100, True),
        (29, 100, 100, False),
        (30, 95, 95, False),
        (30, 99, 100, False),
        (30, None, 100, False),
    ],
)
def test_size_reference_uses_own_group_at_both_clock_endpoints(count, previous, current, qualifies):
    _, config = runner.load_config(NAME, "development_liquid_size_peers")
    strategy = runner.load_strategy(NAME, config["params"])
    initial = view(peer_at_599=100)
    rows = [(585, 100), (600, current)]
    if previous is not None:
        rows.insert(1, (599, previous))
    matched = {
        f"S{i:02d}": stock(f"S{i:02d}", 200 + i, rows, 500e6, 10e6, 10_000) for i in range(count)
    }
    midsize = {
        f"M{i:02d}": stock(
            f"M{i:02d}", 300 + i, [(585, 100), (599, 90), (600, 90)], 4e9, 10e6, 10_000
        )
        for i in range(60)
    }
    session = DayView(
        initial.day,
        initial.open_minute,
        initial.close_minute,
        {**initial.symbols, **matched, **midsize},
    )
    found = day_signals(strategy, session)
    expected = [Signal("ABC", 600, expire_minute=601, max_hold_minutes=120)] if qualifies else []
    assert found == expected
    check_no_lookahead(strategy, session, found, [585, 599, 600, 601, 910])


@pytest.mark.parametrize("phase", ["development", "validation"])
def test_size_reference_config_only_changes_the_reference(phase):
    _, base = runner.load_config(NAME, f"{phase}_liquid_peer_recovery_two_hour")
    _, variant = runner.load_config(NAME, f"{phase}_liquid_size_peers")
    assert variant["params"].pop("size_peers") is True
    assert variant == base
