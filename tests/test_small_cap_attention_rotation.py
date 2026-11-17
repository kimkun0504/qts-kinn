"""Check leader timing, laggard selection and same-session execution."""

from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "small_cap_attention_rotation"
DAY = date(2016, 12, 2)
LEADER = [(570, 10, 30_000), (599, 11.1, 30_000)]
LAGGARD = [(570, 10, 6_000), (599, 10, 6_000), (613, 10.45, 6_000), (614, 10.50, 6_000)]
EXPECTED = [Signal("ABC", 614, expire_minute=615, max_hold_minutes=60)]


def stock(symbol, identifier, rows, *, ret60=-0.25, prev=10, adv=1e6):
    minutes, prices, volumes = zip(*rows, strict=True)
    return make_symbol_day(
        symbol,
        identifier,
        minutes,
        prices,
        prices,
        prices,
        prices,
        volumes,
        {"ret60_prev": ret60, "prev_close": prev, "adv20_prev": adv},
    )


def session(
    laggard=LAGGARD,
    *,
    leader=LEADER,
    ids=(2, 3, 4),
    ret60=-0.25,
    lead_ret60=-0.25,
    prev=10,
    adv=1e6,
    close_minute=960,
):
    members = {"ABC": stock("ABC", 1, laggard, ret60=ret60, prev=prev, adv=adv)}
    for symbol, identifier in zip(("AA", "BB", "CC"), ids, strict=False):
        members[symbol] = stock(symbol, identifier, leader, ret60=lead_ret60)
    return DayView(DAY, 570, close_minute, members)


def test_staggered_rotation_uses_three_other_early_leaders_and_passes_replay():
    strategy = runner.load_strategy(NAME, {})
    view = session(
        [*LAGGARD, (615, 11.0, 8_000), (951, 12.0, 9_000)],
        leader=[*LEADER, (614, 7.0, 900_000)],
    )
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(613)) == []
    assert day_signals(strategy, view.upto(614)) == EXPECTED
    check_no_lookahead(strategy, view, found, [570, 599, 613, 614, 615, 951])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ids": (2, 3)},
        {"ids": (2, 2, 4)},
        {"ids": (1, 3, 4)},
        {"leader": [LEADER[0], (598, 11.1, 30_000), (600, 13.0, 900_000)]},
        {"leader": [LEADER[0], (599, 10.9, 30_000)]},
        {"leader": [(565, 11.1, 900_000), LEADER[0], (599, 11.1, 1_000)]},
        {"lead_ret60": -0.10},
        {"ret60": float("nan")},
        {"ret60": -0.10},
        {"prev": 9.0},
        {"adv": 2e6},
        {"laggard": LAGGARD[1:]},
        {"laggard": [LAGGARD[0], (599, 10.3, 6_000), *LAGGARD[2:]]},
        {"laggard": [*LAGGARD[:2], LAGGARD[-1]]},
        {"laggard": [*LAGGARD[:2], (613, 10.1, 6_000), LAGGARD[-1]]},
        {"laggard": [*LAGGARD[:-1], (614, 11.2, 6_000)]},
        {"laggard": [*LAGGARD[:2], (613, 10.45, 10_000), (614, 10.5, 3_000)]},
        {"close_minute": 688},
    ],
)
def test_rejects_invalid_leader_or_laggard(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


@pytest.mark.parametrize("entry", [615, 616])
def test_next_minute_expiry_and_one_hour_exit(entry):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*LAGGARD, (entry, 10.6, 8_000), (675, 10.9, 8_000)])
    trades = simulate_day(
        DayData(view, {"ABC": 11.1}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 615:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (615, 675, "time")
    else:
        assert trades == []


def test_development_and_validation_configs_differ_only_by_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
