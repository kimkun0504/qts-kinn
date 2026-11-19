"""Synthetic quote contract and price-control checks; no real quote loader exists yet."""

from dataclasses import dataclass, replace
from types import SimpleNamespace

import pytest

from kinn import run as runner
from kinn.data.quotes import minute_ns
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals, input_sessions
from kinn.features.base import LookaheadError
from tests.test_filing_aware_dislocation import DAY, EXPECTED, session, stock

NAME = "bid_replenishment_reversal"


def quote(timestamp, *, bid=199.5, ask=200.5, bid_size=100, ask_size=100):
    return SimpleNamespace(
        sip_timestamp=timestamp, bid_price=bid, ask_price=ask, bid_size=bid_size, ask_size=ask_size
    )


def pair(minute=600, *, status="available", symbol="ABC", company=100):
    end = minute_ns(DAY, minute + 1)
    return SimpleNamespace(
        day=DAY,
        symbol=symbol,
        permaticker=company,
        minute=minute,
        status=status,
        early=quote(end - 5_000_000_000),
        late=quote(end - 1, bid_size=300),
    )


@dataclass(frozen=True)
class BookView:
    """Proposed prefix behavior only; this is a synthetic contract fixture."""

    base: object
    book_pairs: dict

    def __getattr__(self, name):
        return getattr(self.base, name)

    def upto(self, cut):
        return BookView(
            self.base.upto(cut),
            {s: tuple(p for p in rows if p.minute <= cut) for s, rows in self.book_pairs.items()},
        )


def test_exact_size_and_spread_boundaries_and_unit_invariance():
    p = pair()
    module = runner.load_strategy(NAME, {}).signals.__func__.__globals__
    fn = module["replenishes"]
    assert fn(p.early, p.late)
    assert fn(
        quote(0, bid_size=10_000, ask_size=10_000), quote(1, bid_size=30_000, ask_size=10_000)
    )
    assert not fn(p.early, quote(1, bid_size=299))
    assert not fn(p.early, quote(1, bid_size=300, ask=200.5001))


@pytest.mark.parametrize("failure", ["initial", "growth", "price", "locked", "size", "fraction"])
def test_replenishment_requires_every_registered_component(failure):
    p = pair()
    if failure == "initial":
        p.early.bid_size = 101
    elif failure == "growth":
        p.early.bid_size = p.early.ask_size = 151
    elif failure == "price":
        p.late.bid_price = 199.49
    elif failure == "locked":
        p.late.ask_price = p.late.bid_price
    elif failure == "size":
        p.late.ask_size = 0
    else:
        p.late.bid_size = 300.5
    strategy = runner.load_strategy(NAME, {})
    assert not strategy.signals.__func__.__globals__["replenishes"](p.early, p.late)


def test_freshness_at_nanosecond_boundary_and_postdecision_rejection():
    strategy = runner.load_strategy(NAME, {})
    fn = strategy.signals.__func__.__globals__["valid_pair"]
    p = pair()
    p.late.sip_timestamp -= 1_000_000_000
    assert fn(p, DAY, "ABC", 100, 600)
    p.late.sip_timestamp -= 1
    assert not fn(p, DAY, "ABC", 100, 600)
    p = pair()
    p.late.sip_timestamp += 2
    assert not fn(p, DAY, "ABC", 100, 600)


def test_control_is_available_before_quote_adapter_and_has_fixed_broader_trigger():
    strategy = runner.load_strategy(NAME, {"use_quotes": False})
    data = session(target=[(585, 10), (599, 9.2), (600, 9.3), (601, 9.4), (721, 10)])
    assert not strategy.inputs and day_signals(strategy, data) == EXPECTED
    check_no_lookahead(strategy, data, EXPECTED, [585, 599, 600, 601, 721])
    assert not day_signals(runner.load_strategy("filing_aware_dislocation", {}), data)


def test_primary_subset_and_full_prefixes_using_synthetic_contract():
    primary = runner.load_strategy(NAME, {})
    control = runner.load_strategy(NAME, {"use_quotes": False})
    data = BookView(session(), {"ABC": (pair(),)})
    assert day_signals(primary, data) == day_signals(control, data) == EXPECTED
    check_no_lookahead(primary, data, EXPECTED, list(range(580, 724)))
    bad = BookView(session(), {"ABC": (pair(status="stale"),)})
    assert not day_signals(primary, bad)
    with pytest.raises(ValueError, match="exact first parent"):
        day_signals(primary, BookView(session(), {}))
    with pytest.raises(RuntimeError, match="native nbbo_replenishment"):
        day_signals(primary, session())


def test_failed_first_quote_event_cannot_be_rescued_by_later_quotes():
    minute = [585, 599, 600, 601, 605, 619, 620, 621, 721]
    target = [10, 8.5, 8.6, 8.7, 10, 8.5, 8.6, 8.7, 9.1]
    data = session()
    members = {
        f"P{i:02d}": stock(f"P{i:02d}", i + 1, list(zip(minute, [100] * len(minute), strict=True)))
        for i in range(30)
    }
    members["ABC"] = stock("ABC", 100, list(zip(minute, target, strict=True)))
    data = replace(data, symbols=members)
    quotes = {"ABC": (pair(status="stale"), pair(620))}
    assert day_signals(runner.load_strategy(NAME, {"use_quotes": False}), data) == EXPECTED
    assert not day_signals(runner.load_strategy(NAME, {}), BookView(data, quotes))


def test_checker_catches_a_deliberate_future_pair_lookup():
    base = runner.load_strategy(NAME, {})

    class Cheater(type(base)):
        def signals(self, view, features):
            found = super().signals(view, features)
            return [] if len(view.book_pairs["ABC"]) > 1 else found

    data = BookView(session(), {"ABC": (pair(), pair(900))})
    strategy = Cheater(True)
    with pytest.raises(LookaheadError):
        check_no_lookahead(strategy, data, day_signals(strategy, data), [600])


def test_no_undeclared_native_input_bypass_and_configs_only_choose_declared_cases():
    primary = runner.load_strategy(NAME, {})
    with pytest.raises(ValueError, match="unknown inputs"):
        input_sessions(primary, "nbbo_replenishment")
    _, dev = runner.load_config(NAME, "development")
    _, control = runner.load_config(NAME, "development_control")
    assert control == {**dev, "params": {"use_quotes": False}}
    for params in ({"use_quotes": 1}, {"cutoff": 0.08}):
        with pytest.raises(ValueError, match="frozen boolean"):
            runner.load_strategy(NAME, params)
