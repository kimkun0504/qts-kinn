import importlib.util
import random
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np

from kinn import after_hours_paper as ahp

TOOL = Path(__file__).resolve().parents[1] / "tools" / "owner" / "paper_after_hours.py"


def ms(day: date, minute: int) -> int:
    """Milliseconds since the epoch of a New York minute of ``day``."""
    local = datetime(day.year, day.month, day.day, minute // 60, minute % 60, tzinfo=ahp.NEW_YORK)
    return int(local.timestamp() * 1000)


def research_reading(minute, high, low, price, volume, accepted):
    """research/claude/after_hours.py, collect() and collect_lows(), for one stock and one
    after-close filing, copied line for line (numpy arrays of one day's bars)."""
    regular = np.flatnonzero((minute >= 570) & (minute <= 960))
    if not len(regular):
        return None
    last_price = price[regular[-1]]
    at = min(max(accepted + 30, 990), 1170)
    base, session = last_price, minute > 960
    k = int(np.searchsorted(minute, at)) - 1
    e = k + 1
    if k < 0 or not session[k] or e >= len(minute) or not session[e] or minute[e] > at + 20:
        return None
    traded = float(np.dot(price[: k + 1] * session[: k + 1], volume[: k + 1]))
    return {
        "reaction": price[k] / base - 1,
        "traded": traded,
        "entry": float(low[e]),
        "entry_high": float(high[e]),
        "entry_dollars": float(price[e] * volume[e]),
    }


def test_the_reading_is_the_research_reading():
    rng = random.Random(7)
    day = date(2019, 7, 30)
    checked = 0
    for _ in range(400):
        minutes = sorted(rng.sample(range(560, 1200), rng.randint(5, 120)))
        bars, rows = [], []
        for m in minutes:
            close = rng.uniform(5, 50)
            low, high = close * rng.uniform(0.95, 1), close * rng.uniform(1, 1.05)
            volume = rng.choice([10, 100, 1000, 20000])
            bars.append({"t": ms(day, m), "o": close, "h": high, "l": low, "c": close, "v": volume})
            rows.append((m, high, low, close, volume))
        accepted = rng.randint(960, 1110)
        mine = ahp.reading(ahp.minute_bars(bars, day), accepted)
        arr = [np.array([r[i] for r in rows], dtype=float) for i in range(5)]
        theirs = research_reading(*arr, accepted)
        assert (mine is None) == (theirs is None)
        if mine is not None:
            checked += 1
            for name in theirs:
                assert abs(mine[name] - theirs[name]) < 1e-9, name
    assert checked > 50


def test_results_filings_are_the_evening_ones_in_new_york_time():
    subs = {
        "filings": {
            "recent": {
                "form": ["8-K", "8-K", "8-K", "8-K/A", "8-K", "10-Q", "8-K"],
                "items": ["2.02,9.01", "2.02", "7.01", "2.02", "2.02", "", "2.02"],
                "acceptanceDateTime": [
                    "2026-11-17T21:05:00.000Z",  # 16:05 New York (standard time)
                    "2026-11-17T20:59:00.000Z",  # 15:59
                    "2026-11-17T21:30:00.000Z",  # not results
                    "2026-11-17T21:10:00.000Z",  # an amendment
                    "2026-11-17T23:31:00.000Z",  # 18:31, too late
                    "2026-11-17T21:00:00.000Z",
                    "2026-11-17T23:30:00.000Z",  # 18:30
                ],
                "accessionNumber": ["a", "b", "c", "d", "e", "f", "g"],
            }
        }
    }
    found = ahp.results_filings(subs, date(2026, 11, 17))
    assert [(f["accession"], f["minute"]) for f in found] == [("a", 965), ("g", 1110)]
    summer = {
        "filings": {
            "recent": {
                "form": ["8-K"],
                "items": ["2.02"],
                "acceptanceDateTime": ["2026-07-28T20:05:00.000Z"],
                "accessionNumber": ["x"],
            }
        }
    }
    assert ahp.results_filings(summer, date(2026, 7, 28))[0]["minute"] == 965  # 16:05 daylight time


def test_daily_index_keeps_8ks_only():
    text = """Form Type   Company Name      CIK   Date Filed  File Name
---------------------------------------------------------------------
10-Q        ACME CORP         1111  20261117    edgar/data/1111/0001-26-000001.txt
8-K         BETA INC          2222  20261117    edgar/data/2222/0002-26-000002.txt
8-K/A       GAMMA INC         3333  20261117    edgar/data/3333/0003-26-000003.txt
8-K         DELTA CO          4444  20261117    edgar/data/4444/0004-26-000004.txt
8-K         BETA INC          2222  20261117    edgar/data/2222/0002-26-000005.txt
"""
    assert ahp.daily_index_8k(text) == [2222, 4444]


def test_signal_tests_and_reasons():
    read = {"reaction": -0.2, "traded": 80_000.0, "entry_high": 12.0}
    assert ahp.is_signal(read, 5e8, 3e6) == (True, "signal")
    assert not ahp.is_signal(None, 5e8, 3e6)[0]
    assert "outside" in ahp.is_signal(read, 2.5e9, 3e6)[1]
    assert "250,000" in ahp.is_signal(read, 5e8, 1e5)[1]
    assert "under $50,000" in ahp.is_signal({**read, "traded": 10_000.0}, 5e8, 3e6)[1]
    assert "not down 15%" in ahp.is_signal({**read, "reaction": -0.1}, 5e8, 3e6)[1]


def test_settle_charges_the_research_costs():
    out = ahp.settle(entry=10.0, next_open=9.0, adv=5e6)
    assert abs(out["gross"] - 0.10) < 1e-12
    cost = 0.0010 + 2 * 0.00035 + 0.10 / 252
    assert abs(out["net"] - (0.10 - cost)) < 1e-12


def test_held_to_1530_crosses_the_spread():
    day = date(2026, 11, 18)
    bars = ahp.minute_bars(
        [
            {"t": ms(day, m), "h": p, "l": p, "c": p, "v": 100}
            for m, p in ((570, 9.0), (929, 8.5), (931, 8.0))
        ],
        day,
    )
    assert ahp.price_at(bars, 930) == 8.5
    out = ahp.settle_held(entry=10.0, price=8.5, adv=5e6)
    assert abs(out["net_1530"] - (0.15 - 0.0018 - 2 * 0.00035 - 0.10 / 252)) < 1e-12


def test_ledger_records_an_evening_once_and_reports(tmp_path, monkeypatch):
    monkeypatch.setenv("KINN_PAPER_DIR", str(tmp_path))
    folder = ahp.paper_dir(tmp_path / "runs")
    state = ahp.load_state(folder)
    signal = {
        "day": "2026-11-17",
        "symbol": "ABCD",
        "cik": 1,
        "accepted": "16:05",
        "market_cap": 8e8,
        "adv": 4e6,
        "reaction": -0.21,
        "entry": 10.0,
        "entry_dollars": 3000.0,
        "next_open": None,
        "gross": None,
        "net": None,
        "borrow": None,
    }
    ahp.record(
        state,
        date(2026, 11, 17),
        [signal],
        [{"day": "2026-11-17", "symbol": "ABCD", "why": "signal"}],
    )
    ahp.record(
        state,
        date(2026, 11, 17),
        [signal],
        [{"day": "2026-11-17", "symbol": "ABCD", "why": "signal"}],
    )
    assert len(state["signals"]) == 1 and state["evenings"] == ["2026-11-17"]
    assert ahp.pending(state) == [signal]
    signal.update(ahp.settle(10.0, 9.5, 4e6))
    ahp.save(folder, state)
    page = (folder / "report.md").read_text()
    assert "ABCD" in page and "| yes |" in page and "made money" in page
    assert ahp.load_state(folder)["signals"][0]["net"] > 0


def test_tool_finds_a_signal_from_fetched_answers(monkeypatch):
    spec = importlib.util.spec_from_file_location("paper_after_hours", TOOL)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    day = date(2026, 11, 17)
    monkeypatch.setattr(tool, "index_ciks", lambda d, agent: [42] if d == day else [])
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    subs = {
        "tickers": ["ABCDW", "ABCD"],
        "filings": {
            "recent": {
                "form": ["8-K"],
                "items": ["2.02,9.01"],
                "acceptanceDateTime": ["2026-11-17T21:05:00.000Z"],
                "accessionNumber": ["acc"],
            }
        },
    }
    monkeypatch.setattr(tool.tool, "get_json", lambda url, host, headers: subs)
    bars = [
        {"t": ms(day, 959), "h": 20.0, "l": 20.0, "c": 20.0, "v": 1000},
        {"t": ms(day, 990), "h": 16.0, "l": 15.5, "c": 15.8, "v": 5000},
        {"t": ms(day, 996), "h": 15.9, "l": 15.6, "c": 15.7, "v": 400},
    ]

    def massive(route, key, **query):
        if "/minute/" in route:
            return {"results": bars}
        if "/range/1/day/" in route:
            return {"results": [{"vw": 20.0, "v": 100_000, "o": 15.0}] * 20}
        if "ABCDW" in route:
            return {"results": {"type": "WARRANT"}}
        return {"results": {"type": "CS", "market_cap": 8e8}}

    monkeypatch.setattr(tool.tool, "massive", massive)
    signals, seen = tool.evening(day, "key", "me@x")
    assert [s["symbol"] for s in signals] == ["ABCD"] and seen[0]["why"] == "signal"
    assert abs(signals[0]["reaction"] + 0.21) < 1e-9 and signals[0]["entry"] == 15.6
    assert tool.next_open("ABCD", day, "key") == 15.0
    assert (
        tool.last_evening(datetime(2026, 11, 18, 9, 40, tzinfo=UTC).astimezone(ahp.NEW_YORK)) == day
    )
