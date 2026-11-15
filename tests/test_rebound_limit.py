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


def signals(v, **params):
    strategy = runner.load_strategy("rebound_limit", params)
    found = day_signals(strategy, v)
    check_no_lookahead(strategy, v, found, range(571, 955, 2))
    return {s.symbol: s for s in found}


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
