"""OWNER-ONLY: the paper ledger for the after-hours short (strategies/after_hours).

Run it yourself on the Mac, the morning after an evening of results (any time after 09:35
New York time, so the next open exists), or in the evening to see the signals before they
have an outcome. It sends no order. For the evening asked (by default the last session
before today) it:

1. reads the SEC's daily form index for that day and the next one out (filings accepted after
   17:30 are dated the next business day) and keeps every 8-K. The next day's index appears
   late in its evening, so a morning run reads the evening in part and a later run the rest;
2. reads each filer's submissions at the SEC and keeps the results 8-Ks (item 2.02) accepted
   between 16:00 and 18:30 that evening;
3. for each, looks up the stock's type and market value at Massive, its normal dollar volume
   (20 sessions of daily bars), and that evening's minute bars;
4. applies the rule of strategies/after_hours ("short mid down15 open") and records each
   signal; later runs fill in the next open and the result.

It asks the SEC at most four times a second and reads each company once a run. If the SEC
pauses the address anyway (HTTP 403 after it has answered), the run waits eleven minutes and
carries on; a refusal of the first request, or a second one in a row, stops it with the reason.
A filer that could not be read is read again by the next run, and an evening whose SEC index
is not out yet is not recorded.

    export SEC_USER_AGENT="Your Name you@example.com"  # your name and a real email address
    uv run python tools/owner/paper_after_hours.py                     # the last evening
    uv run python tools/owner/paper_after_hours.py --day 2026-11-17    # a given evening
    uv run python tools/owner/paper_after_hours.py --since 2026-11-09  # every evening since
    uv run python tools/owner/paper_after_hours.py --since 2026-11-09 --redo  # read them again
    uv run python tools/owner/paper_after_hours.py --borrow "ABCD=yes, 0.4%"   # what IBKR showed

The Massive key is read from MASSIVE_API_KEY or `.env`, sent only to api.massive.com and never
printed. The SEC gets no key. The ledger (state.json, report.md) is written beside the run
store, in `paper/after_hours/`; nothing is written to the raw or processed data.
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
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
CONTACT = re.compile(r"\S.*\s[^\s@]+@[^\s@]+\.[A-Za-z]{2,}")
FILING_FIELDS = ("form", "items", "acceptanceDateTime", "accessionNumber")


def sec_agent() -> str:
    agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if not CONTACT.fullmatch(agent):
        raise SystemExit(
            "Set SEC_USER_AGENT to your name and a real email address, e.g.\n"
            '  export SEC_USER_AGENT="Your Name you@example.com"\n'
            f"It is now {agent!r}; the SEC refuses requests that do not say who is calling."
        )
    return agent


def sec_headers(agent: str) -> dict:
    return {"User-Agent": agent, "Accept-Encoding": "gzip, deflate", "Host": SEC_WWW}


class Refused(Exception):
    pass


def refused(refusal: Refused, agent: str, answers: int) -> str:
    if not answers:
        return (
            f"The SEC refused the first request ({refusal}).\n"
            f"SEC_USER_AGENT is {agent!r}; it must be your name and a real email address."
        )
    return (
        f"The SEC refused requests from this address again after a pause ({refusal}).\n"
        f"It had answered {answers} requests. Evenings already read are kept; run this again "
        "later."
    )


def reason(error: urllib.error.HTTPError) -> str:
    try:
        page = decoded(error.read(), error.headers.get("Content-Encoding"))
    except Exception:
        return ""
    title = re.search(r"<title>(.*?)</title>", page, re.IGNORECASE | re.DOTALL)
    return " ".join(title.group(1).split())[:120] if title else ""


def decoded(body: bytes, encoding: str | None) -> str:
    if encoding == "gzip":
        body = gzip.decompress(body)
    elif encoding == "deflate":
        try:
            body = zlib.decompress(body)
        except zlib.error:
            body = zlib.decompress(body, -zlib.MAX_WBITS)
    return body.decode("latin-1")


def get_text(url: str, host: str, headers: dict) -> str | None:
    """A text answer from ``host`` only, or None when there is no such page (HTTP 404). A refusal
    (HTTP 403) raises Refused; other failures are retried as the earnings tool's requests are."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname != host or parts.port not in (None, 443):
        raise SystemExit("refusing to call an unexpected host")
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                body, encoding = response.read(), response.headers.get("Content-Encoding")
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if error.code == 403:
                said = reason(error)
                raise Refused(f"HTTP 403 from {host}" + (f": {said}" if said else "")) from None
            if error.code not in (429, 500, 502, 503, 504) or attempt == 5:
                raise tool.FetchError(f"HTTP {error.code} from {host}", error.code) from None
            time.sleep(2**attempt)
            continue
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 5:
                raise tool.FetchError(f"could not reach {host}") from None
            time.sleep(2**attempt)
            continue
        try:
            return decoded(body, encoding)
        except (OSError, EOFError, zlib.error):
            raise tool.FetchError(f"an unreadable answer from {host}") from None
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


def index_ciks(day: date, agent: str) -> list[int] | None:
    """8-K filers in the SEC's daily form index for ``day``; None when the SEC has no index for
    it (it was closed that day, or the index is not published yet)."""
    q = (day.month - 1) // 3 + 1
    url = f"https://{SEC_WWW}/Archives/edgar/daily-index/{day.year}/QTR{q}/form.{day:%Y%m%d}.idx"
    text = get_text(url, SEC_WWW, sec_headers(agent))
    if text is None:
        return None
    if "edgar/data/" not in text:
        raise tool.FetchError(f"the SEC's index for {day} lists no filings")
    return ahp.daily_index_8k(text)


def submissions_of(cik: int, agent: str) -> dict:
    try:
        return tool.get_json(
            f"https://{tool.SEC}/submissions/CIK{cik:010d}.json", tool.SEC, {"User-Agent": agent}
        )
    except tool.FetchError as error:
        if error.status == 403:
            raise Refused(f"HTTP 403 from {tool.SEC}") from None
        raise


def eight_ks(subs: dict) -> dict:
    recent = (subs.get("filings") or {}).get("recent") or {}
    columns = {name: recent.get(name) or [] for name in FILING_FIELDS}
    keep = [i for i, form in enumerate(columns["form"]) if form == "8-K"]
    return {
        "tickers": subs.get("tickers") or [],
        "filings": {
            "recent": {
                name: [values[i] if i < len(values) else None for i in keep]
                for name, values in columns.items()
            }
        },
    }


class Sec:
    def __init__(self, agent: str, interval: float = 0.25, pause: float = 660.0) -> None:
        self.agent = agent
        self.interval = interval
        self.pause = pause
        self.answers = 0
        self.paused = False
        self.last = 0.0
        self.indexes: dict[date, list[int] | None] = {}
        self.filings: dict[int, dict] = {}

    def ask(self, fetch):
        while True:
            wait = self.interval - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.monotonic()
            try:
                answer = fetch()
            except Refused as refusal:
                if not self.answers or self.paused:
                    raise SystemExit(refused(refusal, self.agent, self.answers)) from None
                self.paused = True
                until = datetime.now(ahp.NEW_YORK) + timedelta(seconds=self.pause)
                print(
                    f"  the SEC paused this address ({refusal}); waiting until {until:%H:%M}",
                    flush=True,
                )
                time.sleep(self.pause)
                continue
            self.answers += 1
            self.paused = False
            return answer

    def index(self, day: date) -> list[int] | None:
        if day not in self.indexes:
            self.indexes[day] = self.ask(lambda: index_ciks(day, self.agent))
        return self.indexes[day]

    def submissions(self, cik: int) -> dict:
        if cik not in self.filings:
            self.filings[cik] = eight_ks(self.ask(lambda: submissions_of(cik, self.agent)))
        return self.filings[cik]


def filers(day: date, today: date, sec: Sec) -> tuple[list[int], str] | None:
    own = sec.index(day)
    later, more = next_weekday(day), None
    while more is None and later <= today:
        more = sec.index(later)
        later = next_weekday(later)
    if own is None:
        return None if more is None else ([], "closed")
    if more is None:
        return own, "partial"
    return sorted(set(own) | set(more)), "complete"


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


def common_stock(tickers: list[str], day: date, key: str) -> tuple[str, dict]:
    """The first of a company's tickers that the vendor calls common stock (a company can list
    warrants, units or preferred shares beside it), with its details; else the first ticker."""
    first = None
    for symbol in tickers[:4]:
        try:
            details = tool.massive(f"/v3/reference/tickers/{urllib.parse.quote(symbol)}", key,
                                   date=day.isoformat()).get("results") or {}  # fmt: skip
        except tool.FetchError as error:
            if error.status not in (400, 422):
                raise
            continue
        first = first or (symbol, details)
        if details.get("type") in ("CS", "ADRC"):
            return symbol, details
    return first or (tickers[0], {})


def evening(
    day: date, ciks: list[int], key: str, sec: Sec
) -> tuple[list[dict], list[dict], list[int]]:
    signals, seen, done = [], [], []
    for cik in ciks:
        try:
            subs = sec.submissions(cik)
        except tool.FetchError:
            continue
        filings = ahp.results_filings(subs, day)
        tickers = subs.get("tickers") or []
        if not filings or not tickers:
            done.append(cik)
            continue
        minute = filings[0]["minute"]
        try:
            symbol, details = common_stock(tickers, day, key)
            row = {
                "day": day.isoformat(),
                "cik": cik,
                "symbol": symbol,
                "accepted": f"{minute // 60:02d}:{minute % 60:02d}",
            }
            if details.get("type") not in ("CS", "ADRC"):
                seen.append({**row, "why": f"not common stock ({details.get('type')})"})
                done.append(cik)
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
            print(f"  {tickers[0]}: Massive could not be read ({error})", flush=True)
            continue
        done.append(cik)
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
    return signals, seen, done


def read_evening(state: dict, day: date, today: date, key: str, sec: Sec, fresh: bool) -> None:
    found = filers(day, today, sec)
    if found is None:
        print(f"{day}: the SEC's index for this day is not out yet; run again later", flush=True)
        return
    ciks, status = found
    if status == "closed":
        print(f"{day}: the SEC was closed (no index); nothing to read", flush=True)
        ahp.record(state, day, [], [], filers=0)
        return
    already = set() if fresh else set(ahp.read_so_far(state, day))
    todo = [cik for cik in ciks if cik not in already]
    print(f"{day}: {len(ciks)} 8-K filers in the SEC's index; reading {len(todo)}", flush=True)
    signals, seen, done = evening(day, todo, key, sec)
    missed = len(todo) - len(done)
    complete = status == "complete" and not missed
    ahp.record(state, day, signals, seen, filers=len(ciks), read=done, complete=complete)
    if missed:
        print(f"  {missed} could not be read; the next run reads them again", flush=True)
    elif not complete:
        print("  the next day's SEC index is not out yet; a later run reads filings after 17:30")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--day", help="the evening to read (YYYY-MM-DD); default: the last one")
    parser.add_argument("--since", help="read every weekday evening from this date to the last one")
    parser.add_argument("--redo", action="store_true", help="read again evenings already recorded")
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
        sec = Sec(sec_agent())
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
            if args.redo or ahp.needs_reading(state, day):
                try:
                    read_evening(state, day, now.date(), key, sec, fresh=args.redo)
                except tool.FetchError as error:
                    print(f"{day}: stopped ({error}); the next run reads it again", flush=True)
                ahp.save(folder, state)
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


if __name__ == "__main__":
    main()
