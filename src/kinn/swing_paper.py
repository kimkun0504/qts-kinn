"""Paper trading for the earnings drift: each evening, from that day's bars and filings, find
the signals, fill yesterday's at today's open, close what has been held long enough at today's
close, and keep a ledger. No order is sent anywhere.

Nothing here touches the network or the research data. The owner's tool
(``tools/owner/paper_earnings_drift.py``) fetches a window of daily bars adjusted to today,
company details and 8-K filings, and hands them to these functions. The rule is the one in
:mod:`kinn.swing_run`; a test holds the two to the same signals.

Every signal is followed whether or not a book has room for it, so the ledger shows what the
skipped ones did. Several books (say 10 positions and 20) can be kept side by side. A book
with ``skip_fallen_cash_rich: true`` takes only the signals that pass the quality test of
:func:`kinn.swing_run.keeps` (up over the year, or net debt); the facts for it come from
:func:`year_return` and :func:`net_cash` and are recorded with each signal.
"""

from __future__ import annotations

import json
import os
import statistics
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from kinn.costs.model import CostModel
from kinn.swing_run import MAX_GAP_DAYS, YEAR_SESSIONS, Rule, allowance, keeps

COMMON_STOCK = ("CS", "ADRC")  # the vendor's types for common stock and common-stock ADRs
EARNINGS_ITEM = "2.02"  # 8-K item: results of operations and financial condition
ADV_SESSIONS, MIN_ADV_SESSIONS, MISSED_LIMIT = 20, 10, 5
BENCHMARK = "IWM"  # the small-stock index fund each trade is set beside (and, hedged, against)


@dataclass(frozen=True)
class Bar:
    """One stock's session, with prices adjusted to the evening the window was fetched."""

    open: float
    low: float
    close: float
    dollar_volume: float


Window = dict[date, dict[str, Bar]]


def bars_of(results: list[dict]) -> dict[str, Bar]:
    """The vendor's grouped daily bars for one session, as {symbol: Bar}."""
    out = {}
    for r in results or []:
        try:
            o, low, c, v = float(r["o"]), float(r["l"]), float(r["c"]), float(r["v"])
        except (KeyError, TypeError, ValueError):
            continue
        if o > 0 and low > 0 and c > 0:
            out[r["T"]] = Bar(o, low, c, float(r.get("vw") or c) * v)
    return out


def earnings_days(submissions: dict) -> list[tuple[date, str]]:
    """(filing date, accession number) of each 8-K with the earnings item, from the SEC's
    submissions file for one company."""
    recent = (submissions.get("filings") or {}).get("recent") or {}
    rows = zip(recent.get("form", []), recent.get("filingDate", []), recent.get("items", []),
               recent.get("accessionNumber", []), strict=False)  # fmt: skip
    return [
        (date.fromisoformat(filed), accession)
        for form, filed, items, accession in rows
        if form == "8-K" and EARNINGS_ITEM in (items or "").split(",")
    ]


def _own(window: Window, symbol: str, before: date) -> list[tuple[date, Bar]]:
    return [
        (d, bars[symbol]) for d, bars in sorted(window.items()) if d < before and symbol in bars
    ]


def prescreen(window: Window, day: date, rule: Rule) -> list[dict]:
    """Stocks whose price and volume meet the rule at ``day``'s close. Size, type and the
    earnings filing are checked afterwards (:func:`confirm`), for these few only."""
    found = []
    for symbol, bar in window[day].items():
        if bar.close < rule.min_close:
            continue
        own = _own(window, symbol, day)
        if len(own) < MIN_ADV_SESSIONS + 1 or (day - own[-1][0]).days > MAX_GAP_DAYS:
            continue
        jump = bar.close / own[-2][1].close - 1
        if jump < rule.jump:
            continue
        adv = statistics.median(b.dollar_volume for _, b in own[-ADV_SESSIONS:])
        adv_prev = statistics.median(b.dollar_volume for _, b in own[-ADV_SESSIONS - 1 : -1])
        if adv < rule.min_adv or adv <= 0:
            continue
        volume = max(bar.dollar_volume / adv,
                     own[-1][1].dollar_volume / adv_prev if adv_prev > 0 else 0.0)  # fmt: skip
        if volume >= rule.volume:
            found.append({"symbol": symbol, "day": day, "prev_day": own[-1][0], "jump": jump,
                          "volume": volume, "adv": adv, "close": bar.close})  # fmt: skip
    return sorted(found, key=lambda c: c["symbol"])


def confirm(
    candidate: dict, *, kind: str | None, market_cap: float | None,
    filings: list[tuple[date, str]], rule: Rule,
) -> tuple[dict | None, str]:  # fmt: skip
    """The candidate as a signal, or None and the reason it is not one."""
    if kind not in COMMON_STOCK:
        return None, f"not common stock ({kind})"
    if market_cap is None:
        return None, "no market value from the vendor"
    if not rule.cap_min <= market_cap < rule.cap_max:
        return None, f"market value ${market_cap / 1e6:,.0f}M is outside the band"
    recent = [f for f in filings if candidate["prev_day"] <= f[0] < candidate["day"]]
    if not recent:
        return None, "no earnings 8-K since the previous session"
    return {
        **candidate,
        "market_cap": market_cap,
        "filed": recent[-1][0],
        "filing": recent[-1][1],
    }, ""


def year_return(closes: list[float]) -> float | None:
    """The return over the 250 sessions to the last close in ``closes`` (the stock's own
    sessions, oldest first, adjusted for splits), or None with less history than that."""
    if len(closes) <= YEAR_SESSIONS or closes[-1 - YEAR_SESSIONS] <= 0:
        return None
    return closes[-1] / closes[-1 - YEAR_SESSIONS] - 1


# XBRL tags (us-gaap) for the balance sheet. Sharadar's fields, which the research used, are
# cash and equivalents (investments not counted) and total debt including lease liabilities;
# these tags approximate them. Each tuple is alternatives that must not be added together.
CASH_TAGS = ("CashAndCashEquivalentsAtCarryingValue",
             "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents", "Cash")  # fmt: skip
REPORT_FORMS = ("10-Q", "10-K", "10-Q/A", "10-K/A", "10-KT", "10-QT")


def _instants(facts: dict, tag: str, before: date) -> dict[str, float]:
    """{balance date: value} for one tag, from quarterly and annual reports filed before
    ``before``; where a date was reported more than once, the latest filing wins."""
    units = ((facts.get("facts") or {}).get("us-gaap") or {}).get(tag, {}).get("units") or {}
    found: dict[str, tuple[str, float]] = {}
    for row in units.get("USD", []):
        filed, end = row.get("filed"), row.get("end")
        if (not filed or not end or "start" in row or row.get("form") not in REPORT_FORMS
                or date.fromisoformat(filed) >= before or row.get("val") is None):  # fmt: skip
            continue
        if end not in found or filed > found[end][0]:
            found[end] = (filed, float(row["val"]))
    return {end: value for end, (_, value) in found.items()}


def net_cash(facts: dict, before: date) -> dict | None:
    """Cash less debt at the latest balance sheet filed before ``before``, from the SEC's
    company-facts file. Returns the figures used ({period, cash, debt, leases, net_cash}), or
    None when there is no cash figure (no XBRL filing, or a filer that does not report in
    US GAAP)."""
    cash_by_tag = [(tag, _instants(facts, tag, before)) for tag in CASH_TAGS]
    periods = [max(values) for _, values in cash_by_tag if values]
    if not periods:
        return None
    period = max(periods)
    cash = next(values[period] for _, values in cash_by_tag if period in values)

    def v(tag: str) -> float:
        return _instants(facts, tag, before).get(period, 0.0)

    def either(total: str, *parts: str) -> float:
        return v(total) or sum(v(part) for part in parts)

    # Borrowings: companies tag them in several overlapping ways, so take the largest of the
    # ways of adding them up, never the sum of all.
    current = max(v("DebtCurrent"), v("LongTermDebtCurrent") + v("ShortTermBorrowings"))
    by_kind = (
        either("ConvertibleNotesPayable", "ConvertibleNotesPayableCurrent",
               "ConvertibleLongTermNotesPayable")
        + either("LineOfCredit", "LinesOfCreditCurrent", "LongTermLineOfCredit")
        + either("NotesPayable", "NotesPayableCurrent", "LongTermNotesPayable")
        + either("LoansPayable", "LoansPayableCurrent", "LongTermLoansPayable")
        + v("SeniorNotes") + v("SecuredDebt")
    )  # fmt: skip
    with_leases = max(
        v("DebtAndCapitalLeaseObligations"),
        v("LongTermDebtAndCapitalLeaseObligations")
        + max(v("LongTermDebtAndCapitalLeaseObligationsCurrent"), v("DebtCurrent")),
    )
    without = max(
        v("DebtLongtermAndShorttermCombinedAmount"),
        v("LongTermDebt") + v("ShortTermBorrowings"),
        v("LongTermDebtNoncurrent") + current,
        by_kind,
    )
    finance = either("FinanceLeaseLiability", "FinanceLeaseLiabilityCurrent",
                     "FinanceLeaseLiabilityNoncurrent")  # fmt: skip
    operating = either("OperatingLeaseLiability", "OperatingLeaseLiabilityCurrent",
                       "OperatingLeaseLiabilityNoncurrent")  # fmt: skip
    debt = max(with_leases, without + finance)
    return {"period": period, "cash": cash, "debt": debt, "leases": operating,
            "net_cash": cash - debt - operating}  # fmt: skip


def quality(year: float | None, balance: dict | None) -> dict:
    """The quality test's facts for one signal, in the form the ledger keeps."""
    cash = balance["net_cash"] if balance else None
    return {"year_return": year, "net_cash": cash, "balance": balance, "kept": keeps(year, cash)}


def new_state() -> dict:
    return {"schema": "paper-1", "last_session": None, "tracks": []}


def ema(closes: list[float], sessions: int) -> float:
    """The exponential average of ``closes`` (oldest first) with the usual 2 / (n + 1) weight,
    started at the first close."""
    alpha, average = 2 / (sessions + 1), closes[0]
    for close in closes[1:]:
        average = alpha * close + (1 - alpha) * average
    return average


def _live(t: dict) -> bool:
    """A track still followed: waiting, held under the plain exit, or held by a book with
    its own exit."""
    return t["status"] in ("pending", "open") or any(p.get("open") for p in t["books"].values())


def _held(t: dict, name: str) -> bool:
    """Whether book ``name`` holds this track's stock now."""
    position = t["books"].get(name)
    if position is None:
        return False
    return position["open"] if "open" in position else t["status"] == "open"


def _settle(position: dict, growth: float, forced: bool, a: float, costs: CostModel) -> None:
    """Close one book's position at ``growth`` times its entry: fees and the allowance."""
    n, exit_value = position["notional"], position["notional"] * growth
    fees = sum(sum(costs.order_fees(side=side, value=value, marketable=0, passive=0,
                                    auction=position["shares"]))
               for side, value in (("buy", n), ("sell", exit_value)))  # fmt: skip
    slip = a * n + (costs.forced_exit_bps / 1e4 if forced else a) * exit_value
    position.update(net=exit_value - n - fees - slip, net_2x=exit_value - n - fees - 2 * slip)


def step(
    state: dict, window: Window, day: date, signals: list[dict], *, hold: int,
    books: dict[str, dict], costs: CostModel, allowance_bps: list[list[float]],
) -> list[str]:  # fmt: skip
    """Advance the ledger by one session: enter yesterday's signals at the open, exit at the
    close what has been held ``hold`` sessions, then add today's signals. Returns what happened.

    A book with ``exit: {average: 20, max_sessions: 30}`` leaves by its own rule instead: once
    a close is under the stock's 20-day exponential average it sells at the next open, and at
    the close of the 30th session at the latest (the exit study's variant)."""
    if state["last_session"] and date.fromisoformat(state["last_session"]) >= day:
        raise ValueError(f"{day} is not after the last session done, {state['last_session']}")
    said = []
    bars = window[day]
    live = [t for t in state["tracks"] if _live(t)]
    for t in live:
        t["sessions"] += 1
    waiting = sorted((t for t in live if t["status"] == "pending"),
                     key=lambda t: (-t["volume"], t["symbol"]))  # fmt: skip
    for t in waiting:
        bar = bars.get(t["symbol"])
        if bar is None:
            t.update(status="cancelled", reason="did not trade on the entry day")
            said.append(f"{t['symbol']}: no entry, it did not trade")
            continue
        t.update(status="open", entry_day=day.isoformat(), entry_open=bar.open, missed=0, books={})
        for name, book in books.items():
            held = sum(1 for o in state["tracks"] if _held(o, name))
            size = book["account"] / book["slots"]
            shares = int(size // bar.open)
            if book.get("skip_fallen_cash_rich") and not t.get("kept"):
                continue  # fails the quality test, or its facts were never recorded
            if held < book["slots"] and shares > 0:
                t["books"][name] = {"shares": shares, "notional": shares * bar.open}
                if book.get("exit"):
                    t["books"][name].update(open=True, exit=dict(book["exit"]), missed=0)
        where = ", ".join(t["books"]) or "no book had room"
        said.append(f"{t['symbol']}: bought at the open, {bar.open:.2f} ({where})")
    for t in live:  # positions of books with their own exit
        entry_day = date.fromisoformat(t["entry_day"]) if t.get("entry_day") else None
        for name, position in t["books"].items():
            if not position.get("open") or entry_day == day:
                continue
            bar, forced, at_open = bars.get(t["symbol"]), False, False
            if bar is None:
                position["missed"] = position.get("missed", 0) + 1
                last = _own(window, t["symbol"], day)
                if position["missed"] <= MISSED_LIMIT or not last:
                    continue
                price, forced, why = last[-1][1].close, True, "stopped trading"
            elif position.get("leave"):
                price, at_open, why = bar.open, True, "under its average"
            elif t["sessions"] >= position["exit"]["max_sessions"]:
                price, why = bar.close, "time"
            else:
                closes = [b.close for _, b in _own(window, t["symbol"], day)] + [bar.close]
                if bar.close < ema(closes, position["exit"]["average"]):
                    position["leave"] = True
                continue
            entry = window.get(entry_day, {}).get(t["symbol"])
            growth = price / (entry.open if entry else t["entry_open"])
            _settle(position, growth, forced, allowance(allowance_bps, t["adv"]), costs)
            position.update(open=False, exit_day=day.isoformat(), gross_return=growth - 1,
                            reason=why)  # fmt: skip
            said.append(f"{t['symbol']}: {name} sold at the {'open' if at_open else 'close'} "
                        f"({why}), {100 * (growth - 1):+.1f}% before costs")  # fmt: skip
    for t in [t for t in live if t["status"] == "open" and t["sessions"] >= hold]:
        bar, forced = bars.get(t["symbol"]), False
        if bar is None:
            t["missed"] += 1
            if t["missed"] <= MISSED_LIMIT:
                continue
            last = _own(window, t["symbol"], day)
            if not last:
                continue
            bar, forced = last[-1][1], True
        entry_day = date.fromisoformat(t["entry_day"])
        entry = window.get(entry_day, {}).get(t["symbol"])
        growth = bar.close / (entry.open if entry else t["entry_open"])
        a = allowance(allowance_bps, t["adv"])
        for result in t["books"].values():
            if "exit" not in result:  # books with their own exit are settled above
                _settle(result, growth, forced, a, costs)
        t.update(status="closed", exit_day=day.isoformat(), gross_return=growth - 1,
                 benchmark_return=_benchmark(window, entry_day, day),
                 reason="stopped trading" if forced else "time")  # fmt: skip
        said.append(f"{t['symbol']}: sold at the close, {100 * (growth - 1):+.1f}% before costs")
    for s in sorted(signals, key=lambda s: (-s["volume"], s["symbol"])):
        state["tracks"].append({
            "symbol": s["symbol"], "signal_day": day.isoformat(), "status": "pending",
            "sessions": 0, "jump": s["jump"], "volume": s["volume"], "adv": s["adv"],
            "market_cap": s["market_cap"], "signal_close": s["close"],
            "filed": s["filed"].isoformat(), "filing": s["filing"], "books": {},
            **{k: s[k] for k in ("year_return", "net_cash", "balance", "kept") if k in s},
        })  # fmt: skip
        said.append(
            f"{s['symbol']}: signal, up {100 * s['jump']:.0f}% in two days on "
            f"{s['volume']:.1f}x volume; buy at the next open{quality_note(s)}"
        )
    state["last_session"] = day.isoformat()
    return said


def quality_note(t: dict) -> str:
    """What the quality test made of a signal, in words (empty if it was never applied)."""
    if "kept" not in t:
        return ""
    year, cash = t.get("year_return"), t.get("net_cash")
    over = "no year of history" if year is None else f"{100 * year:+.0f}% over the year"
    owes = ("balance sheet not found" if cash is None
            else f"net {'debt' if cash < 0 else 'cash'} ${abs(cash) / 1e6:,.0f}M")  # fmt: skip
    verdict = "passes the quality test" if t["kept"] else "fails the quality test"
    return f" ({verdict}: {over}, {owes})"


def _benchmark(window: Window, entry_day: date, day: date) -> float | None:
    """The index fund's return from the open of ``entry_day`` to the close of ``day``."""
    first, last = window.get(entry_day, {}).get(BENCHMARK), window.get(day, {}).get(BENCHMARK)
    return last.close / first.open - 1 if first and last else None


def report(state: dict, window: Window, *, hold: int, books: dict[str, dict]) -> str:
    """The ledger as a page: tomorrow's orders, what is held, and the results so far."""
    day = state["last_session"]
    bars = window.get(date.fromisoformat(day), {}) if day else {}
    tracks = state["tracks"]
    lines = [f"# Earnings drift, paper ledger to the close of {day}", "",
             "No order is sent anywhere. Prices are the official open and close.", ""]  # fmt: skip
    pending = [t for t in tracks if t["status"] == "pending"]
    lines += ["## Buy at the next open (an on-open order)", ""]
    if not pending:
        lines.append("Nothing.")
    for t in pending:
        sizes = ", ".join(f"{name}: about {int(b['account'] / b['slots'] // t['signal_close'])} "
                          f"shares" for name, b in books.items())  # fmt: skip
        lines.append(
            f"- **{t['symbol']}** closed {t['signal_close']:.2f}, up {100 * t['jump']:.0f}% in "
            f"two days on {t['volume']:.1f}x volume; ${t['market_cap'] / 1e6:,.0f}M; earnings "
            f"8-K filed {t['filed']} ({t['filing']}). {sizes}, if the book has room."
            + (f" It{quality_note(t).replace(' (', ' ', 1).rstrip(')')}." if "kept" in t else "")
        )
    leaving = [(t, [n for n, p in t["books"].items() if p.get("open") and p.get("leave")])
               for t in tracks]  # fmt: skip
    leaving = [(t, names) for t, names in leaving if names]
    if leaving:
        lines += ["", "## Sell at the next open (closed under its 20-day average)", ""]
        lines += [f"- **{t['symbol']}**, bought {t['entry_day']}: {', '.join(names)}"
                  for t, names in leaving]  # fmt: skip
    due = []
    for t in tracks:
        names = [n for n, p in t["books"].items()
                 if (t["status"] == "open" and "exit" not in p and t["sessions"] + 1 >= hold)
                 or (p.get("open") and not p.get("leave")
                     and t["sessions"] + 1 >= p["exit"]["max_sessions"])]  # fmt: skip
        if names or (t["status"] == "open" and not t["books"] and t["sessions"] + 1 >= hold):
            due.append(f"- **{t['symbol']}**, bought {t['entry_day']}"
                       + (f": {', '.join(names)}" if names else " (followed only)"))  # fmt: skip
    lines += ["", "## Sell at the next close (an on-close order)", ""]
    lines += due or ["Nothing."]
    today = date.fromisoformat(day) if day else None
    lines += ["", "## Held now", "",
              f"| Stock | Signal | Bought | At | Now | {BENCHMARK} since | Sessions | Books |",
              "|---|---|---|---|---|---|---|---|"]  # fmt: skip
    unrealised = dict.fromkeys(books, 0.0)
    hedged = dict.fromkeys(books, 0.0)
    for t in (t for t in tracks if t["status"] == "open" or any(_held(t, n) for n in t["books"])):
        bar = bars.get(t["symbol"])
        change = bar.close / t["entry_open"] - 1 if bar else None
        fund = _benchmark(window, date.fromisoformat(t["entry_day"]), today)
        holding = [name for name in t["books"] if _held(t, name)]
        for name in holding:
            if name in unrealised:
                result = t["books"][name]
                unrealised[name] += result["notional"] * (change or 0.0)
                hedged[name] += result["notional"] * ((change or 0.0) - (fund or 0.0))
        now = f"{bar.close:.2f} ({100 * change:+.1f}%)" if bar else "n/a"
        since = f"{100 * fund:+.1f}%" if fund is not None else "n/a"
        lines.append(f"| {t['symbol']} | {t['signal_day']} | {t['entry_day']} | "
                     f"{t['entry_open']:.2f} | {now} | {since} | {t['sessions']} of {hold} | "
                     f"{', '.join(holding) or 'none (followed only)'} |")  # fmt: skip
    lines += ["", "Open positions, before costs: " + "; ".join(
        f"{name} ${unrealised[name]:+,.0f} (${hedged[name]:+,.0f} with the same dollars of "
        f"{BENCHMARK} sold short)" for name in books) + "."]  # fmt: skip
    closed = [t for t in tracks if t["status"] == "closed"]
    settled = {name: [p for t in tracks for n, p in t["books"].items() if n == name and "net" in p]
               for name in books}  # fmt: skip
    lines += ["", "## Results so far", ""]
    if closed or any(settled.values()):
        gross = [t["gross_return"] for t in closed]
        if closed:
            lines.append(f"Every signal, whether or not a book took it, sold after {hold} "
                         f"sessions: {len(closed)} finished, mean "
                         f"{100 * statistics.fmean(gross):+.2f}% before costs, "
                         f"{sum(g > 0 for g in gross)} winners.")  # fmt: skip
        ahead = [t["gross_return"] - t["benchmark_return"] for t in closed
                 if t.get("benchmark_return") is not None]  # fmt: skip
        if ahead:
            lines.append(f"Against {BENCHMARK} over the same days ({len(ahead)} trades): "
                         f"{100 * statistics.fmean(ahead):+.2f}% a trade.")  # fmt: skip
        for flag, name in ((True, "passed"), (False, "failed")):
            some = [t["gross_return"] for t in closed if t.get("kept") is flag]
            if some:
                lines.append(f"Signals that {name} the quality test: {len(some)} finished, mean "
                             f"{100 * statistics.fmean(some):+.2f}% before costs.")  # fmt: skip
        lines += ["", "| Book | Trades | A trade | A trade, costs doubled | Total | Doubled |",
                  "|---|---|---|---|---|---|"]  # fmt: skip
        for name in books:
            mine = settled[name]
            if not mine:
                lines.append(f"| {name} | 0 | | | | |")
                continue
            one = statistics.fmean(r["net"] / r["notional"] for r in mine)
            two = statistics.fmean(r["net_2x"] / r["notional"] for r in mine)
            lines.append(f"| {name} | {len(mine)} | {100 * one:+.2f}% | {100 * two:+.2f}% | "
                         f"${sum(r['net'] for r in mine):,.0f} | "
                         f"${sum(r['net_2x'] for r in mine):,.0f} |")  # fmt: skip
    else:
        lines.append("No trade has finished yet.")
    cancelled = [t for t in tracks if t["status"] == "cancelled"]
    if cancelled:
        lines += ["", f"Signals never entered: {', '.join(t['symbol'] for t in cancelled)}."]
    return "\n".join(lines) + "\n"


def snapshot(state: dict, window: Window, *, hold: int, books: dict[str, dict]) -> dict:
    """The ledger as data, for the Workbench: what :func:`report` says, with numbers left as
    numbers. Written beside the state after every session."""
    day = state["last_session"]
    today = date.fromisoformat(day) if day else None
    bars = window.get(today, {}) if today else {}
    tracks = state["tracks"]
    positions = []
    totals = {name: {"open": 0, "unrealised": 0.0, "hedged": 0.0} for name in books}
    for t in tracks:
        holding = [name for name in t["books"] if _held(t, name)]
        if t["status"] != "open" and not holding:
            continue
        bar = bars.get(t["symbol"])
        change = bar.close / t["entry_open"] - 1 if bar else None
        fund = _benchmark(window, date.fromisoformat(t["entry_day"]), today)
        for name in holding:
            if name in totals:
                n = t["books"][name]["notional"]
                totals[name]["open"] += 1
                totals[name]["unrealised"] += n * (change or 0.0)
                totals[name]["hedged"] += n * ((change or 0.0) - (fund or 0.0))
        positions.append({
            "symbol": t["symbol"], "signal_day": t["signal_day"], "entry_day": t["entry_day"],
            "entry_open": t["entry_open"], "last": bar.close if bar else None, "change": change,
            "benchmark": fund, "sessions": t["sessions"], "books": holding,
            "kept": t.get("kept"), "note": quality_note(t).strip(" ()") or None,
        })  # fmt: skip
    out_books = []
    for name, book in books.items():
        done = [p for t in tracks for n, p in t["books"].items() if n == name and "net" in p]
        out_books.append({
            "name": name, "account": book["account"], "slots": book["slots"],
            "quality": bool(book.get("skip_fallen_cash_rich")), "exit": book.get("exit"),
            **totals[name], "trades": len(done),
            "net": sum(p["net"] for p in done), "net_2x": sum(p["net_2x"] for p in done),
            "mean": statistics.fmean(p["net"] / p["notional"] for p in done) if done else None,
        })  # fmt: skip
    closed = [t for t in tracks if t["status"] == "closed"]
    gross = [t["gross_return"] for t in closed]
    ahead = [t["gross_return"] - t["benchmark_return"] for t in closed
             if t.get("benchmark_return") is not None]  # fmt: skip

    def group(flag: bool) -> dict | None:
        some = [t["gross_return"] for t in closed if t.get("kept") is flag]
        return {"finished": len(some), "mean_gross": statistics.fmean(some)} if some else None

    return {
        "schema": "paper-snapshot-1", "last_session": day, "hold": hold, "benchmark": BENCHMARK,
        "buy_next_open": [
            {"symbol": t["symbol"], "signal_close": t["signal_close"], "jump": t["jump"],
             "volume": t["volume"], "market_cap": t["market_cap"], "kept": t.get("kept"),
             "note": quality_note(t).strip(" ()") or None}
            for t in tracks if t["status"] == "pending"
        ],
        "sell_next_open": [
            {"symbol": t["symbol"],
             "books": [n for n, p in t["books"].items() if p.get("open") and p.get("leave")]}
            for t in tracks if any(p.get("open") and p.get("leave") for p in t["books"].values())
        ],
        "sell_next_close": [
            {"symbol": t["symbol"], "books": [n for n in t["books"] if "exit" not in t["books"][n]]}
            for t in tracks if t["status"] == "open" and t["sessions"] + 1 >= hold
        ],
        "positions": positions, "books": out_books,
        "followed": {
            "signals": len(tracks), "finished": len(closed),
            "mean_gross": statistics.fmean(gross) if gross else None,
            "winners": sum(g > 0 for g in gross),
            "vs_benchmark": statistics.fmean(ahead) if ahead else None,
            "passed": group(True), "failed": group(False),
        },
    }  # fmt: skip


def paper_dir(runs_dir: Path, name: str) -> Path:
    """Where a strategy's paper ledger lives: beside the run store, outside the repository."""
    return Path(os.environ.get("KINN_PAPER_DIR") or runs_dir.parent / "paper") / name


def load_state(folder: Path) -> dict:
    path = folder / "state.json"
    return json.loads(path.read_text()) if path.exists() else new_state()


def save(folder: Path, state: dict, page: str, data: dict | None = None) -> None:
    """Write the ledger: its state, the page, and (when given) the snapshot the Workbench reads."""
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / "state.json.tmp"
    tmp.write_text(json.dumps(state, indent=1) + "\n")
    os.replace(tmp, folder / "state.json")
    (folder / "report.md").write_text(page)
    if data is not None:
        tmp = folder / "snapshot.json.tmp"
        tmp.write_text(json.dumps(data, indent=1) + "\n")
        os.replace(tmp, folder / "snapshot.json")
