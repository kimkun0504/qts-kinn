"""Check public filing availability, the opening confirmation and next-bar fills."""

from dataclasses import replace
from datetime import date

import pytest

from kinn import run as runner
from kinn.core.types import Disclosure, Signal
from kinn.costs.model import load
from kinn.engine.intraday.data import DayData, DayView, make_symbol_day
from kinn.engine.intraday.simulator import FillConfig, simulate_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals, form4_sessions
from kinn.risk.sizing import RiskConfig

NAME = "form4_opening_confirmation"
DAY = date(2016, 12, 2)
PURCHASE = Disclosure(
    accession="example-1",
    issuer_cik="1234",
    issuer_name="Example Inc.",
    symbol="ABC",
    filed=date(2016, 12, 1),
    document_type="4",
    transaction_code="P",
    acquired="A",
    shares=10_000,
    amount=100_000,
    purchase_amount=100_000,
    owner_cik="123",
    owner_name="Example",
    officer=True,
    director=False,
    ten_percent_owner=False,
    title="CEO",
)
ROWS = [(570, 10.0, 7_000), (582, 10.1, 5_000), (583, 10.3, 7_000), (584, 10.4, 7_000)]
LATER = [(585, 10.5, 8_000), (950, 11.1, 10_000)]
EXPECTED = [Signal("ABC", 584, expire_minute=585)]


def session(rows=ROWS, *, filings=(PURCHASE,), adv=2e6):
    minutes, prices, sizes = zip(*rows, strict=True)
    stock = make_symbol_day(
        "ABC", 1, minutes, prices, prices, prices, prices, sizes, {"adv20_prev": adv}
    )
    return DayView(DAY, 570, 960, {"ABC": stock}, {"ABC": filings})


def test_open_confirmation_passes_prefix_replay():
    strategy = runner.load_strategy(NAME, {})
    assert form4_sessions(strategy) == 1
    view = session([(550, 2.0, 900_000), *ROWS, *LATER])
    found = day_signals(strategy, view)
    assert found == EXPECTED
    assert day_signals(strategy, view.upto(583)) == []
    assert day_signals(strategy, view.upto(584)) == EXPECTED
    check_no_lookahead(strategy, view, found, [550, 570, 583, 584, 585, 950])


@pytest.mark.parametrize(
    "filings",
    [
        (),
        (replace(PURCHASE, filed=DAY),),
        (replace(PURCHASE, filed=date(2016, 12, 5)),),
        (replace(PURCHASE, document_type="4/A"),),
        (replace(PURCHASE, transaction_code="S", acquired="D"),),
        (replace(PURCHASE, transaction_code="M"),),
        (replace(PURCHASE, purchase_amount=None),),
        (replace(PURCHASE, issuer_cik=""),),
        (replace(PURCHASE, purchase_amount=50_000),) * 2,
        (PURCHASE, replace(PURCHASE, purchase_amount=60_000)),
        (PURCHASE, replace(PURCHASE, accession="example-2", issuer_cik="9999")),
    ],
)
def test_uses_only_distinct_eligible_original_disclosures(filings):
    assert day_signals(runner.load_strategy(NAME, {}), session(filings=filings)) == []


def test_distinct_filings_contribute_to_the_same_issuer():
    first = replace(PURCHASE, purchase_amount=50_000)
    second = replace(first, accession="example-2")
    assert day_signals(runner.load_strategy(NAME, {}), session(filings=(first, second))) == EXPECTED


@pytest.mark.parametrize(
    ("rows", "adv"),
    [
        (ROWS[1:], 2e6),
        ([*ROWS[:2], ROWS[-1]], 2e6),
        (ROWS[:-1], 2e6),
        ([*ROWS[:2], (583, 10.1, 7_000), ROWS[-1]], 2e6),
        ([*ROWS[:-1], (584, 10.4, 3_000)], 2e6),
        ([(550, 2.0, 900_000), *ROWS], 3e6),
    ],
)
def test_requires_regular_open_turnover_and_two_confirming_bars(rows, adv):
    assert day_signals(runner.load_strategy(NAME, {}), session(rows, adv=adv)) == []


def test_order_enters_next_minute_and_exits_at_the_close():
    meta, config = runner.load_config(NAME, "development")
    strategy = runner.load_strategy(NAME, config["params"])
    view = session([*ROWS, *LATER])
    result = simulate_day(
        DayData(view, {"ABC": 11.2}),
        day_signals(strategy, view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    )
    (trade,) = result.trades
    assert (trade.entry_minute, trade.exit_minute, trade.exit_reason) == (585, 960, "auction")


def test_config_differs_only_in_the_date_range():
    _, development = runner.load_config(NAME, "development")
    _, validation = runner.load_config(NAME, "validation")
    assert development.pop("period") == {"start": date(2003, 9, 10), "end": date(2016, 12, 30)}
    assert validation.pop("period") == {"start": date(2017, 1, 3), "end": date(2023, 11, 8)}
    assert development == validation
