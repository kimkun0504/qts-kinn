"""Check filing eligibility, the disclosed-price reclaim and execution timing."""

from dataclasses import replace
from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Disclosure, Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals
from kinn.risk.sizing import RiskConfig

NAME = "insider_price_reclaim"
DAY = date(2016, 12, 2)
PURCHASE = Disclosure(
    accession="original",
    issuer_cik="issuer",
    issuer_name="ABC, Inc.",
    symbol="ABC",
    filed=date(2016, 12, 1),
    document_type="4",
    transaction_code="P",
    acquired="A",
    shares=12_000,
    amount=120_000,
    purchase_amount=120_000,
    owner_cik="person",
    owner_name="Buyer",
    officer=True,
    director=False,
    ten_percent_owner=False,
    title="CEO",
)
ROWS = [(570, 10.0, 7_000), (573, 9.35, 7_000), (574, 9.5, 7_000), (575, 9.6, 7_000)]
LATER = [(576, 9.65, 8_000), (578, 9.36, 8_000), (579, 9.61, 8_000), (950, 10.1, 8_000)]
EXPECTED = [Signal("ABC", 575, expire_minute=576)]


def session(rows=ROWS, *, filings=(PURCHASE,), prior_close=10.0):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC",
        1,
        minutes,
        prices,
        prices,
        prices,
        prices,
        sizes,
        {"prev_close": prior_close, "adv20_prev": 2e6},
    )
    return DayView(DAY, 570, 960, {"ABC": stock}, disclosures={"ABC": filings})


def test_first_completed_reclaim_passes_prefix_replay():
    strategy = runner.load_strategy(NAME, {})
    assert strategy.inputs == {"form4": {"sessions": 1}}
    view = session([(550, 9.0, 900_000), *ROWS, *LATER])
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(574)) == []
    assert day_signals(strategy, view.upto(575)) == EXPECTED
    check_no_lookahead(strategy, view, found, [550, 570, 574, 575, 576, 579, 950])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"filings": ()},
        {"filings": (replace(PURCHASE, filed=DAY),)},
        {"filings": (replace(PURCHASE, document_type="4/A"),)},
        {"filings": (replace(PURCHASE, transaction_code="A"),)},
        {"filings": (replace(PURCHASE, symbol="XYZ"),)},
        {"filings": (replace(PURCHASE, officer=False, ten_percent_owner=True),)},
        {"filings": (replace(PURCHASE, purchase_amount=99_999),)},
        {"filings": (replace(PURCHASE, shares=0),)},
        {"filings": (PURCHASE, replace(PURCHASE, shares=13_000))},
        {"filings": (PURCHASE, replace(PURCHASE, accession="other", issuer_cik="wrong"))},
        {"prior_close": 11.1},
        {"rows": [(570, 9.5, 7_000), *ROWS[1:]]},
        {"rows": [(550, 9.0, 900_000), ROWS[0], *ROWS[2:]]},
        {"rows": ROWS[1:]},
        {"rows": [*ROWS[:2], ROWS[-1]]},
        {"rows": [*ROWS[:-1], (575, 9.8, 7_000)]},
        {"rows": [*ROWS[:-1], (575, 9.6, 3_000)]},
        {"rows": [*ROWS[:-2], (780, 9.5, 7_000), (781, 9.6, 7_000)]},
    ],
)
def test_requires_valid_disclosure_and_intraday_washout_then_reclaim(kwargs):
    assert day_signals(runner.load_strategy(NAME, {}), session(**kwargs)) == []


def test_largest_single_purchase_selects_the_reference():
    strategy = runner.load_strategy(NAME, {})
    larger = replace(PURCHASE, accession="larger", purchase_amount=165_000, shares=15_000)
    assert day_signals(strategy, session(filings=(PURCHASE, larger))) == []
    assert day_signals(strategy, session(filings=(PURCHASE, PURCHASE))) == EXPECTED


@pytest.mark.parametrize(("entry_minute", "exit_reason"), [(576, "auction"), (577, None)])
def test_can_only_enter_on_next_clock_minute_and_flattens_at_auction(entry_minute, exit_reason):
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, (entry_minute, 9.65, 8_000), LATER[-1]])
    trades = simulate_day(
        DayData(view, {"ABC": 10.2}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if exit_reason:
        (trade,) = trades
        assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (576, 960, exit_reason)
    else:
        assert trades == []


def test_development_and_validation_configs_differ_only_by_dates():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
