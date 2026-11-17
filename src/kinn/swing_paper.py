"""Paper trading for the earnings drift: each evening, from that day's bars and filings, find
the signals, fill yesterday's at today's open, close what has been held long enough at today's
close, and keep a ledger. No order is sent anywhere.

Nothing here touches the network or the research data. The owner's tool
(``tools/owner/paper_earnings_drift.py``) fetches a window of daily bars adjusted to today,
company details and 8-K filings, and hands them to these functions. The rule is the one in
:mod:`kinn.swing_run`; a test holds the two to the same signals.

Every signal is followed whether or not a book has room for it, so the ledger shows what the
skipped ones did. Several books (say 10 positions and 20) can be kept side by side.
"""

from __future__ import annotations

import json
import os
import statistics
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from kinn.costs.model import CostModel
from kinn.swing_run import MAX_GAP_DAYS, Rule, allowance

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


def new_state() -> dict:
    return {"schema": "paper-1", "last_session": None, "tracks": []}


def step(
    state: dict, window: Window, day: date, signals: list[dict], *, hold: int,
    books: dict[str, dict], costs: CostModel, allowance_bps: list[list[float]],
) -> list[str]:  # fmt: skip
    """Advance the ledger by one session: enter yesterday's signals at the open, exit at the
    close what has been held ``hold`` sessions, then add today's signals. Returns what happened."""
    if state["last_session"] and date.fromisoformat(state["last_session"]) >= day:
        raise ValueError(f"{day} is not after the last session done, {state['last_session']}")
    said = []
    bars = window[day]
    live = [t for t in state["tracks"] if t["status"] in ("pending", "open")]
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
            held = sum(1 for o in state["tracks"] if o["status"] == "open" and name in o["books"])
            size = book["account"] / book["slots"]
            shares = int(size // bar.open)
            if held < book["slots"] and shares > 0:
                t["books"][name] = {"shares": shares, "notional": shares * bar.open}
        where = ", ".join(t["books"]) or "no book had room"
        said.append(f"{t['symbol']}: bought at the open, {bar.open:.2f} ({where})")
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
            n, exit_value = result["notional"], result["notional"] * growth
            fees = sum(sum(costs.order_fees(side=side, value=value, marketable=0, passive=0,
                                            auction=result["shares"]))
                       for side, value in (("buy", n), ("sell", exit_value)))  # fmt: skip
            slip = a * n + (costs.forced_exit_bps / 1e4 if forced else a) * exit_value
            result.update(net=exit_value - n - fees - slip, net_2x=exit_value - n - fees - 2 * slip)
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
        })  # fmt: skip
        said.append(f"{s['symbol']}: signal, up {100 * s['jump']:.0f}% in two days on "
                    f"{s['volume']:.1f}x volume; buy at the next open")  # fmt: skip
    state["last_session"] = day.isoformat()
    return said


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
        )
    due = [t for t in tracks if t["status"] == "open" and t["sessions"] + 1 >= hold]
    lines += ["", "## Sell at the next close (an on-close order)", ""]
    lines += [f"- **{t['symbol']}**, bought {t['entry_day']}" for t in due] or ["Nothing."]
    today = date.fromisoformat(day) if day else None
    lines += ["", "## Held now", "",
              f"| Stock | Signal | Bought | At | Now | {BENCHMARK} since | Sessions | Books |",
              "|---|---|---|---|---|---|---|---|"]  # fmt: skip
    unrealised = dict.fromkeys(books, 0.0)
    hedged = dict.fromkeys(books, 0.0)
    for t in (t for t in tracks if t["status"] == "open"):
        bar = bars.get(t["symbol"])
        change = bar.close / t["entry_open"] - 1 if bar else None
        fund = _benchmark(window, date.fromisoformat(t["entry_day"]), today)
        for name, result in t["books"].items():
            unrealised[name] += result["notional"] * (change or 0.0)
            hedged[name] += result["notional"] * ((change or 0.0) - (fund or 0.0))
        now = f"{bar.close:.2f} ({100 * change:+.1f}%)" if bar else "n/a"
        since = f"{100 * fund:+.1f}%" if fund is not None else "n/a"
        lines.append(f"| {t['symbol']} | {t['signal_day']} | {t['entry_day']} | "
                     f"{t['entry_open']:.2f} | {now} | {since} | {t['sessions']} of {hold} | "
                     f"{', '.join(t['books']) or 'none (followed only)'} |")  # fmt: skip
    lines += ["", "Open positions, before costs: " + "; ".join(
        f"{name} ${unrealised[name]:+,.0f} (${hedged[name]:+,.0f} with the same dollars of "
        f"{BENCHMARK} sold short)" for name in books) + "."]  # fmt: skip
    closed = [t for t in tracks if t["status"] == "closed"]
    lines += ["", "## Results so far", ""]
    if closed:
        gross = [t["gross_return"] for t in closed]
        lines.append(f"Every signal, whether or not a book took it: {len(closed)} finished, "
                     f"mean {100 * statistics.fmean(gross):+.2f}% before costs, "
                     f"{sum(g > 0 for g in gross)} winners.")  # fmt: skip
        ahead = [t["gross_return"] - t["benchmark_return"] for t in closed
                 if t.get("benchmark_return") is not None]  # fmt: skip
        if ahead:
            lines.append(f"Against {BENCHMARK} over the same days ({len(ahead)} trades): "
                         f"{100 * statistics.fmean(ahead):+.2f}% a trade.")  # fmt: skip
        lines += ["", "| Book | Trades | A trade | A trade, costs doubled | Total | Doubled |",
                  "|---|---|---|---|---|---|"]  # fmt: skip
        for name in books:
            mine = [t["books"][name] for t in closed if name in t["books"]]
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


def paper_dir(runs_dir: Path, name: str) -> Path:
    """Where a strategy's paper ledger lives: beside the run store, outside the repository."""
    return Path(os.environ.get("KINN_PAPER_DIR") or runs_dir.parent / "paper") / name


def load_state(folder: Path) -> dict:
    path = folder / "state.json"
    return json.loads(path.read_text()) if path.exists() else new_state()


def save(folder: Path, state: dict, page: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / "state.json.tmp"
    tmp.write_text(json.dumps(state, indent=1) + "\n")
    os.replace(tmp, folder / "state.json")
    (folder / "report.md").write_text(page)
