"""OWNER-ONLY: the paper ledger for the after-hours short (strategies/after_hours).

Run it yourself on the Mac, the morning after an evening of results (any time after 09:35
New York time, so the next open exists), or in the evening to see the signals before they
have an outcome. It sends no order. For the evening asked (by default the last session
before today) it:

1. reads the SEC's daily form index for that day and the next (filings accepted after 17:30
   are dated the next day) and keeps every 8-K;
2. reads each filer's submissions at the SEC and keeps the results 8-Ks (item 2.02) accepted
   between 16:00 and 18:30 that evening;
3. for each, looks up the stock's type and market value at Massive, its normal dollar volume
   (20 sessions of daily bars), and that evening's minute bars;
4. applies the rule of strategies/after_hours ("short mid down15 open") and records each
   signal; later runs fill in the next open and the result.

    export SEC_USER_AGENT="Your Name your@email"     # the SEC asks who is calling
    uv run python tools/owner/paper_after_hours.py                     # the last evening
    uv run python tools/owner/paper_after_hours.py --day 2026-11-17    # a given evening
    uv run python tools/owner/paper_after_hours.py --since 2026-11-09  # every evening since
    uv run python tools/owner/paper_after_hours.py --borrow "ABCD=yes, 0.4%"   # what IBKR showed

The Massive key is read from MASSIVE_API_KEY or `.env`, sent only to api.massive.com and never
printed. The SEC gets no key. The ledger (state.json, report.md) is written beside the run
store, in `paper/after_hours/`; nothing is written to the raw or processed data.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from kinn import after_hours_paper as ahp
from kinn.core.settings import load_settings

# The earnings ledger's tool holds the key handling and the guarded requests; used as is.
_spec = importlib.util.spec_from_file_location(
    "paper_earnings_drift", Path(__file__).with_name("paper_earnings_drift.py")
)
tool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tool)

SEC_WWW = "www.sec.gov"


def get_text(url: str, host: str, headers: dict) -> str:
    """A text answer from ``host`` only, retried as the earnings tool's requests are."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname != host or parts.port not in (None, 443):
        raise SystemExit("refusing to call an unexpected host")
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read().decode("latin-1")
        except urllib.error.HTTPError as error:
            if error.code in (403, 404):
                raise tool.FetchError(f"HTTP {error.code} from {host}") from None
            if error.code in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(2**attempt)
                continue
            raise tool.FetchError(f"HTTP {error.code} from {host}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 5:
                raise tool.FetchError(f"could not reach {host}") from None
            time.sleep(2**attempt)
    raise tool.FetchError("no response")


def last_evening(now: datetime) -> date:
    """The last session whose evening is over: the one before today until 20:00, then today's."""
    day = now.date() if now.hour >= 20 else now.date() - timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def next_weekday(day: date) -> date:
    day += timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return day


def index_ciks(day: date, agent: str) -> list[int]:
    """8-K filers in the SEC's daily form index for ``day`` (none if it is not published yet)."""
    q = (day.month - 1) // 3 + 1
    url = f"https://{SEC_WWW}/Archives/edgar/daily-index/{day.year}/QTR{q}/form.{day:%Y%m%d}.idx"
    try:
        text = get_text(url, SEC_WWW, {"User-Agent": agent})
    except tool.FetchError:
        return []
    return ahp.daily_index_8k(text)


def normal_volume(symbol: str, day: date, key: str) -> float | None:
    """Average dollar volume of the 20 sessions before ``day``."""
    route = (
        f"/v2/aggs/ticker/{urllib.parse.quote(symbol)}/range/1/day/"
        f"{(day - timedelta(days=45)).isoformat()}/{(day - timedelta(days=1)).isoformat()}"
    )
    bars = tool.massive(route, key, adjusted="true", sort="asc", limit="100").get("results") or []
    values = [float(b["vw"]) * float(b["v"]) for b in bars[-20:] if b.get("vw") and b.get("v")]
    return sum(values) / len(values) if len(values) >= 10 else None


def next_session(symbol: str, day: date, key: str) -> tuple[date, float] | None:
    """The stock's next session after ``day`` and its open, once the vendor has it."""
    route = (
        f"/v2/aggs/ticker/{urllib.parse.quote(symbol)}/range/1/day/"
        f"{next_weekday(day).isoformat()}/{(day + timedelta(days=8)).isoformat()}"
    )
    bars = tool.massive(route, key, adjusted="false", sort="asc", limit="10").get("results") or []
    if not bars or not bars[0].get("o"):
        return None
    when = (
        datetime.fromtimestamp(int(bars[0]["t"]) / 1000, tz=ahp.NEW_YORK).date()
        if "t" in bars[0]
        else next_weekday(day)
    )
    return when, float(bars[0]["o"])


def next_open(symbol: str, day: date, key: str) -> float | None:
    found = next_session(symbol, day, key)
    return found[1] if found else None


def price_at_1530(symbol: str, day: date, key: str) -> float | None:
    stock, d = urllib.parse.quote(symbol), day.isoformat()
    results = tool.massive(
        f"/v2/aggs/ticker/{stock}/range/1/minute/{d}/{d}",
        key,
        adjusted="false",
        sort="asc",
        limit="50000",
    ).get("results")
    return ahp.price_at(ahp.minute_bars(results, day), 930)


def evening(day: date, key: str, agent: str) -> tuple[list[dict], list[dict]]:
    ciks = sorted(set(index_ciks(day, agent)) | set(index_ciks(next_weekday(day), agent)))
    print(f"{day}: {len(ciks)} 8-K filers in the SEC's index; reading their filings", flush=True)
    signals, seen = [], []
    for cik in ciks:
        try:
            subs = tool.get_json(
                f"https://{tool.SEC}/submissions/CIK{cik:010d}.json",
                tool.SEC,
                {"User-Agent": agent},
            )
        except tool.FetchError:
            continue
        finally:
            time.sleep(0.12)  # the SEC allows ten requests a second
        filings = ahp.results_filings(subs, day)
        tickers = subs.get("tickers") or []
        if not filings or not tickers:
            continue
        symbol, minute = tickers[0], filings[0]["minute"]
        row = {
            "day": day.isoformat(),
            "cik": cik,
            "symbol": symbol,
            "accepted": f"{minute // 60:02d}:{minute % 60:02d}",
        }
        try:
            details = (
                tool.massive(
                    f"/v3/reference/tickers/{urllib.parse.quote(symbol)}", key, date=day.isoformat()
                ).get("results")
                or {}
            )
            if details.get("type") not in ("CS", "ADRC"):
                seen.append({**row, "why": f"not common stock ({details.get('type')})"})
                continue
            stock, d = urllib.parse.quote(symbol), day.isoformat()
            route = f"/v2/aggs/ticker/{stock}/range/1/minute/{d}/{d}"
            bars = ahp.minute_bars(
                tool.massive(route, key, adjusted="false", sort="asc", limit="50000").get(
                    "results"
                ),
                day,
            )
            read = ahp.reading(bars, minute)
            cap = details.get("market_cap")
            adv = (
                normal_volume(symbol, day, key)
                if cap and ahp.CAP_MIN <= cap < ahp.CAP_MAX
                else None
            )
        except tool.FetchError as error:
            seen.append({**row, "why": f"could not fetch ({error})"})
            continue
        ok, why = ahp.is_signal(read, cap, adv)
        seen.append({**row, "why": why, "reaction": None if read is None else read["reaction"]})
        if ok:
            signals.append(
                {
                    **row,
                    "market_cap": float(cap),
                    "adv": adv,
                    **read,
                    "next_open": None,
                    "gross": None,
                    "net": None,
                    "price_1530": None,
                    "net_1530": None,
                    "borrow": None,
                }
            )
            print(
                f"  signal: {symbol} {100 * read['reaction']:+.1f}% after hours, "
                f"sold at ${read['entry']:.2f}",
                flush=True,
            )
    return signals, seen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--day", help="the evening to read (YYYY-MM-DD); default: the last one")
    parser.add_argument("--since", help="read every weekday evening from this date to the last one")
    parser.add_argument("--borrow", action="append", default=[], help='SYMBOL="what IBKR showed"')
    args = parser.parse_args()
    folder = ahp.paper_dir(load_settings().runs_dir)
    state = ahp.load_state(folder)
    for note in args.borrow:
        symbol, _, text = note.partition("=")
        hits = [s for s in state["signals"] if s["symbol"] == symbol.strip().upper()]
        if not hits:
            raise SystemExit(f"no signal for {symbol} in the ledger")
        hits[-1]["borrow"] = text.strip()
    if not args.borrow or args.day:
        agent = os.environ.get("SEC_USER_AGENT") or raise_agent()
        key = tool.api_key()
        now = datetime.now(ZoneInfo("America/New_York"))
        last = date.fromisoformat(args.day) if args.day else last_evening(now)
        days = [last]
        if args.since:
            days, day = [], date.fromisoformat(args.since)
            while day <= last:
                if day.weekday() < 5:
                    days.append(day)
                day += timedelta(days=1)
        for day in days:
            if day.isoformat() not in state["evenings"]:
                signals, seen = evening(day, key, agent)
                ahp.record(state, day, signals, seen)
                ahp.save(folder, state)  # a long catch-up keeps what it has read
        for s in state["signals"]:
            if s.get("net") is not None and s.get("net_1530") is not None:
                continue
            found = next_session(s["symbol"], date.fromisoformat(s["day"]), key)
            if not found:
                continue
            when, opened = found
            if s.get("net") is None:
                s.update(ahp.settle(s["entry"], opened, s["adv"]))
            if s.get("net_1530") is None and (now.date(), now.hour * 60 + now.minute) > (when, 932):
                price = price_at_1530(s["symbol"], when, key)
                if price:
                    s.update(ahp.settle_held(s["entry"], price, s["adv"]))
    ahp.save(folder, state)
    print(ahp.report(state))
    print(f"Ledger: {folder}")


def raise_agent() -> str:
    raise SystemExit('Set SEC_USER_AGENT first, e.g. export SEC_USER_AGENT="Your Name your@email"')


if __name__ == "__main__":
    main()
