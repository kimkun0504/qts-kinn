"""OWNER-ONLY: the paper ledger for big prints (strategies/big_prints).

Run it yourself on the Mac after the close (the vendor's daily bars are complete by about
16:30 New York time). It sends no order. For the session asked (by default the latest
finished one) it:

1. fetches the vendor's grouped daily bars, unadjusted, for that session and the 70 sessions
   before it (kept in the ledger folder, so later evenings fetch one day);
2. reads each stock's footprint (shares per trade against its own previous 60 sessions),
   normal dollar volume, and the day's return and volume; if 5% or more of liquid stocks
   trade in large pieces (an index day) the rule skips the evening, and its signals are
   recorded apart, marked "index day", outside the rule's figures;
3. for each stock that passes, looks up its type and market value at Massive and its 8-Ks at
   the SEC, and records each signal of strategies/big_prints ("small 20 fp>=3");
4. on every run, fills in open signals from the stock's adjusted daily bars: bought at the
   next open, sold at the close 20 sessions after the signal (and, beside it, 40), with IWM
   over the same days.

    export SEC_USER_AGENT="Your Name your@email"     # the SEC asks who is calling
    uv run python tools/owner/paper_big_prints.py                      # the latest session
    uv run python tools/owner/paper_big_prints.py --day 2026-11-17     # a given session
    uv run python tools/owner/paper_big_prints.py --since 2026-10-20   # every session since
    uv run python tools/owner/paper_big_prints.py --since 2026-10-20 --redo   # read them again

The Massive key is read from MASSIVE_API_KEY or `.env`, sent only to api.massive.com and never
printed. The SEC gets no key. The ledger (state.json, report.md, bars/) is written beside the
run store, in `paper/big_prints/`; nothing is written to the raw or processed data.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import time
import urllib.parse
from datetime import date, datetime, timedelta
from pathlib import Path

from kinn import big_prints_paper as bpp
from kinn.core.settings import load_settings

# The earnings ledger's tool holds the key handling and the guarded requests; used as is.
_spec = importlib.util.spec_from_file_location(
    "paper_earnings_drift", Path(__file__).with_name("paper_earnings_drift.py")
)
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

SESSIONS = 71  # the signal session and 70 before it (60 are needed; gaps in a stock's trading)


def grouped(day: date, key: str, folder: Path) -> dict[str, bpp.DayBar] | None:
    """One session's unadjusted bars, from the ledger's folder or the vendor; None on a
    day with no session."""
    path = folder / "bars" / f"{day.isoformat()}.json"
    if path.exists():
        rows = json.loads(path.read_text())
        return {s: bpp.DayBar(*v) for s, v in rows.items()}
    route = f"/v2/aggs/grouped/locale/us/market/stocks/{day.isoformat()}"
    results = tool.massive(route, key, adjusted="false", include_otc="false").get("results")
    bars = bpp.day_bars(results)
    if len(bars) < 1000:  # a holiday, or not finished yet
        if results and len(results) >= 1000:
            raise SystemExit("the vendor's daily bars carry no trade counts; nothing was changed")
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({s: [b.open, b.close, b.volume, b.transactions] for s, b in bars.items()})
    )
    return bars


def window_to(last: date, key: str, folder: Path) -> bpp.Window:
    window: bpp.Window = {}
    day = last
    while len(window) < SESSIONS and (last - day).days < 3 * SESSIONS:
        if day.weekday() < 5:
            bars = grouped(day, key, folder)
            if bars:
                window[day] = bars
        day -= timedelta(days=1)
    if last not in window:
        raise SystemExit(f"no bars for {last} yet; nothing was changed")
    if len(window) < SESSIONS:
        raise SystemExit(f"only {len(window)} sessions of bars came back; nothing was changed")
    return window


def evening(day: date, window: bpp.Window, key: str, agent: str) -> tuple[float, list, list]:
    found = bpp.measures(window, day)
    share = bpp.market_share(found)
    index_day = share >= bpp.SHARE_MAX  # the rule skips the day; its signals are kept apart
    sessions = sorted(window)
    previous = max(d for d in sessions if d < day)
    signals, screened = [], []
    for c in bpp.candidates(found):
        details = tool.massive(f"/v3/reference/tickers/{urllib.parse.quote(c['symbol'])}", key,
                               date=previous.isoformat()).get("results") or {}  # fmt: skip
        times = []
        if details.get("cik") and details.get("type") in bpp.COMMON_STOCK:
            url = f"https://data.sec.gov/submissions/CIK{int(details['cik']):010d}.json"
            times = bpp.eight_k_times(tool.get_json(url, "data.sec.gov", {"User-Agent": agent}))
            time.sleep(0.15)  # the SEC allows ten requests a second
        ok, why = bpp.confirm(c, details.get("type"), details.get("market_cap"),
                              bpp.quiet(times, day, sessions))  # fmt: skip
        row = {**c, "day": day.isoformat(), "market_cap": details.get("market_cap") or 0.0}
        if index_day:
            row["index_day"] = True
        if ok:
            signals.append(row)
        else:
            screened.append({**row, "why": why})
    return share, signals, screened


def daily(symbol: str, start: date, end: date, key: str) -> list[tuple[date, float, float]]:
    route = (f"/v2/aggs/ticker/{urllib.parse.quote(symbol)}/range/1/day/"
             f"{start.isoformat()}/{end.isoformat()}")  # fmt: skip
    out = []
    for r in tool.massive(route, key, adjusted="true", sort="asc", limit=5000).get("results") or []:
        try:
            when = datetime.fromtimestamp(int(r["t"]) / 1000, tz=bpp.NEW_YORK).date()
            out.append((when, float(r["o"]), float(r["c"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--day", help="the session to read (YYYY-MM-DD); default: the latest")
    parser.add_argument("--since", help="read every session from this date to the latest")
    parser.add_argument("--redo", action="store_true", help="read again evenings already recorded")
    args = parser.parse_args()
    agent = os.environ.get("SEC_USER_AGENT") or raise_agent()
    key = tool.api_key()
    folder = bpp.paper_dir(load_settings().runs_dir)
    state = bpp.load_state(folder)
    last = date.fromisoformat(args.day) if args.day else tool.latest_finished_session()
    days = [last]
    if args.since:
        days, day = [], date.fromisoformat(args.since)
        while day <= last:
            if day.weekday() < 5:
                days.append(day)
            day += timedelta(days=1)
    done = set() if args.redo else {e["day"] for e in state["evenings"]}
    for day in days:
        if day.isoformat() in done:
            continue
        try:
            window = window_to(day, key, folder)
        except SystemExit as stop:
            if day == last:
                raise
            print(f"{day}: {stop}")
            continue
        share, signals, screened = evening(day, window, key, agent)
        bpp.record(state, day, share, signals, screened)
        bpp.save(folder, state)  # a long catch-up keeps what it has read
    open_ = bpp.pending(state)
    if open_:
        first = min(date.fromisoformat(s["day"]) for s in open_)
        benchmark = daily("IWM", first, last + timedelta(days=1), key)
        for s in open_:
            bars = daily(s["symbol"], date.fromisoformat(s["day"]), last + timedelta(days=1), key)
            bpp.settle(s, bars, benchmark, last)
    bpp.save(folder, state)
    print(bpp.report(state))
    print(f"Ledger: {folder}")


def raise_agent() -> str:
    raise SystemExit('Set SEC_USER_AGENT first, e.g. export SEC_USER_AGENT="Your Name your@email"')


if __name__ == "__main__":
    main()
