from datetime import date

from kinn import run as runner
from kinn.engine.intraday.data import DayView, make_symbol_day
from kinn.engine.intraday.strategy import check_no_lookahead, day_signals

PRIOR = {"prev_close": 10.0, "adv20_prev": 5_000_000.0, "filings_prev": 0}


def view(symbols):
    out = {}
    for k, (name, bars, prior) in enumerate(symbols):
        m, c = zip(*bars, strict=True)
        out[name] = make_symbol_day(name, k, m, c, c, c, c, [1000] * len(m), {**PRIOR, **prior})
    return DayView(date(2015, 1, 5), 570, 960, dict(sorted(out.items())))


def all_signals(v, **params):
    strategy = runner.load_strategy("rebound_limit", params)
    found = day_signals(strategy, v)
    check_no_lookahead(strategy, v, found, range(571, 955, 2))
    return found


def signals(v, **params):
    return {s.symbol: s for s in all_signals(v, **params)}


DROP = [(570, 10.0), (620, 9.8), (640, 8.9), (700, 9.2)]


def test_limit_price_and_expiry():
    got = signals(view([("AAA", DROP, {})]), limit_offset=0.01, rest_minutes=10)
    s = got["AAA"]
    assert (s.minute, s.limit_price, s.expire_minute) == (640, 8.81, 650)


def test_filters():
    slow = [(570, 10.0), (600, 9.5), (625, 9.2), (640, 8.9)]  # only 3% in the last 15 minutes
    v = view([("FAST", DROP, {}), ("SLOW", slow, {}), ("THIN", DROP, {"adv20_prev": 1e6})])
    assert set(signals(v)) == {"FAST", "SLOW", "THIN"}
    assert set(signals(v, min_adv=1e7)) == set()
    assert set(signals(v, min_drop_15m=0.05)) == {"FAST", "THIN"}
    assert set(signals(v, last_minute=630)) == set()


def test_calm_session_filter_counts_earlier_events_only():
    names = [(f"S{k:02d}", [(570, 10.0), (600 + k, 8.9)], {}) for k in range(14)]
    got = signals(view(names), max_prior_events=10)
    assert sorted(got) == [f"S{k:02d}" for k in range(11)]  # the 12th event onwards is skipped


def test_exits_and_minimum_price_are_settings():
    v = view([("AAA", DROP, {}), ("CHEAP", [(m, c / 4) for m, c in DROP], {"prev_close": 2.5})])
    plain = signals(v)["AAA"]
    assert (plain.target_pct, plain.stop_pct, plain.max_hold_minutes) == (None, None, None)
    got = signals(v, target_pct=0.05, stop_pct=0.07, max_hold_minutes=60, min_price=5.0)
    assert set(got) == {"AAA"}  # CHEAP's previous close is under $5
    s = got["AAA"]
    assert (s.target_pct, s.stop_pct, s.max_hold_minutes) == (0.05, 0.07, 60)


def test_market_cap_floor_drops_small_and_unknown_companies():
    v = view([
        ("BIG", DROP, {"marketcap_prev": 5e8}),
        ("SMALL", DROP, {"marketcap_prev": 2e8}),
        ("UNKNOWN", DROP, {}),
    ])  # fmt: skip
    assert set(signals(v)) == {"BIG", "SMALL", "UNKNOWN"}
    assert set(signals(v, min_marketcap=3e8)) == {"BIG"}
    assert set(signals(v, max_marketcap=3e8)) == {"SMALL"}


def test_no_order_below_the_minimum_limit_price():
    cheap = [(m, c / 9) for m, c in DROP]  # previous close 1.11, event bar close about 0.99
    v = view([("AAA", DROP, {}), ("CHEAP", cheap, {"prev_close": 10 / 9})])
    assert set(signals(v, limit_offset=0.04)) == {"AAA", "CHEAP"}
    assert signals(v, limit_offset=0.04)["CHEAP"].limit_price < 1
    assert set(signals(v, limit_offset=0.04, min_limit_price=1.0)) == {"AAA"}
    # In a ladder only the rungs under the minimum are dropped.
    edge = [(m, c * 0.118) for m, c in DROP]  # event bar close about 1.05
    v = view([("EDGE", edge, {"prev_close": 1.18})])
    rungs = all_signals(v, ladder=[[0.04, 0.5], [0.08, 0.5]], min_limit_price=1.0)
    assert [s.tag for s in rungs] == ["o4"] and rungs[0].limit_price >= 1.0


def test_a_ladder_sends_one_order_per_rung_and_the_simulator_admits_them_together():
    import pytest

    from kinn.costs import model as cost_model
    from kinn.engine.intraday.data import DayData
    from kinn.engine.intraday.simulator import FillConfig, simulate_day
    from kinn.risk.sizing import RiskConfig

    # After the event at 640 (close 8.90) the price trades down to 8.40, then recovers.
    bars = [(570, 10.0), (620, 9.8), (640, 8.9), (643, 8.4), (700, 9.2), (959, 9.3)]
    v = view([("AAA", bars, {})])
    found = all_signals(v, ladder=[[0.04, 0.5], [0.08, 0.5]])
    assert [(s.limit_price, s.weight, s.tag) for s in found] == [
        (8.54, 0.5, "o4"), (8.19, 0.5, "o8"),
    ]  # fmt: skip
    with pytest.raises(ValueError):
        all_signals(v, ladder=[[0.04, 0.5], [0.08, 0.4]])
    result = simulate_day(
        DayData(v, {"AAA": 9.3}), found,
        risk=RiskConfig(equity=20_000, position_dollars=2_000, buying_power=20_000),
        config=FillConfig(participation=1.0, flatten_before_close=0),
        costs=cost_model.load("ibkr_pro_tiered"),
    )  # fmt: skip
    # The 4% rung fills (8.40 is through 8.54); the 8% rung does not (8.40 is above 8.19).
    assert (result.signals, result.unfilled, result.rejected_capital) == (2, 1, 0)
    (trade,) = result.trades
    assert (trade.tag, trade.entry_price, trade.quantity) == ("o4", 8.54, int(1000 / 8.54))
