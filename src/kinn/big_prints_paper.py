"""Paper trading for big prints (strategies/big_prints, the lead of 18 November).

On a session D, a company of $50M to $300M trades in pieces at least three times the size of
its own normal (shares per trade against the geometric mean of its previous 60 sessions), on
1.5 times its usual dollar volume, closes 0% to 4% up, and has filed no 8-K in the days before
(no 8-K whose reaction session falls from four days before D to D). The paper trade buys at
the open of the next session and sells at the close 20 sessions after D. Nothing here sends an
order or touches the network or the research data: the owner's tool
(``tools/owner/paper_big_prints.py``) fetches the vendor's daily bars and the SEC's filings and
hands them to these functions.

The rule is the one measured in ``research/claude/big_prints.py`` (the cell "small 20 fp>=3");
a test holds these functions to that reading. Two differences, both written down in the
strategy's report: the day's share of large-trade stocks (under 5%, to skip index days) is
counted over every stock with $250,000 a day and $2 or more, as market values are not known
for all of them here; and the vendor's bars are read unadjusted, as in the research.
"""

from __future__ import annotations

import json
import math
import os
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")
NORM, ADV_SESSIONS, HOLD, LONG_HOLD = 60, 20, 20, 40
CAP_MIN, CAP_MAX = 5e7, 3e8
MIN_ADV, MIN_PRICE = 250_000.0, 2.0
FOOTPRINT, MARKET_FOOTPRINT, VOLUME_RATIO, UP_MAX, SHARE_MAX = 3.0, 2.0, 1.5, 0.04, 0.05
NEWS_DAYS = 4
COMMON_STOCK = ("CS", "ADRC")


@dataclass(frozen=True)
class DayBar:
    open: float
    close: float
    volume: float
    transactions: float


Window = dict[date, dict[str, DayBar]]


def day_bars(results: list[dict] | None) -> dict[str, DayBar]:
    """The vendor's grouped daily bars for one session (unadjusted), as {symbol: DayBar}.
    Bars without a trade count are dropped: the indicator cannot be read on them."""
    out = {}
    for r in results or []:
        try:
            bar = DayBar(float(r["o"]), float(r["c"]), float(r["v"]), float(r["n"]))
        except (KeyError, TypeError, ValueError):
            continue
        if bar.open > 0 and bar.close > 0 and bar.volume > 0 and bar.transactions > 0:
            out[r["T"]] = bar
    return out


def measures(window: Window, day: date) -> dict[str, dict]:
    """For every stock that traded on ``day`` with ``NORM`` earlier sessions in the window:
    its footprint, normal dollar volume (median of the previous 20 sessions), previous close,
    the day's return and the day's dollar volume against normal."""
    earlier = sorted(d for d in window if d < day)
    out = {}
    for symbol, bar in window.get(day, {}).items():
        own = [window[d][symbol] for d in earlier if symbol in window[d]][-NORM:]
        if len(own) < NORM:
            continue
        mean_log = sum(math.log(b.volume / b.transactions) for b in own) / NORM
        adv = statistics.median(b.close * b.volume for b in own[-ADV_SESSIONS:])
        prev_close = own[-1].close
        out[symbol] = {
            "symbol": symbol,
            "footprint": (bar.volume / bar.transactions) / math.exp(mean_log),
            "adv": adv,
            "prev_close": prev_close,
            "close": bar.close,
            "ret": bar.close / prev_close - 1,
            "volume_ratio": bar.close * bar.volume / adv if adv > 0 else 0.0,
        }
    return out


def market_share(found: dict[str, dict]) -> float:
    """The share of liquid stocks trading in large pieces on the day (index days run high)."""
    pool = [m for m in found.values() if m["adv"] >= MIN_ADV and m["prev_close"] >= MIN_PRICE]
    return sum(m["footprint"] >= MARKET_FOOTPRINT for m in pool) / len(pool) if pool else 0.0


def candidates(found: dict[str, dict]) -> list[dict]:
    """The stocks that pass every test the bars can answer (size and filings come later)."""
    return sorted(
        (
            m
            for m in found.values()
            if m["footprint"] >= FOOTPRINT
            and m["volume_ratio"] >= VOLUME_RATIO
            and 0 <= m["ret"] <= UP_MAX
            and m["adv"] >= MIN_ADV
            and m["prev_close"] >= MIN_PRICE
        ),
        key=lambda m: m["symbol"],
    )


def reaction_session(accepted: datetime, sessions: list[date]) -> date | None:
    """The first session whose 16:00 close comes after the SEC accepted a filing."""
    local = accepted.astimezone(NEW_YORK)
    for day in sessions:
        if day > local.date() or (day == local.date() and local.hour < 16):
            return day
    return None


def eight_k_times(submissions: dict) -> list[datetime]:
    """The SEC's acceptance times of every 8-K in a company's submissions file."""
    recent = (submissions.get("filings") or {}).get("recent") or {}
    out = []
    for form, accepted in zip(
        recent.get("form", []), recent.get("acceptanceDateTime", []), strict=False
    ):
        if form == "8-K" and accepted:
            try:
                out.append(datetime.fromisoformat(accepted.replace("Z", "+00:00")))
            except ValueError:
                continue
    return out


def quiet(times: list[datetime], day: date, sessions: list[date]) -> bool:
    """No 8-K whose reaction session falls from ``NEWS_DAYS`` calendar days before ``day`` to
    ``day`` (as the research's filter)."""
    for accepted in times:
        r = reaction_session(accepted, sessions)
        if r is not None and day - timedelta(days=NEWS_DAYS) <= r <= day:
            return False
    return True


def confirm(
    candidate: dict, kind: str | None, market_cap: float | None, is_quiet: bool
) -> tuple[bool, str]:
    if kind not in COMMON_STOCK:
        return False, f"not common stock ({kind})"
    if not market_cap or not CAP_MIN <= market_cap < CAP_MAX:
        value = "unknown" if not market_cap else f"${market_cap / 1e6:,.0f}M"
        return False, f"market value {value}"
    if not is_quiet:
        return False, "an 8-K in the last days"
    return True, ""


def tier(adv: float) -> float:
    """The auction allowance a side, by normal dollar volume (as the research)."""
    return 0.0025 if adv < 1e6 else 0.0010 if adv < 1e7 else 0.0005 if adv < 1e8 else 0.0002


def cost(close: float, adv: float) -> float:
    """Round trip: the allowance and commission each way, on the signal day's close."""
    return 2 * (min(0.01, max(0.000175, 0.0035 / close)) + tier(adv))


def settle(
    signal: dict,
    bars: list[tuple[date, float, float]],
    benchmark: list[tuple[date, float, float]],
    last_session: date,
) -> None:
    """Fill a signal from the stock's adjusted (day, open, close) bars after its day: bought
    at the first open, sold at the close of the ``HOLD``-th session (the rule as tested) and,
    beside it, of the ``LONG_HOLD``-th (the longer hold that did better in every period of the
    research). A stock that stops trading is sold at its last close once 14 days pass with no
    bar."""
    after = sorted(b for b in bars if b[0] > date.fromisoformat(signal["day"]))
    if not after:
        return
    signal["entry_day"], signal["entry"] = after[0][0].isoformat(), after[0][1]
    own = {b[0]: b for b in benchmark}
    stopped = len(after) < LONG_HOLD and (last_session - after[-1][0]).days > 14
    for hold, suffix in ((HOLD, ""), (LONG_HOLD, "_40")):
        if signal.get("net" + suffix) is not None:
            continue
        if len(after) >= hold:
            exit_day, exit_price = after[hold - 1][0], after[hold - 1][2]
        elif stopped:
            exit_day, exit_price = after[-1][0], after[-1][2]
            signal["stopped"] = True
        else:
            continue
        signal["exit_day" + suffix], signal["exit" + suffix] = exit_day.isoformat(), exit_price
        signal["gross" + suffix] = exit_price / signal["entry"] - 1
        signal["net" + suffix] = signal["gross" + suffix] - cost(signal["close"], signal["adv"])
        start, end = own.get(after[0][0]), own.get(exit_day)
        signal["benchmark" + suffix] = end[2] / start[1] - 1 if start and end else None


def new_state() -> dict:
    return {"strategy": "big_prints", "evenings": [], "signals": [], "screened": []}


def record(state: dict, day: date, share: float, signals: list[dict], screened: list[dict]) -> None:
    """Add one evening; replaces it if it was recorded before."""
    key = day.isoformat()
    state["signals"] = [s for s in state["signals"] if s["day"] != key] + signals
    state["screened"] = [s for s in state["screened"] if s["day"] != key] + screened
    state["evenings"] = [e for e in state["evenings"] if e["day"] != key] + [
        {"day": key, "share": share}
    ]
    state["evenings"].sort(key=lambda e: e["day"])


def pending(state: dict) -> list[dict]:
    return [s for s in state["signals"] if s.get("net") is None or s.get("net_40") is None]


def report(state: dict) -> str:
    done = [s for s in state["signals"] if s.get("net") is not None]
    lines = [
        "# Paper ledger: big prints",
        "",
        "A company of $50M to $300M trading in pieces three times its normal size, on 1.5 times",
        "its usual volume, up 0% to 4%, with no recent 8-K; bought at the next open, sold at the",
        "close 20 sessions later. Paper only; IWM over the same days is shown beside each trade.",
        "",
        f"Evenings recorded: {len(state['evenings'])}. Signals: {len(state['signals'])} "
        f"({len(done)} closed, {len(state['signals']) - len(done)} open).",
    ]
    if done:
        net = [s["net"] for s in done]
        over = [s["net"] - s["benchmark"] for s in done if s.get("benchmark") is not None]
        lines.append(
            f"Closed: average {100 * sum(net) / len(net):+.2f}% after costs, "
            f"{sum(n > 0 for n in net)} of {len(net)} made money"
            + (f"; {100 * sum(over) / len(over):+.2f}% over IWM." if over else ".")
        )
    skipped = [e["day"] for e in state["evenings"] if e["share"] >= SHARE_MAX]
    longer = [s["net_40"] for s in done if s.get("net_40") is not None]
    if longer:
        average = 100 * sum(longer) / len(longer)
        lines.append(f"Held 40 sessions instead: average {average:+.2f}% on {len(longer)}.")
    if skipped:
        lines.append(
            f"Skipped as index days (share of large-trade stocks 5% or more): {', '.join(skipped)}."
        )
    lines += [
        "",
        "| Day | Stock | Value | Trade size x | Up | Volume x | Bought | Sold | After costs "
        "| IWM | 40 sessions |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in sorted(state["signals"], key=lambda s: (s["day"], s["symbol"])):
        bought = "" if s.get("entry") is None else f"{s['entry_day']} ${s['entry']:.2f}"
        sold = (
            ""
            if s.get("exit") is None
            else f"{s['exit_day']} ${s['exit']:.2f}" + (" (stopped)" if s.get("stopped") else "")
        )
        out = "open" if s.get("net") is None else f"{100 * s['net']:+.2f}%"
        bench = "" if s.get("benchmark") is None else f"{100 * s['benchmark']:+.2f}%"
        longer = "" if s.get("net_40") is None else f"{100 * s['net_40']:+.2f}%"
        lines.append(
            f"| {s['day']} | {s['symbol']} | ${s['market_cap'] / 1e6:,.0f}M | {s['footprint']:.1f} "
            f"| {100 * s['ret']:+.1f}% | {s['volume_ratio']:.1f} | {bought} | {sold} | {out} "
            f"| {bench} | {longer} |"
        )
    lines.append("")
    return "\n".join(lines)


def paper_dir(runs_dir: Path) -> Path:
    """Beside the run store, outside the repository, as the other ledgers."""
    return Path(os.environ.get("KINN_PAPER_DIR") or runs_dir.parent / "paper") / "big_prints"


def load_state(folder: Path) -> dict:
    path = folder / "state.json"
    return json.loads(path.read_text()) if path.exists() else new_state()


def save(folder: Path, state: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / "state.json.tmp"
    tmp.write_text(json.dumps(state, indent=1) + "\n")
    os.replace(tmp, folder / "state.json")
    (folder / "report.md").write_text(report(state))
