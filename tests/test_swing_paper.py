"""The paper ledger of the earnings drift: the same signals as the engine, and the bookkeeping."""

from __future__ import annotations

from datetime import date, timedelta

import pyarrow as pa
import pytest

from kinn import swing_paper, swing_run
from kinn.costs import model as cost_model
from kinn.swing_paper import Bar
from kinn.swing_run import Rule

RULE = Rule(jump=0.15, volume=5, cap_min=5e7, cap_max=3e8, hold=3)
DAYS = [date(2020, 3, 2) + timedelta(days=i) for i in range(40)]  # consecutive, for simplicity
BOOKS = {"one": {"account": 2000, "slots": 1}, "two": {"account": 2000, "slots": 2}}
COSTS = cost_model.load("ibkr_pro_tiered")


def _window(stocks: dict[str, tuple[list[float], list[float]]]) -> swing_paper.Window:
    """{symbol: (closes, dollar volumes)}; each day opens at the previous close."""
    window: swing_paper.Window = {d: {} for d in DAYS}
    for symbol, (closes, volumes) in stocks.items():
        previous = closes[0]
        for day, close, volume in zip(DAYS, closes, volumes, strict=False):
            window[day][symbol] = Bar(previous, min(previous, close), close, volume)
            previous = close
    return window


def _quiet(n=40):
    return [10.0] * n, [1e6] * n


def _jumper(at: int, n=40):
    """Flat at 10, then +10% on day ``at`` - 1 and +9.1% on day ``at`` with 6x volume."""
    closes = [10.0] * (at - 1) + [11.0, 12.0] + [12.0 + 0.5 * i for i in range(1, n - at)]
    volumes = [1e6] * n
    volumes[at - 1] = 6e6
    return closes[:n], volumes


def _signal(symbol, volume=6.0):
    return {"symbol": symbol, "day": DAYS[0], "prev_day": DAYS[0], "jump": 0.2, "volume": volume,
            "adv": 5e5, "close": 12.0, "market_cap": 1e8, "filed": DAYS[0],
            "filing": "x"}  # fmt: skip


def _step(state, window, i, signals=()):
    return swing_paper.step(state, window, DAYS[i], list(signals), hold=RULE.hold, books=BOOKS,
                            costs=COSTS, allowance_bps=[[0, 25]])  # fmt: skip


def test_the_paper_screen_and_the_engine_find_the_same_signal():
    window = _window({"AAA": _jumper(25), "BBB": _quiet()})
    (candidate,) = swing_paper.prescreen(window, DAYS[25], RULE)
    assert candidate["symbol"] == "AAA" and candidate["volume"] == pytest.approx(6.0)
    assert candidate["jump"] == pytest.approx(0.2) and candidate["prev_day"] == DAYS[24]
    assert not swing_paper.prescreen(window, DAYS[24], RULE)
    assert not swing_paper.prescreen(window, DAYS[26], RULE)
    signal, _ = swing_paper.confirm(candidate, kind="CS", market_cap=1e8,
                                    filings=[(DAYS[24], "0001-25-1")], rule=RULE)  # fmt: skip
    assert signal["filing"] == "0001-25-1"
    # The engine, on the same bars as a panel, with the same filing as an event.
    rows, permatickers = [], {"AAA": 1, "BBB": 2}
    for symbol in ("AAA", "BBB"):
        for i, day in enumerate(DAYS):
            bar = window[day][symbol]
            history = sorted(window[d][symbol].dollar_volume for d in DAYS[max(0, i - 20) : i])
            rows.append({
                "date": day, "permaticker": permatickers[symbol], "symbol": symbol,
                "category": "Domestic Common Stock", "open": bar.open, "low": bar.low,
                "close": bar.close, "prev_close": bar.open, "prev_date": day - timedelta(days=1),
                "dollar_volume": bar.dollar_volume, "marketcap_prev": 1e8,
                "adv20_prev": (history[len(history) // 2 - 1] + history[len(history) // 2]) / 2
                if len(history) > 1 and len(history) % 2 == 0
                else (history[len(history) // 2] if history else 0.0),
            })  # fmt: skip
    events = pa.table({"permaticker": [1], "date": [DAYS[24]], "eventcodes": ["22|91"]})
    found = swing_run.find_signals(pa.Table.from_pylist(rows), events, RULE, DAYS[21], DAYS[-1],
                                   DAYS[-1])  # fmt: skip
    assert [(s.symbol, s.day) for s in found] == [("AAA", DAYS[25])]
    assert found[0].volume == pytest.approx(candidate["volume"])


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"kind": "ETF"}, "not common stock"),
        ({"market_cap": 4e7}, "outside the band"),
        ({"market_cap": None}, "no market value"),
        ({"filings": [(DAYS[25], "today")]}, "no earnings 8-K"),  # filed on the signal day itself
        ({"filings": [(DAYS[20], "old")]}, "no earnings 8-K"),
    ],
)
def test_a_candidate_needs_the_right_type_size_and_a_fresh_earnings_filing(change, reason):
    candidate = {"symbol": "AAA", "day": DAYS[25], "prev_day": DAYS[24]}
    inputs = {"kind": "CS", "market_cap": 1e8, "filings": [(DAYS[24], "ok")], **change}
    signal, why = swing_paper.confirm(candidate, rule=RULE, **inputs)
    assert signal is None and reason in why


def test_only_8ks_with_the_earnings_item_count():
    recent = {"form": ["8-K", "8-K", "10-Q", "8-K/A"], "items": ["2.02,9.01", "5.02", "", "2.02"],
              "filingDate": ["2024-05-02", "2024-05-01", "2024-05-02", "2024-05-03"],
              "accessionNumber": ["a", "b", "c", "d"]}  # fmt: skip
    assert swing_paper.earnings_days({"filings": {"recent": recent}}) == [(date(2024, 5, 2), "a")]
    assert swing_paper.earnings_days({}) == []


def test_bars_with_no_price_are_dropped_and_dollar_volume_uses_the_average_price():
    bars = swing_paper.bars_of([{"T": "AAA", "o": 10, "l": 9, "c": 11, "v": 100, "vw": 10.5},
                                {"T": "BBB", "o": 0, "l": 0, "c": 0, "v": 0},
                                {"T": "CCC"}])  # fmt: skip
    assert bars == {"AAA": Bar(10.0, 9.0, 11.0, 1050.0)}


def test_a_signal_is_bought_next_open_held_for_the_hold_and_sold_at_the_close():
    window = _window({"AAA": _jumper(25)})
    state = swing_paper.new_state()
    _step(state, window, 25, [_signal("AAA")])
    (track,) = state["tracks"]
    assert track["status"] == "pending"
    _step(state, window, 26)
    assert track["status"] == "open" and track["entry_open"] == 12.0  # day 26 opens at 12
    assert track["books"]["one"] == {"shares": 166, "notional": 1992.0}
    assert track["books"]["two"]["shares"] == 83
    _step(state, window, 27)
    assert track["status"] == "open"
    _step(state, window, 28)  # the third session after the signal
    assert track["status"] == "closed" and track["exit_day"] == DAYS[28].isoformat()
    growth = window[DAYS[28]]["AAA"].close / 12.0
    assert track["gross_return"] == pytest.approx(growth - 1)
    result = track["books"]["one"]
    slip = 0.0025 * (1992.0 + 1992.0 * growth)
    assert result["net"] - result["net_2x"] == pytest.approx(slip)
    assert result["net"] < 1992.0 * (growth - 1) - slip  # fees too
    with pytest.raises(ValueError, match="not after"):
        _step(state, window, 28)


def test_a_full_book_skips_but_the_signal_is_still_followed():
    window = _window({s: _jumper(25) for s in ("AAA", "BBB", "CCC")})
    state = swing_paper.new_state()
    _step(state, window, 25, [_signal("AAA", 6), _signal("BBB", 9), _signal("CCC", 7)])
    _step(state, window, 26)
    books = {t["symbol"]: sorted(t["books"]) for t in state["tracks"]}
    assert books == {"BBB": ["one", "two"], "CCC": ["two"], "AAA": []}  # most volume first
    for i in (27, 28):
        _step(state, window, i)
    assert all(t["status"] == "closed" for t in state["tracks"])
    page = swing_paper.report(state, window, hold=RULE.hold, books=BOOKS)
    assert "3 finished" in page and "| one | 1 |" in page and "| two | 2 |" in page


def test_a_stock_that_does_not_trade_is_not_entered_and_the_report_lists_orders(tmp_path):
    window = _window({"AAA": _jumper(25)})
    state = swing_paper.new_state()
    _step(state, window, 25, [_signal("AAA"), _signal("GONE")])
    page = swing_paper.report(state, window, hold=RULE.hold, books=BOOKS)
    assert "## Buy at the next open" in page and "**AAA**" in page and "**GONE**" in page
    _step(state, window, 26)
    assert {t["symbol"]: t["status"] for t in state["tracks"]} == {
        "AAA": "open",
        "GONE": "cancelled",
    }
    _step(state, window, 27)
    assert "**AAA**, bought" in swing_paper.report(state, window, hold=RULE.hold, books=BOOKS)
    swing_paper.save(tmp_path / "ledger", state, "page")
    assert swing_paper.load_state(tmp_path / "ledger") == state


def test_the_report_sets_each_trade_beside_the_index_fund():
    window = _window({"AAA": _jumper(25), "IWM": ([100.0 + i for i in range(40)], [1e9] * 40)})
    state = swing_paper.new_state()
    _step(state, window, 25, [_signal("AAA")])
    _step(state, window, 26)
    page = swing_paper.report(state, window, hold=RULE.hold, books=BOOKS)
    fund = window[DAYS[26]]["IWM"].close / window[DAYS[26]]["IWM"].open - 1
    assert f"{100 * fund:+.1f}%" in page and "IWM sold short" in page
    for i in (27, 28):
        _step(state, window, i)
    (track,) = state["tracks"]
    expected = window[DAYS[28]]["IWM"].close / window[DAYS[26]]["IWM"].open - 1
    assert track["benchmark_return"] == pytest.approx(expected)
    assert "Against IWM over the same days (1 trades)" in swing_paper.report(
        state, window, hold=RULE.hold, books=BOOKS
    )
