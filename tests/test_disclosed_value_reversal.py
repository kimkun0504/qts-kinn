"""Public-disclosure eligibility, exact ablation, replay and next-minute execution."""

from dataclasses import replace
from datetime import date

import pytest

from kinn import run as runner
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals, input_sessions
from kinn.features.base import LookaheadError
from tests.test_filing_aware_dislocation import DAY, EXPECTED, TARGET
from tests.test_filing_aware_dislocation import session as price_session
from tests.test_insider_price_reclaim import PURCHASE

NAME = "disclosed_value_reversal"


def strategy(primary=True):
    return runner.load_strategy(NAME, {"require_purchase": primary})


def session(*, filings=(PURCHASE,), **kwargs):
    return replace(price_session(**kwargs), disclosures={"ABC": filings})


def eligible(filings):
    st = strategy()
    return st.signals.__func__.__globals__["material_purchase"](session(), "ABC", filings)


def test_material_floor_original_role_and_duplicate_deduplication():
    assert eligible((replace(PURCHASE, purchase_amount=100_000),))
    assert eligible((PURCHASE, PURCHASE))
    assert eligible((replace(PURCHASE, officer=False, director=True),))
    small = replace(PURCHASE, purchase_amount=50_000)
    assert not eligible((small, small))
    assert not eligible((small, replace(small, accession="other")))


@pytest.mark.parametrize(
    "changes",
    [
        {"filed": DAY},
        {"filed": date(2016, 12, 3)},
        {"symbol": "OTHER"},
        {"document_type": "4/A"},
        {"transaction_code": "S"},
        {"acquired": "D"},
        {"officer": False, "director": False, "ten_percent_owner": True},
        {"accession": ""},
        {"accession": None},
        {"issuer_cik": ""},
        {"issuer_cik": None},
        {"purchase_amount": None},
        {"purchase_amount": float("nan")},
        {"purchase_amount": float("inf")},
        {"purchase_amount": 99_999.99},
        {"shares": None},
        {"shares": 0},
        {"shares": float("nan")},
    ],
)
def test_unavailable_future_invalid_or_ineligible_disclosures_do_not_select(changes):
    assert not eligible((replace(PURCHASE, **changes),))
    view = session(filings=(replace(PURCHASE, **changes),))
    assert not day_signals(strategy(), view)
    assert day_signals(strategy(False), view) == EXPECTED


@pytest.mark.parametrize(
    "changes", [{"shares": 11_999}, {"purchase_amount": 50_000}, {"issuer_cik": "other"}]
)
def test_conflicting_valid_duplicate_or_issuer_fails_closed(changes):
    assert not eligible((PURCHASE, replace(PURCHASE, **changes)))
    if "issuer_cik" in changes:
        assert not eligible((PURCHASE, replace(PURCHASE, accession="other", **changes)))


def test_no_purchase_price_reference_and_stale_transaction_fields_not_used():
    # Shares can change the disclosed price proxy; no price reference enters this definition.
    assert day_signals(strategy(), session(filings=(replace(PURCHASE, shares=1.0),))) == EXPECTED
    assert day_signals(strategy(), session(filings=(replace(PURCHASE, shares=1e9),))) == EXPECTED
    # A same-day conflicting record is not known and cannot invalidate yesterday's public one.
    assert eligible((PURCHASE, replace(PURCHASE, filed=DAY, purchase_amount=1.0)))


def test_primary_control_subset_and_all_price_prefixes_keep_all_peers():
    view = session()
    assert len(view.disclosures) == 1 and len(view.symbols) == 31
    for primary in (True, False):
        st = strategy(primary)
        assert input_sessions(st, "form4") == 20
        assert day_signals(st, view) == EXPECTED
        check_no_lookahead(st, view, EXPECTED, list(range(580, 724)))
    no_purchase = session(filings=())
    assert not day_signals(strategy(), no_purchase)
    assert day_signals(strategy(False), no_purchase) == EXPECTED


def test_archive_warmup_applies_to_both_variants():
    early = replace(session(), day=date(2006, 1, 31))
    assert not day_signals(strategy(), early)
    assert not day_signals(strategy(False), early)
    ready = replace(
        session(),
        day=date(2006, 2, 1),
        disclosures={"ABC": (replace(PURCHASE, filed=date(2006, 1, 31)),)},
    )
    assert day_signals(strategy(), ready) == EXPECTED


def test_first_price_event_is_not_changed_by_disclosures():
    view = session(target=[*TARGET, (730, 10), (744, 8.5), (745, 8.6), (746, 8.7)])
    for primary in (True, False):
        assert day_signals(strategy(primary), view) == EXPECTED
    assert not day_signals(strategy(), replace(view, disclosures={}))


def test_deliberate_future_price_lookup_is_caught():
    base = strategy()

    class Cheater(type(base)):
        def signals(self, view, features):
            found = super().signals(view, features)
            return found if len(view.symbols["ABC"].minute) > 4 else []

    st = Cheater(True)
    view = session()
    with pytest.raises(LookaheadError):
        check_no_lookahead(st, view, day_signals(st, view), [600])


@pytest.mark.parametrize(("entry", "close_minute"), [(601, 960), (602, 960), (601, 700)])
def test_next_clock_minute_expiry_and_two_hour_exit_with_auction_fallback(entry, close_minute):
    from kinn.costs.model import load
    from kinn.engine.intraday.data import DayData
    from kinn.engine.intraday.simulator import FillConfig, simulate_day
    from kinn.risk.sizing import RiskConfig

    meta, config = runner.load_config(NAME, "development")
    view = session(target=[*TARGET[:3], (entry, 8.7), TARGET[-1]], close_minute=close_minute)
    trades = simulate_day(
        DayData(view, {"ABC": 9.2}),
        day_signals(strategy(), view),
        risk=RiskConfig(**config["risk"]),
        config=FillConfig(**config["fills"]),
        costs=load(meta["cost_calibration"]),
    ).trades
    if entry == 602:
        assert not trades
    else:
        (trade,) = trades
        assert trade.entry_minute == 601
        assert (trade.exit_minute, trade.exit_reason) == (
            (721, "time") if close_minute == 960 else (700, "auction")
        )


def test_configs_and_parameter_contract_are_frozen():
    _, dev = runner.load_config(NAME, "development")
    _, control = runner.load_config(NAME, "development_control")
    _, validation = runner.load_config(NAME, "validation")
    assert control == {**dev, "params": {"require_purchase": False}}
    assert validation == {**dev, "period": {"start": "2017-01-03", "end": "2023-11-08"}}
    assert strategy().universe.min_adv20 == 1e6
    assert strategy().universe.min_marketcap == 50e6 and strategy().universe.max_marketcap == 2e9
    for params in ({"require_purchase": 1}, {"lookback": 5}):
        with pytest.raises(ValueError, match="frozen boolean"):
            runner.load_strategy(NAME, params)
