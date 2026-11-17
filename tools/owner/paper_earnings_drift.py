"""OWNER-ONLY: the nightly paper ledger for the earnings drift (strategies/earnings_drift).

Run it yourself on the Mac after the close (the vendor's daily bars are complete by about
16:30 New York time). It sends no order. It fetches the last 45 sessions of daily bars from
Massive, finds the stocks that meet the rule's price and volume tests, looks up each one's
type and market value at Massive and its 8-K filings at the SEC, then updates the ledger.
For each signal it also fetches a year of the stock's daily bars (Massive) and the company's
reported balance sheet (the SEC's company facts), for the quality test that two of the books
apply:

    export SEC_USER_AGENT="Your Name your@email"     # the SEC asks who is calling
    uv run python tools/owner/paper_earnings_drift.py            # the latest finished session
    uv run python tools/owner/paper_earnings_drift.py --backfill 16   # first run only

The Massive key is read from MASSIVE_API_KEY or `.env`, sent only to api.massive.com and never
printed. The SEC gets no key. The ledger (state.json, report.md) is written beside the run
store, in `paper/earnings_drift/`; nothing is written to the raw or processed data. A night
that was missed is caught up on the next run, up to 20 sessions.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from kinn import swing_paper, swing_run
from kinn.core.settings import load_settings
from kinn.costs import model as cost_model

MASSIVE, SEC = "api.massive.com", "data.sec.gov"
REPO = Path(__file__).resolve().parents[2]
STRATEGY, CONFIG = "earnings_drift", "paper"
WINDOW, MAX_CATCH_UP = 45, 20


class FetchError(Exception):
    """A request failed (the message never contains the key or the URL)."""


def api_key() -> str:
    key = os.environ.get("MASSIVE_API_KEY", "")
    env_file = REPO / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "MASSIVE_API_KEY":
                key = value.strip().strip("'\"")
    if not key:
        raise SystemExit("MASSIVE_API_KEY is not set and was not found in .env")
    return key


def get_json(url: str, host: str, headers: dict) -> dict:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname != host or parts.port not in (None, 443):
        raise SystemExit("refusing to call an unexpected host")
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return {}
            if error.code in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(2**attempt)
                continue
            raise FetchError(f"HTTP {error.code} from {host}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 5:
                raise FetchError(f"could not reach {host}") from None
            time.sleep(2**attempt)
    raise FetchError("no response")


def massive(route: str, key: str, **query) -> dict:
    url = f"https://{MASSIVE}{route}?{urllib.parse.urlencode(query)}"
    return get_json(url, MASSIVE, {"Authorization": f"Bearer {key}"})


def fetch_window(last: date, key: str) -> swing_paper.Window:
    """The ``WINDOW`` sessions ending at ``last``, every stock, adjusted to today."""
    window: swing_paper.Window = {}
    day = last
    while len(window) < WINDOW and (last - day).days < 3 * WINDOW:
        if day.weekday() < 5:
            route = f"/v2/aggs/grouped/locale/us/market/stocks/{day.isoformat()}"
            bars = swing_paper.bars_of(
                massive(route, key, adjusted="true", include_otc="false").get("results")
            )
            if len(bars) > 1000:  # a holiday returns nothing
                window[day] = bars
        day -= timedelta(days=1)
    if len(window) < WINDOW:
        raise SystemExit(f"only {len(window)} sessions of bars came back; nothing was changed")
    return window


def latest_finished_session() -> date:
    now = datetime.now(ZoneInfo("America/New_York"))
    day = now.date() if (now.hour, now.minute) >= (16, 30) else now.date() - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def signals_for(window, day: date, rule, key: str, agent: str) -> tuple[list[dict], list[str]]:
    found, notes = [], []
    for c in swing_paper.prescreen(window, day, rule):
        details = massive(f"/v3/reference/tickers/{urllib.parse.quote(c['symbol'])}", key,
                          date=c["prev_day"].isoformat()).get("results") or {}  # fmt: skip
        filings = []
        if details.get("cik") and details.get("type") in swing_paper.COMMON_STOCK:
            url = f"https://{SEC}/submissions/CIK{int(details['cik']):010d}.json"
            filings = swing_paper.earnings_days(get_json(url, SEC, {"User-Agent": agent}))
            time.sleep(0.15)  # the SEC allows ten requests a second
        signal, why = swing_paper.confirm(
            c, kind=details.get("type"), market_cap=details.get("market_cap"),
            filings=filings, rule=rule,
        )  # fmt: skip
        if signal:
            signal.update(quality_facts(c["symbol"], day, details.get("cik"), key, agent))
            found.append(signal)
        else:
            notes.append(f"{c['symbol']} (+{100 * c['jump']:.0f}%, {c['volume']:.1f}x): {why}")
    return found, notes


def quality_facts(symbol: str, day: date, cik, key: str, agent: str) -> dict:
    """The quality test's facts for a signal: the return over the 250 sessions to ``day`` and
    cash less debt at the last report filed before it. If a source cannot be reached the
    signal is recorded without them (the quality books then pass it by) and the next run
    tries again; the ledger of the frozen rule is never held up by this."""
    try:
        return _quality_facts(symbol, day, cik, key, agent)
    except FetchError as error:
        print(f"    {symbol}: the quality facts could not be fetched ({error}); "
              "the next run tries again")  # fmt: skip
        return {}


def _quality_facts(symbol: str, day: date, cik, key: str, agent: str) -> dict:
    since = day - timedelta(days=swing_run.YEAR_DAYS)
    route = (
        f"/v2/aggs/ticker/{urllib.parse.quote(symbol)}/range/1/day/"
        f"{since.isoformat()}/{day.isoformat()}"
    )
    bars = massive(route, key, adjusted="true", sort="asc", limit="5000").get("results") or []
    closes = [float(b["c"]) for b in bars if b.get("c")]
    balance = None
    if cik:
        url = f"https://{SEC}/api/xbrl/companyfacts/CIK{int(cik):010d}.json"
        balance = swing_paper.net_cash(get_json(url, SEC, {"User-Agent": agent}), day)
        time.sleep(0.15)
    return swing_paper.quality(swing_paper.year_return(closes), balance)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--day", help="the session to run to (default: the latest finished one)")
    parser.add_argument("--backfill", type=int, default=0,
                        help="on the first run, start this many sessions back")  # fmt: skip
    args = parser.parse_args()
    agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if "@" not in agent:
        raise SystemExit('set SEC_USER_AGENT="Your Name your@email" (the SEC requires it)')
    settings, key = load_settings(), api_key()
    meta, cfg = swing_run.load_config(STRATEGY, CONFIG)
    rule = swing_run.Rule.from_config(cfg["rule"])
    costs = cost_model.load(meta["cost_calibration"])
    folder = swing_paper.paper_dir(settings.runs_dir, STRATEGY)
    state = swing_paper.load_state(folder)
    for track in state["tracks"]:
        if "kept" not in track:  # recorded before the quality test: add its facts, once
            day = date.fromisoformat(track["signal_day"])
            route = f"/v3/reference/tickers/{urllib.parse.quote(track['symbol'])}"
            try:
                details = massive(route, key, date=day.isoformat()).get("results") or {}
            except FetchError:
                continue  # tried again on the next run
            track.update(quality_facts(track["symbol"], day, details.get("cik"), key, agent))
            if "kept" in track:
                print(f"{track['symbol']} ({track['signal_day']}):"
                      f"{swing_paper.quality_note(track)}")  # fmt: skip
    last = date.fromisoformat(args.day) if args.day else latest_finished_session()
    window = fetch_window(last, key)
    sessions = sorted(window)
    if state["last_session"]:
        todo = [d for d in sessions if d > date.fromisoformat(state["last_session"])]
    else:
        todo = sessions[-1 - min(max(args.backfill, 0), MAX_CATCH_UP) :]
    if not todo:
        print(f"already done to {state['last_session']}; nothing to do")
        if state["last_session"]:  # the facts added above are still worth saving
            page = swing_paper.report(state, window, hold=rule.hold, books=cfg["books"])
            snap = swing_paper.snapshot(state, window, hold=rule.hold, books=cfg["books"])
            swing_paper.save(folder, state, page, snap)
    if len(todo) > MAX_CATCH_UP + 1:
        raise SystemExit(f"{len(todo)} sessions have been missed, more than {MAX_CATCH_UP}; "
                         "the ledger was not changed")  # fmt: skip
    for day in todo:
        signals, notes = signals_for(window, day, rule, key, agent)
        said = swing_paper.step(
            state, window, day, signals, hold=rule.hold, books=cfg["books"], costs=costs,
            allowance_bps=cfg["costs"]["allowance_bps"],
        )  # fmt: skip
        print(f"{day}: " + ("; ".join(said) or "nothing"))
        for note in notes:
            print(f"    not a signal: {note}")
        # Saved after every session, so an interrupted catch-up resumes where it stopped.
        page = swing_paper.report(state, window, hold=rule.hold, books=cfg["books"])
        snap = swing_paper.snapshot(state, window, hold=rule.hold, books=cfg["books"])
        swing_paper.save(folder, state, page, snap)
    print(f"\nledger: {folder / 'report.md'}\n")
    print(swing_paper.report(state, window, hold=rule.hold, books=cfg["books"]))


if __name__ == "__main__":
    main()
