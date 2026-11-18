"""Paper trading for the after-hours short (strategies/after_hours, the lead of 17 November).

A company of $300M to $2B files its results (an 8-K with item 2.02) after the close; half an
hour after the SEC accepted it, its stock trades 15% or more under the 16:00 price with at
least $50,000 traded since 16:00. The paper trade sells short at the low of the next minute
that trades and buys back at the next session's open; beside it the ledger records the
better exit of the research, held through that session and bought back at 15:30. Nothing here sends an order or touches
the network or the research data: the owner's tool (``tools/owner/paper_after_hours.py``)
fetches the SEC's filings and the vendor's minute bars and hands them to these functions.

The rule is the one measured in ``research/claude/after_hours.py`` (``collect`` and
``collect_lows``, the cell "short mid down15 open"); a test holds this code to the same
reading on the same bars. The candidates come from every results 8-K of the evening, never
from what the stock did the next morning, so the ledger cannot be biased toward winners.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
OPEN, CLOSE, LAST_ACCEPTED = 570, 960, 1110  # 09:30, 16:00, 18:30 as minutes of the day
CAP_MIN, CAP_MAX = 3e8, 2e9
FALL = -0.15
MIN_DOLLARS, MIN_ADV, MIN_PRICE, THIN = 50_000.0, 250_000.0, 1.0, 5_000.0
BORROW_NIGHT = 0.10 / 252  # a night's borrow at 10% a year, as the research charged
EARNINGS_ITEM = "2.02"


@dataclass(frozen=True)
class MinuteBar:
    minute: int  # minutes after midnight, New York time
    high: float
    low: float
    close: float
    volume: float


def minute_bars(results: list[dict] | None, day: date) -> list[MinuteBar]:
    """The vendor's minute aggregates (``t`` in milliseconds since the epoch) for ``day``, in
    New York minutes, sorted. Bars of other days and broken bars are dropped."""
    out = []
    for r in results or []:
        try:
            when = datetime.fromtimestamp(int(r["t"]) / 1000, tz=NEW_YORK)
            bar = MinuteBar(
                when.hour * 60 + when.minute,
                float(r["h"]),
                float(r["l"]),
                float(r["c"]),
                float(r["v"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
        if when.date() == day and bar.low > 0 and bar.close > 0:
            out.append(bar)
    return sorted(out, key=lambda b: b.minute)


def daily_index_8k(text: str) -> list[int]:
    """The filer CIKs of the 8-Ks (not amendments) in an EDGAR daily form index."""
    ciks = set()
    for line in text.splitlines():
        if not line.startswith("8-K "):
            continue
        path = line.split()[-1]  # edgar/data/<cik>/<accession>.txt
        try:
            ciks.add(int(path.split("/")[2]))
        except (IndexError, ValueError):
            continue
    return sorted(ciks)


def results_filings(submissions: dict, day: date) -> list[dict]:
    """The results 8-Ks in a company's SEC submissions that were accepted on ``day`` between
    16:00 and 18:30 New York time, with the minute each was accepted."""
    recent = (submissions.get("filings") or {}).get("recent") or {}
    forms = recent.get("form") or []
    items = recent.get("items") or [""] * len(forms)
    accepted = recent.get("acceptanceDateTime") or [None] * len(forms)
    numbers = recent.get("accessionNumber") or [""] * len(forms)
    found = []
    for i, form in enumerate(forms):
        if form != "8-K" or EARNINGS_ITEM not in (items[i] or "").split(",") or not accepted[i]:
            continue
        try:
            when = datetime.fromisoformat(accepted[i].replace("Z", "+00:00")).astimezone(NEW_YORK)
        except ValueError:
            continue
        minute = when.hour * 60 + when.minute
        if when.date() == day and CLOSE <= minute <= LAST_ACCEPTED:
            found.append({"accession": numbers[i], "minute": minute})
    return sorted(found, key=lambda f: f["minute"])


def reading(bars: list[MinuteBar], accepted_minute: int) -> dict | None:
    """The rule's reading half an hour after the filing was accepted, or None when the bars
    do not allow one (as the research skipped it). ``reaction`` is the last after-hours price
    before the reading against the last regular-session price; ``entry`` is the low of the
    next minute that trades, within 20 minutes."""
    regular = [b for b in bars if OPEN <= b.minute <= CLOSE]
    if not regular:
        return None
    base = regular[-1].close
    at = min(max(accepted_minute + 30, 990), 1170)
    before = [i for i, b in enumerate(bars) if b.minute < at]
    if not before:
        return None
    k = before[-1]
    e = k + 1
    if (
        bars[k].minute <= CLOSE
        or e >= len(bars)
        or bars[e].minute <= CLOSE
        or bars[e].minute > at + 20
    ):
        return None
    traded = sum(b.close * b.volume for b in bars[: k + 1] if b.minute > CLOSE)
    return {
        "base": base,
        "reading_minute": at,
        "reaction": bars[k].close / base - 1,
        "traded": traded,
        "entry": bars[e].low,
        "entry_minute": bars[e].minute,
        "entry_high": bars[e].high,
        "entry_dollars": bars[e].close * bars[e].volume,
    }


def is_signal(read: dict | None, market_cap: float | None, adv: float | None) -> tuple[bool, str]:
    """Whether a reading is a signal of the lead, and if not, why."""
    if read is None:
        return False, "no reading (too few after-hours trades around it)"
    if market_cap is None or not CAP_MIN <= market_cap < CAP_MAX:
        return False, "market value outside $300M to $2B"
    if adv is None or adv < MIN_ADV:
        return False, "under $250,000 a day"
    if read["traded"] < MIN_DOLLARS:
        return False, f"${read['traded']:,.0f} traded after hours (under $50,000)"
    if read["entry_high"] < MIN_PRICE:
        return False, "under $1"
    if read["reaction"] > FALL:
        return False, f"{100 * read['reaction']:+.1f}% after hours (not down 15%)"
    return True, "signal"


def tier(adv: float) -> float:
    """The auction allowance for the buy-back at the open, by normal dollar volume (one side)."""
    return 0.0025 if adv < 1e6 else 0.0010 if adv < 1e7 else 0.0005 if adv < 1e8 else 0.0002


def settle(entry: float, next_open: float, adv: float) -> dict:
    """The short's return from ``entry`` to the next open, before and after the research's
    costs (the allowance on the buy-back, commission both ways, a night's borrow)."""
    gross = 1 - next_open / entry
    cost = tier(adv) + 2 * min(0.01, max(0.000175, 0.0035 / entry)) + BORROW_NIGHT
    return {"next_open": next_open, "gross": gross, "net": gross - cost}


def price_at(bars: list[MinuteBar], minute: int) -> float | None:
    """The last regular-session price before ``minute`` (the close of the last bar before it)."""
    before = [b for b in bars if OPEN <= b.minute < minute]
    return before[-1].close if before else None


def half_spread(adv: float) -> float:
    """The modelled half-spread for a market order inside the session, by normal dollar volume."""
    return 0.0065 if adv < 1e6 else 0.0018 if adv < 1e7 else 0.0010 if adv < 1e8 else 0.0005


def settle_held(entry: float, price: float, adv: float) -> dict:
    """The short held through the next session and bought back at 15:30 (the better exit of
    the research, a market order with the spread crossed)."""
    gross = 1 - price / entry
    cost = half_spread(adv) + 2 * min(0.01, max(0.000175, 0.0035 / entry)) + BORROW_NIGHT
    return {"price_1530": price, "net_1530": gross - cost}


def new_state() -> dict:
    return {"strategy": "after_hours_short", "evenings": [], "signals": [], "seen": []}


def record(state: dict, day: date, signals: list[dict], seen: list[dict]) -> None:
    """Add one evening (its signals and every results 8-K looked at); replaces the evening if
    it was recorded before."""
    key = day.isoformat()
    state["signals"] = [s for s in state["signals"] if s["day"] != key] + signals
    state["seen"] = [s for s in state["seen"] if s["day"] != key] + seen
    state["evenings"] = sorted(set(state["evenings"]) | {key})


def pending(state: dict) -> list[dict]:
    """Signals still waiting for their next open."""
    return [s for s in state["signals"] if s.get("net") is None]


def report(state: dict) -> str:
    """The ledger as a page."""
    done = [s for s in state["signals"] if s.get("net") is not None]
    lines = [
        "# Paper ledger: the after-hours short",
        "",
        "A company of $300M to $2B down 15% or more half an hour after an after-close results",
        "8-K; sold short at the low of the next minute, bought back at the next open. Paper only.",
        "",
        f"Evenings recorded: {len(state['evenings'])}. "
        f"Results 8-Ks looked at: {len(state['seen'])}. "
        f"Signals: {len(state['signals'])} ({len(done)} closed, "
        f"{len(state['signals']) - len(done)} waiting).",
    ]
    held = [s["net_1530"] for s in done if s.get("net_1530") is not None]
    if done:
        net = [s["net"] for s in done]
        lines.append(
            f"Closed: average {100 * sum(net) / len(net):+.2f}% after costs; "
            f"{sum(n > 0 for n in net)} of {len(net)} made money."
        )
    if held:
        lines.append(
            f"Held to 15:30 instead: average {100 * sum(held) / len(held):+.2f}% on {len(held)}."
        )
    lines += [
        "",
        "| Evening | Stock | Value | After hours | Sold at | Thin minute | Next open "
        "| After costs | Held to 15:30 | Borrow (IBKR) |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in sorted(state["signals"], key=lambda s: (s["day"], s["symbol"])):
        out = "waiting" if s.get("net") is None else f"{100 * s['net']:+.2f}%"
        opened = "" if s.get("next_open") is None else f"${s['next_open']:.2f}"
        held = "" if s.get("net_1530") is None else f"{100 * s['net_1530']:+.2f}%"
        lines.append(
            f"| {s['day']} | {s['symbol']} | ${s['market_cap'] / 1e6:,.0f}M "
            f"| {100 * s['reaction']:+.1f}% | ${s['entry']:.2f} "
            f"| {'yes' if s['entry_dollars'] < THIN else 'no'} | {opened} | {out} | {held} | "
            f"{s.get('borrow') or 'not recorded'} |"
        )
    lines += [
        "",
        "Record what IBKR showed for each signal (shares to borrow, fee) with",
        '`--borrow SYMBOL="yes, 0.3%"`: whether the trade could have been made is the first',
        "thing this ledger has to answer.",
        "",
    ]
    return "\n".join(lines)


def paper_dir(runs_dir: Path) -> Path:
    """Beside the run store, outside the repository, as the earnings ledger."""
    return Path(os.environ.get("KINN_PAPER_DIR") or runs_dir.parent / "paper") / "after_hours"


def load_state(folder: Path) -> dict:
    path = folder / "state.json"
    return json.loads(path.read_text()) if path.exists() else new_state()


def save(folder: Path, state: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / "state.json.tmp"
    tmp.write_text(json.dumps(state, indent=1) + "\n")
    os.replace(tmp, folder / "state.json")
    (folder / "report.md").write_text(report(state))
