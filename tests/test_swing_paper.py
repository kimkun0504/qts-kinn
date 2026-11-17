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


# ---- The quality test in the ledger ----


def test_the_years_return_needs_250_sessions_behind_the_close():
    assert swing_paper.year_return([10.0] * 250 + [12.0]) == pytest.approx(0.2)
    assert swing_paper.year_return([5.0] + [10.0] * 250 + [8.0]) == pytest.approx(-0.2)
    assert swing_paper.year_return([10.0] * 250) is None and swing_paper.year_return([]) is None


def _facts(**tags):
    """Company facts with one value a tag: {tag: [(balance date, filed, value, form), ...]}."""
    return {"facts": {"us-gaap": {
        tag: {"units": {"USD": [{"end": end, "filed": filed, "val": val, "form": form}
                                for end, filed, val, form in rows]}}
        for tag, rows in tags.items()}}}  # fmt: skip


Q2, Q3 = ("2026-06-30", "2026-08-05"), ("2026-09-30", "2026-11-04")


def test_net_cash_uses_the_latest_balance_sheet_filed_before_the_signal():
    facts = _facts(
        CashAndCashEquivalentsAtCarryingValue=[(*Q2, 50e6, "10-Q"), (*Q3, 40e6, "10-Q")],
        LongTermDebtNoncurrent=[(*Q2, 10e6, "10-Q"), (*Q3, 30e6, "10-Q")],
        LongTermDebtCurrent=[(*Q3, 5e6, "10-Q")],
        OperatingLeaseLiabilityCurrent=[(*Q3, 2e6, "10-Q")],
        OperatingLeaseLiabilityNoncurrent=[(*Q3, 8e6, "10-Q")],
    )
    after = swing_paper.net_cash(facts, date(2026, 11, 6))
    assert after == {"period": "2026-09-30", "cash": 40e6, "debt": 35e6, "leases": 10e6,
                     "net_cash": -5e6}  # fmt: skip
    # On the day the third quarter is filed it is not yet usable: the second quarter stands.
    before = swing_paper.net_cash(facts, date(2026, 11, 4))
    assert before["period"] == "2026-06-30" and before["net_cash"] == 40e6
    assert swing_paper.net_cash(facts, date(2026, 8, 5)) is None  # nothing filed before that
    assert swing_paper.net_cash({}, date(2026, 11, 6)) is None


def test_debt_tagged_in_overlapping_ways_is_not_added_twice():
    facts = _facts(
        Cash=[(*Q3, 20e6, "10-Q")],
        LongTermDebt=[(*Q3, 30e6, "10-Q")],  # the total, current part included
        LongTermDebtNoncurrent=[(*Q3, 25e6, "10-Q")],
        LongTermDebtCurrent=[(*Q3, 5e6, "10-Q")],
        DebtCurrent=[(*Q3, 5e6, "10-Q")],
        ConvertibleNotesPayable=[(*Q3, 12e6, "10-Q")],  # part of the long-term debt
        CashAndCashEquivalentsAtCarryingValue=[("2026-09-30", "2026-11-04", 99e6, "8-K")],
    )
    balance = swing_paper.net_cash(facts, date(2026, 11, 6))
    assert balance["debt"] == 30e6 and balance["cash"] == 20e6  # the 8-K's figure is not used
    restated = _facts(Cash=[(*Q3, 20e6, "10-Q"), ("2026-09-30", "2026-11-05", 22e6, "10-Q/A")])
    assert swing_paper.net_cash(restated, date(2026, 11, 6))["cash"] == 22e6


def test_a_quality_book_takes_only_signals_that_pass_and_the_report_says_why():
    books = {"all": {"account": 2000, "slots": 2},
             "quality": {"account": 2000, "slots": 2, "skip_fallen_cash_rich": True}}  # fmt: skip
    window = _window({s: _jumper(25) for s in ("AAA", "BBB", "CCC")})
    state = swing_paper.new_state()
    good = {**_signal("AAA", 7), **swing_paper.quality(0.3, {"net_cash": 5e6})}
    bad = {**_signal("BBB", 9), **swing_paper.quality(-0.4, {"net_cash": 5e6})}
    unknown = _signal("CCC", 8)  # recorded before the facts were collected
    assert good["kept"] and not bad["kept"]
    assert swing_paper.quality(-0.4, {"net_cash": -1.0})["kept"]  # net debt is enough
    assert not swing_paper.quality(None, None)["kept"]

    def step(i, signals=()):
        return swing_paper.step(state, window, DAYS[i], list(signals), hold=RULE.hold,
                                books=books, costs=COSTS, allowance_bps=[[0, 25]])  # fmt: skip

    said = step(25, [good, bad, unknown])
    assert any("AAA" in line and "passes the quality test: +30% over the year" in line
               for line in said)  # fmt: skip
    page = swing_paper.report(state, window, hold=RULE.hold, books=books)
    assert "**BBB**" in page and "fails the quality test: -40% over the year, net cash $5M" in page
    step(26)
    taken = {t["symbol"]: sorted(t["books"]) for t in state["tracks"]}
    assert taken == {"BBB": ["all"], "CCC": ["all"], "AAA": ["quality"]}  # "all" was full
    for i in (27, 28):
        step(i)
    page = swing_paper.report(state, window, hold=RULE.hold, books=books)
    assert "Signals that passed the quality test: 1 finished" in page
    assert "Signals that failed the quality test: 1 finished" in page
    assert "| quality | 1 |" in page and "| all | 2 |" in page


# ---- A book with the 20-day-average exit ----

TREND = {
    "plain": {"account": 2000, "slots": 1},
    "trend": {"account": 2000, "slots": 1, "exit": {"average": 5, "max_sessions": 6}},
}


def _trend_step(state, window, i, signals=()):
    return swing_paper.step(state, window, DAYS[i], list(signals), hold=RULE.hold, books=TREND,
                            costs=COSTS, allowance_bps=[[0, 25]])  # fmt: skip


def _path(after: list[float], n=40):
    """Flat at 10 to day 23, 11 and 12 on days 24 and 25 (the signal), then ``after``."""
    closes = [10.0] * 24 + [11.0, 12.0] + after
    closes += [closes[-1]] * (n - len(closes))
    return closes, [1e6] * n


def test_the_exponential_average_weights_recent_closes():
    assert swing_paper.ema([10.0], 20) == 10.0
    assert swing_paper.ema([10.0, 10.0, 16.0], 5) == pytest.approx(12.0)  # weight 1/3 on the last
    assert swing_paper.ema([10.0, 16.0, 16.0], 5) == pytest.approx(10 + 6 / 3 + 4 / 3)


def test_a_trend_book_sells_at_the_open_after_a_close_under_the_average():
    # Bought day 26 at 12; closes 12.5, 13, 13.5, then 9 on day 29, under the average.
    window = _window({"AAA": _path([12.5, 13.0, 13.5, 9.0, 9.5, 9.5]), "BBB": _jumper(29),
                      "CCC": _jumper(30)})  # fmt: skip
    state = swing_paper.new_state()
    _trend_step(state, window, 25, [_signal("AAA")])
    for i in (26, 27, 28):
        _trend_step(state, window, i)
    track = state["tracks"][0]
    assert track["status"] == "closed" and track["gross_return"] == pytest.approx(13.5 / 12 - 1)
    assert "net" in track["books"]["plain"]  # the plain book sold after three sessions
    trend = track["books"]["trend"]
    assert trend["open"] and "net" not in trend and not trend.get("leave")
    said = _trend_step(state, window, 29, [_signal("BBB")])  # closes at 9: under its average
    assert trend["open"] and trend["leave"] and not any("AAA" in line for line in said)
    page = swing_paper.report(state, window, hold=RULE.hold, books=TREND)
    assert "## Sell at the next open (closed under its 20-day average)" in page
    assert "- **AAA**, bought 2020-03-28: trend" in page
    assert "| 4 of 3 | trend |" in page  # still held by that book only
    said = _trend_step(state, window, 30, [_signal("CCC")])  # sold at the open, 9 (the prior close)
    assert any("AAA: trend sold at the open (under its average), -25.0%" in line for line in said)
    assert not trend["open"] and trend["exit_day"] == DAYS[30].isoformat()
    assert trend["gross_return"] == pytest.approx(9 / 12 - 1) and trend["net"] < -0.25 * 1992
    # The slot was still taken at that open (BBB could not enter); it is free the day after.
    taken = {t["symbol"]: sorted(t["books"]) for t in state["tracks"]}
    assert taken["BBB"] == ["plain"]
    _trend_step(state, window, 31)
    taken = {t["symbol"]: sorted(t["books"]) for t in state["tracks"]}
    assert taken["CCC"] == ["trend"]  # plain is full with BBB
    page = swing_paper.report(state, window, hold=RULE.hold, books=TREND)
    assert "| trend | 1 |" in page and "| plain | 1 |" in page


def test_a_trend_book_holds_a_riser_to_its_last_session_and_sells_at_that_close():
    rising = [12.0 + 0.5 * i for i in range(1, 12)]
    window = _window({"AAA": _path(rising)})
    state = swing_paper.new_state()
    _trend_step(state, window, 25, [_signal("AAA")])
    for i in range(26, 31):
        _trend_step(state, window, i)
    trend = state["tracks"][0]["books"]["trend"]
    assert trend["open"] and not trend.get("leave")
    page = swing_paper.report(state, window, hold=RULE.hold, books=TREND)
    assert "- **AAA**, bought 2020-03-28: trend" in page.split("## Sell at the next close")[1]
    said = _trend_step(state, window, 31)  # the sixth session after the signal
    assert any("AAA: trend sold at the close (time)" in line for line in said)
    assert trend["gross_return"] == pytest.approx(window[DAYS[31]]["AAA"].close / 12 - 1)
    assert not swing_paper._live(state["tracks"][0])


def test_an_old_ledger_without_exit_fields_still_steps():
    window = _window({"AAA": _jumper(25)})
    state = swing_paper.new_state()
    _step(state, window, 25, [_signal("AAA")])
    _step(state, window, 26)  # recorded by books that have no exit of their own
    for i in (27, 28):
        _trend_step(state, window, i)  # the config now has other books
    track = state["tracks"][0]
    assert track["status"] == "closed" and "net" in track["books"]["one"]
    assert "| plain | 0 |" in swing_paper.report(state, window, hold=RULE.hold, books=TREND)
