import gzip
import importlib.util
import io
import random
import urllib.error
import zlib
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pytest

from kinn import after_hours_paper as ahp

TOOL = Path(__file__).resolve().parents[1] / "tools" / "owner" / "paper_after_hours.py"
AGENT = "Kun Kim kun@example.com"
INDEX = """Description:           Daily Index of EDGAR Dissemination Feed by Form Type
Last Data Received:    November 17, 2026

Form Type   Company Name      CIK   Date Filed  File Name
---------------------------------------------------------------------
10-Q        ACME CORP         1111  20261117    edgar/data/1111/0001-26-000001.txt
8-K         BETA INC          2222  20261117    edgar/data/2222/0002-26-000002.txt
8-K/A       GAMMA INC         3333  20261117    edgar/data/3333/0003-26-000003.txt
8-K         DELTA CO          4444  20261117    edgar/data/4444/0004-26-000004.txt
8-K         BETA INC          2222  20261117    edgar/data/2222/0002-26-000005.txt
"""


def load_tool():
    spec = importlib.util.spec_from_file_location("paper_after_hours", TOOL)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    return tool


class Answer:
    def __init__(self, body: bytes, encoding: str | None = None):
        self.body = body
        self.headers = {"Content-Encoding": encoding} if encoding else {}

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


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
    assert ahp.daily_index_8k(INDEX) == [2222, 4444]


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
    seen = [{"day": "2026-11-17", "cik": 1, "symbol": "ABCD", "why": "signal"}]
    ahp.record(state, date(2026, 11, 17), [signal], seen, filers=300)
    ahp.record(state, date(2026, 11, 17), [dict(signal)], seen, filers=300)
    assert len(state["signals"]) == 1 and len(state["seen"]) == 1
    assert state["evenings"] == ["2026-11-17"] and state["signals"][0] is signal
    assert not ahp.needs_reading(state, date(2026, 11, 17))
    assert ahp.pending(state) == [signal]
    signal.update(ahp.settle(10.0, 9.5, 4e6))
    ahp.save(folder, state)
    page = (folder / "report.md").read_text()
    assert "ABCD" in page and "| yes |" in page and "made money" in page
    assert ahp.load_state(folder)["signals"][0]["net"] > 0


def test_tool_finds_a_signal_from_fetched_answers(monkeypatch):
    tool = load_tool()
    day = date(2026, 11, 17)
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
    signals, seen, done = tool.evening(day, [42], "key", tool.Sec(AGENT, interval=0))
    assert [s["symbol"] for s in signals] == ["ABCD"] and seen[0]["why"] == "signal"
    assert done == [42]
    assert abs(signals[0]["reaction"] + 0.21) < 1e-9 and signals[0]["entry"] == 15.6
    assert tool.next_open("ABCD", day, "key") == 15.0
    assert (
        tool.last_evening(datetime(2026, 11, 18, 9, 40, tzinfo=UTC).astimezone(ahp.NEW_YORK)) == day
    )


def test_an_evening_recorded_before_the_filer_counts_is_read_again():
    state = {"strategy": "after_hours_short", "evenings": ["2026-11-17"], "signals": [], "seen": []}
    assert ahp.needs_reading(state, date(2026, 11, 17))
    ahp.record(state, date(2026, 11, 17), [], [], filers=12, read=[1, 2], complete=False)
    assert ahp.needs_reading(state, date(2026, 11, 17))
    assert ahp.read_so_far(state, date(2026, 11, 17)) == [1, 2]
    assert "2026-11-17 read in part so far" in ahp.report(state)
    ahp.record(state, date(2026, 11, 17), [], [], filers=12, read=[3])
    assert not ahp.needs_reading(state, date(2026, 11, 17)) and state["partial"] == {}


def test_the_index_is_asked_for_as_the_sec_asks_and_unzipped(monkeypatch):
    tool = load_tool()
    asked = []

    def urlopen(request, timeout):
        asked.append(request)
        return Answer(gzip.compress(INDEX.encode()), "gzip")

    monkeypatch.setattr(tool.urllib.request, "urlopen", urlopen)
    assert tool.index_ciks(date(2026, 11, 17), AGENT) == [2222, 4444]
    request = asked[0]
    assert request.full_url == (
        "https://www.sec.gov/Archives/edgar/daily-index/2026/QTR4/form.20261117.idx"
    )
    assert request.get_header("User-agent") == AGENT
    assert request.get_header("Accept-encoding") == "gzip, deflate"
    assert request.get_header("Host") == "www.sec.gov"


def test_answers_are_unzipped_whatever_the_encoding():
    tool = load_tool()
    squeeze = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    raw = squeeze.compress(b"8-K") + squeeze.flush()
    assert tool.decoded(b"8-K", None) == "8-K"
    assert tool.decoded(gzip.compress(b"8-K"), "gzip") == "8-K"
    assert tool.decoded(zlib.compress(b"8-K"), "deflate") == "8-K"
    assert tool.decoded(raw, "deflate") == "8-K"


def test_a_refusal_carries_the_secs_reason(monkeypatch):
    tool = load_tool()
    page = b"<html><head><title>SEC.gov | Request Rate Threshold Exceeded</title></head></html>"

    def refuse(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, io.BytesIO(page))

    monkeypatch.setattr(tool.urllib.request, "urlopen", refuse)
    with pytest.raises(tool.Refused, match="HTTP 403 from www.sec.gov: SEC.gov . Request Rate"):
        tool.index_ciks(date(2026, 11, 17), AGENT)


def test_a_refusal_of_the_first_request_stops_the_run(monkeypatch):
    tool = load_tool()
    sec = tool.Sec(AGENT, interval=0)

    def refuse():
        raise tool.Refused("HTTP 403 from www.sec.gov")

    with pytest.raises(SystemExit, match="first request") as stop:
        sec.ask(refuse, refuse)
    assert "SEC_USER_AGENT" in str(stop.value) and AGENT in str(stop.value)


def test_a_pause_after_answers_is_waited_out_once(monkeypatch):
    tool = load_tool()
    slept = []
    monkeypatch.setattr(tool.time, "sleep", slept.append)
    sec = tool.Sec(AGENT, interval=0, pause=660)
    answers = iter(["first", tool.Refused("HTTP 403 from data.sec.gov"), "second"])

    def fetch():
        answer = next(answers)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def refuse():
        raise tool.Refused("HTTP 403 from data.sec.gov")

    assert sec.ask(fetch, refuse) == "first" and sec.ask(fetch, refuse) == "second"
    assert slept == [660] and sec.answers == 2
    with pytest.raises(SystemExit, match="again after a pause"):
        sec.ask(refuse, refuse)
    assert slept == [660, 660]


def test_a_refused_file_is_missing_when_the_sec_answers_a_page_that_always_exists(monkeypatch):
    tool = load_tool()
    asked = []

    def urlopen(request, timeout):
        asked.append(request.full_url)
        if request.full_url.endswith("form.20261111.idx"):
            raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, io.BytesIO())
        if request.full_url.endswith("/daily-index/"):
            return Answer(b"<html><title>Directory Listing</title></html>")
        return Answer(INDEX.encode())

    monkeypatch.setattr(tool.urllib.request, "urlopen", urlopen)
    sec = tool.Sec(AGENT, interval=0)
    assert tool.filers(date(2026, 11, 11), date(2026, 11, 19), sec) == ([], "closed")
    assert asked[0].endswith("form.20261111.idx") and asked[1].endswith("/daily-index/")
    assert sec.answers == 2 and not sec.paused

    def get_json(url, host, headers):
        if "CIK0000000042" in url:
            raise tool.tool.FetchError("HTTP 403 from data.sec.gov", 403)
        return {"tickers": ["AAPL"]}

    monkeypatch.setattr(tool.tool, "get_json", get_json)
    assert sec.submissions(42)["tickers"] == []


def test_requests_to_the_sec_are_spaced(monkeypatch):
    tool = load_tool()
    slept = []
    monkeypatch.setattr(tool.time, "sleep", slept.append)
    sec = tool.Sec(AGENT, interval=0.25)
    sec.ask(lambda: 1, lambda: None)
    sec.ask(lambda: 2, lambda: None)
    assert len(slept) == 1 and 0.2 < slept[0] <= 0.25


def test_each_company_is_read_once_a_run_and_kept_small(monkeypatch):
    tool = load_tool()
    asked = []
    full = {
        "tickers": ["ABCD"],
        "name": "ABCD INC",
        "filings": {
            "recent": {
                "form": ["10-Q", "8-K", "4"],
                "items": ["", "2.02,9.01", ""],
                "acceptanceDateTime": [
                    "2026-11-17T20:00:00.000Z",
                    "2026-11-17T21:05:00.000Z",
                    "2026-11-17T22:00:00.000Z",
                ],
                "accessionNumber": ["a", "b", "c"],
                "primaryDocument": ["x", "y", "z"],
            }
        },
    }

    def get_json(url, host, headers):
        asked.append(url)
        return full

    monkeypatch.setattr(tool.tool, "get_json", get_json)
    sec = tool.Sec(AGENT, interval=0)
    kept = sec.submissions(42)
    assert sec.submissions(42) is kept and len(asked) == 1
    assert kept["filings"]["recent"]["form"] == ["8-K"] and "name" not in kept
    assert ahp.results_filings(kept, date(2026, 11, 17)) == ahp.results_filings(
        full, date(2026, 11, 17)
    )


def test_a_missing_index_is_none_and_a_page_without_filings_is_an_error(monkeypatch):
    tool = load_tool()
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    answers = iter(
        [
            urllib.error.HTTPError("u", 404, "Not Found", {}, None),
            urllib.error.HTTPError("u", 503, "Unavailable", {}, None),
            Answer(b"<html>Request Rate Threshold Exceeded</html>"),
        ]
    )

    def urlopen(request, timeout):
        answer = next(answers)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(tool.urllib.request, "urlopen", urlopen)
    assert tool.index_ciks(date(2026, 11, 11), AGENT) is None
    with pytest.raises(tool.tool.FetchError, match="lists no filings"):
        tool.index_ciks(date(2026, 11, 17), AGENT)


def test_an_evening_reads_its_own_index_and_the_next_one_out(monkeypatch):
    tool = load_tool()
    out = {date(2026, 11, 10): [1, 2], date(2026, 11, 12): [2, 3], date(2026, 11, 17): [5]}
    monkeypatch.setattr(tool, "index_ciks", lambda d, agent: out.get(d))
    sec = tool.Sec(AGENT, interval=0)
    assert tool.filers(date(2026, 11, 10), date(2026, 11, 19), sec) == ([1, 2, 3], "complete")
    assert tool.filers(date(2026, 11, 11), date(2026, 11, 19), sec) == ([], "closed")
    assert tool.filers(date(2026, 11, 17), date(2026, 11, 18), sec) == ([5], "partial")
    assert tool.filers(date(2026, 11, 18), date(2026, 11, 18), sec) is None


@pytest.mark.parametrize(
    "agent", ["", "Kun Kim your@email", "kun@example.com", "Your Name your@email"]
)
def test_the_sec_agent_must_name_a_person_and_a_real_email(monkeypatch, agent):
    tool = load_tool()
    monkeypatch.setenv("SEC_USER_AGENT", agent)
    with pytest.raises(SystemExit, match="real email"):
        tool.sec_agent()
    monkeypatch.setenv("SEC_USER_AGENT", f" {AGENT} ")
    assert tool.sec_agent() == AGENT


def test_a_filer_that_could_not_be_read_is_read_on_the_next_run(monkeypatch):
    tool = load_tool()
    day, today = date(2026, 11, 17), date(2026, 11, 19)
    monkeypatch.setattr(tool, "filers", lambda d, t, agent: ([1, 2, 3], "complete"))
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    failing, asked = {2}, []

    def get_json(url, host, headers):
        cik = int(url.split("CIK")[1].split(".")[0])
        asked.append(cik)
        if cik in failing:
            raise tool.tool.FetchError("HTTP 500 from data.sec.gov", 500)
        return {}

    monkeypatch.setattr(tool.tool, "get_json", get_json)
    state = ahp.new_state()
    tool.read_evening(state, day, today, "key", tool.Sec(AGENT, interval=0), fresh=False)
    assert ahp.needs_reading(state, day) and state["partial"] == {"2026-11-17": [1, 3]}
    failing.clear()
    asked.clear()
    tool.read_evening(state, day, today, "key", tool.Sec(AGENT, interval=0), fresh=False)
    assert asked == [2] and not ahp.needs_reading(state, day)
    assert state["filers"] == {"2026-11-17": 3}
    asked.clear()
    tool.read_evening(state, day, today, "key", tool.Sec(AGENT, interval=0), fresh=True)
    assert asked == [1, 2, 3]


def test_a_refused_filer_stops_the_run(monkeypatch):
    tool = load_tool()
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)

    def get_json(url, host, headers):
        raise tool.tool.FetchError("HTTP 403 from data.sec.gov", 403)

    monkeypatch.setattr(tool.tool, "get_json", get_json)
    with pytest.raises(SystemExit, match="first request .HTTP 403 from data.sec.gov"):
        tool.evening(date(2026, 11, 17), [9], "key", tool.Sec(AGENT, interval=0))


def test_an_evening_without_an_index_is_not_recorded_and_a_closed_day_is(monkeypatch):
    tool = load_tool()
    state = ahp.new_state()
    monkeypatch.setattr(tool, "filers", lambda d, t, agent: None)
    sec = tool.Sec(AGENT, interval=0)
    tool.read_evening(state, date(2026, 11, 18), date(2026, 11, 18), "key", sec, fresh=False)
    assert state["evenings"] == [] and ahp.needs_reading(state, date(2026, 11, 18))
    monkeypatch.setattr(tool, "filers", lambda d, t, agent: ([], "closed"))
    tool.read_evening(state, date(2026, 11, 11), date(2026, 11, 19), "key", sec, fresh=False)
    assert state["evenings"] == ["2026-11-11"] and not ahp.needs_reading(state, date(2026, 11, 11))


def test_massive_failures_leave_the_filer_to_be_read_again(monkeypatch):
    tool = load_tool()
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    subs = {
        "tickers": ["ABCD"],
        "filings": {
            "recent": {
                "form": ["8-K"],
                "items": ["2.02"],
                "acceptanceDateTime": ["2026-11-17T21:05:00.000Z"],
                "accessionNumber": ["acc"],
            }
        },
    }
    monkeypatch.setattr(tool.tool, "get_json", lambda url, host, headers: subs)

    def massive(route, key, **query):
        raise tool.tool.FetchError("HTTP 502 from api.massive.com", 502)

    monkeypatch.setattr(tool.tool, "massive", massive)
    assert tool.evening(date(2026, 11, 17), [42], "key", tool.Sec(AGENT, interval=0)) == (
        [],
        [],
        [],
    )
