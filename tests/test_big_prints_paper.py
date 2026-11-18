import importlib.util
import math
import random
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb
import pyarrow as pa

from kinn import big_prints_paper as bpp

TOOL = Path(__file__).resolve().parents[1] / "tools" / "owner" / "paper_big_prints.py"


def weekdays(start: date, n: int) -> list[date]:
    out, day = [], start
    while len(out) < n:
        if day.weekday() < 5:
            out.append(day)
        day += timedelta(days=1)
    return out


def test_measures_match_the_research_sql():
    """The footprint, normal dollar volume and previous close equal the research's window
    functions (research/claude/big_prints.py and the panel's adv20_prev) on random bars,
    including a stock that misses sessions."""
    rng = random.Random(7)
    days = weekdays(date(2026, 1, 5), 75)
    window: bpp.Window = {d: {} for d in days}
    rows = []
    for symbol in ("AAA", "BBB", "CCC"):
        for d in days:
            if symbol == "CCC" and rng.random() < 0.08 and d != days[-1]:
                continue  # a stock that does not trade every session
            bar = bpp.DayBar(
                rng.uniform(5, 20), rng.uniform(5, 20), rng.uniform(1e4, 1e6), rng.randint(10, 900)
            )
            window[d][symbol] = bar
            rows.append((symbol, d, bar.close, bar.volume, bar.transactions))
    table = pa.table(
        {k: [r[i] for r in rows] for i, k in enumerate(("symbol", "date", "close", "volume", "n"))}
    )
    con = duckdb.connect()
    con.register("bars", table)
    expected = {
        r[0]: r[1:]
        for r in con.sql(
            """select symbol,
                      (volume / n) / exp(avg(ln(volume / n)) over (partition by symbol order by date
                          rows between 60 preceding and 1 preceding)),
                      median(close * volume) over (partition by symbol order by date
                          rows between 20 preceding and 1 preceding),
                      lag(close) over (partition by symbol order by date),
                      count(*) over (partition by symbol order by date
                          rows between 60 preceding and 1 preceding),
                      date
               from bars qualify date = (select max(date) from bars)"""
        ).fetchall()
    }
    found = bpp.measures(window, days[-1])
    for symbol, (fp, adv, prev, n, _) in expected.items():
        if n < 60:
            assert symbol not in found
            continue
        m = found[symbol]
        assert math.isclose(m["footprint"], fp, rel_tol=1e-9)
        assert math.isclose(m["adv"], adv, rel_tol=1e-9)
        assert m["prev_close"] == prev


def test_candidates_and_the_index_day_share():
    base = {"footprint": 3.5, "volume_ratio": 2.0, "ret": 0.02, "adv": 400_000.0, "prev_close": 8.0}
    found = {
        "OK": {**base, "symbol": "OK"},
        "FLAT": {**base, "symbol": "FLAT", "footprint": 2.9},
        "JUMP": {**base, "symbol": "JUMP", "ret": 0.05},
        "DOWN": {**base, "symbol": "DOWN", "ret": -0.001},
        "QUIET": {**base, "symbol": "QUIET", "volume_ratio": 1.4},
        "THIN": {**base, "symbol": "THIN", "adv": 200_000.0},
        "CHEAP": {**base, "symbol": "CHEAP", "prev_close": 1.5},
    }
    assert [c["symbol"] for c in bpp.candidates(found)] == ["OK"]
    many = {f"S{i}": {**base, "symbol": f"S{i}", "footprint": 1.0} for i in range(100)}
    many.update({f"B{i}": {**base, "symbol": f"B{i}", "footprint": 2.0} for i in range(5)})
    assert math.isclose(bpp.market_share(many), 5 / 105)


def test_quiet_reads_reaction_sessions():
    sessions = weekdays(date(2026, 11, 9), 8)  # 9 to 18 November
    day = date(2026, 11, 18)

    def at(text):
        return datetime.fromisoformat(text).replace(tzinfo=bpp.NEW_YORK).astimezone(UTC)

    assert not bpp.quiet([at("2026-11-13T17:00")], day, sessions)  # reaction Monday the 16th
    assert bpp.quiet([at("2026-11-12T12:00")], day, sessions)  # reaction the 12th, too early
    assert bpp.quiet([at("2026-11-18T16:30")], day, sessions)  # after the close: tomorrow's
    assert not bpp.quiet([at("2026-11-18T15:00")], day, sessions)
    accepted = ["2026-11-17T20:00:00.000Z", "2026-11-16T14:00:00.000Z"]
    subs = {"filings": {"recent": {"form": ["10-Q", "8-K"], "acceptanceDateTime": accepted}}}
    times = bpp.eight_k_times(subs)
    assert len(times) == 1 and not bpp.quiet(times, day, sessions)


def test_settle_costs_and_benchmark():
    days = weekdays(date(2026, 11, 19), 25)
    signal = {"day": "2026-11-18", "close": 10.0, "adv": 400_000.0}
    bars = [(d, 10.0 if i == 0 else 10.5, 11.0 if i == 19 else 10.5) for i, d in enumerate(days)]
    iwm = [(d, 200.0, 210.0 if i == 19 else 205.0) for i, d in enumerate(days)]
    bpp.settle(signal, bars[:10], iwm, days[9])
    assert signal["entry"] == 10.0 and signal.get("net") is None
    bpp.settle(signal, bars, iwm, days[-1])
    assert signal["exit_day"] == days[19].isoformat()
    assert math.isclose(signal["net"], 0.10 - 2 * (0.00035 + 0.0025))
    assert math.isclose(signal["benchmark"], 0.05)
    assert signal.get("net_40") is None
    longer = weekdays(date(2026, 11, 19), 45)
    bars40 = [(d, 10.0, 12.0 if i == 39 else 10.5) for i, d in enumerate(longer)]
    iwm40 = [(d, 200.0, 220.0 if i == 39 else 205.0) for i, d in enumerate(longer)]
    bpp.settle(signal, bars40, iwm40, longer[-1])
    assert signal["exit_day_40"] == longer[39].isoformat() and math.isclose(
        signal["benchmark_40"], 0.10
    )
    assert math.isclose(signal["net_40"], 0.20 - 2 * (0.00035 + 0.0025))
    assert math.isclose(signal["net"], 0.10 - 2 * (0.00035 + 0.0025))  # the 20-session result stays
    gone = {"day": "2026-11-18", "close": 10.0, "adv": 2e6}
    bpp.settle(gone, bars[:5], iwm, days[-1])
    assert gone["stopped"] and math.isclose(gone["gross"], 0.05)


def test_ledger_record_and_report(tmp_path):
    state = bpp.new_state()
    sig = {"day": "2026-11-17", "symbol": "ABCD", "market_cap": 1.5e8, "footprint": 4.2,
           "ret": 0.02, "volume_ratio": 2.5, "close": 10.0, "adv": 4e5}  # fmt: skip
    bpp.record(state, date(2026, 11, 17), 0.01, [sig], [])
    bpp.record(state, date(2026, 11, 16), 0.07, [], [])
    bpp.record(state, date(2026, 11, 17), 0.01, [dict(sig)], [])
    assert len(state["signals"]) == 1 and [e["day"] for e in state["evenings"]] == [
        "2026-11-16",
        "2026-11-17",
    ]
    page = bpp.report(state)
    assert "ABCD" in page and "Skipped as index days" in page and "2026-11-16" in page
    apart = {**sig, "day": "2026-11-16", "symbol": "WXYZ", "index_day": True, "net": -0.5}
    bpp.record(state, date(2026, 11, 16), 0.07, [apart], [])
    page = bpp.report(state)
    assert "Signals: 1 " in page and "kept apart (not the rule): 1; -50.00% on 1 closed" in page
    assert "2026-11-16 (index day) | WXYZ" in page
    bpp.save(tmp_path, state)
    assert bpp.load_state(tmp_path)["signals"][0]["symbol"] == "ABCD"


def test_tool_finds_a_signal_from_fetched_answers(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("paper_big_prints", TOOL)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    days = weekdays(date(2026, 7, 1), 80)
    day = days[-1]
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)

    def grouped_results(d):
        rows = [
            {"T": f"F{i}", "o": 10.0, "c": 10.0, "v": 50_000 + i, "n": 100} for i in range(1100)
        ]
        last = d == day
        rows.append({"T": "ABCD", "o": 10.0, "c": 10.2 if last else 10.0,
                     "v": 200_000 if last else 50_000, "n": 100 if last else 500})  # fmt: skip
        rows.append({"T": "WRNT", "o": 10.0, "c": 10.2 if last else 10.0,
                     "v": 200_000 if last else 50_000, "n": 100 if last else 500})  # fmt: skip
        return rows

    def massive(route, key, **query):
        if "/grouped/" in route:
            d = date.fromisoformat(route.rsplit("/", 1)[1])
            return {"results": grouped_results(d)} if d in days else {}
        if "WRNT" in route:
            return {"results": {"type": "WARRANT", "cik": 7}}
        return {"results": {"type": "CS", "market_cap": 1.2e8, "cik": 42}}

    monkeypatch.setattr(tool.tool, "massive", massive)
    monkeypatch.setattr(
        tool.tool, "get_json", lambda url, host, headers: {"filings": {"recent": {}}}
    )
    window = tool.window_to(day, "key", tmp_path)
    assert len(window) == tool.SESSIONS and (tmp_path / "bars" / f"{day.isoformat()}.json").exists()
    share, signals, screened = tool.evening(day, window, "key", "me@x")
    assert share < bpp.SHARE_MAX and not any(s.get("index_day") for s in signals)
    assert [s["symbol"] for s in signals] == ["ABCD"] and math.isclose(
        signals[0]["footprint"], 20.0
    )
    assert [s["symbol"] for s in screened] == ["WRNT"] and "common" in screened[0]["why"]
    monkeypatch.setattr(bpp, "SHARE_MAX", 0.0)  # every day an index day: signals kept apart
    _, apart, _ = tool.evening(day, window, "key", "me@x")
    assert [s["symbol"] for s in apart] == ["ABCD"] and apart[0]["index_day"]
    again = tool.window_to(day, "key", tmp_path)  # read back from the ledger's folder
    assert again[day]["ABCD"] == window[day]["ABCD"]
