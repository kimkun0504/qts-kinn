"""The auction-fill measurement for the earnings drift (strategies/earnings_drift/HYPOTHESIS.md,
addendum of 2026-11-16): from the owner's tick sample, whether the bar's open and close are
auction prints, how they sit against the quotes, and what a market order would pay instead.

    uv run python research/claude/swing_fill_measure.py
"""

from __future__ import annotations

import csv
import gzip
import json
from datetime import date

import numpy as np

from kinn.core.settings import load_settings
from kinn.data import quotes

NAME = "swing_auction"
OPEN_CROSS, CLOSE_CROSS = {25, 17}, {8, 19}
SECOND = 1_000_000_000


def read(path) -> list[dict]:
    if not path.exists():
        return []
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def quote_at(rows: list[dict], when: int) -> tuple[float, float] | None:
    """The last two-sided, uncrossed national quote at or before ``when``."""
    best = None
    for q in rows:
        if q["sip_timestamp"] > when:
            break
        bid, ask = q.get("bid_price") or 0, q.get("ask_price") or 0
        if bid > 0 and ask > bid:
            best = (bid, ask)
    return best


def main() -> None:
    settings = load_settings()
    raw = settings.raw_dir / "massive" / "quotes_sample" / NAME
    with open(settings.data_dir / "quotes_sample" / NAME / "windows.csv") as handle:
        windows = list(csv.DictReader(handle))
    rows = []
    for w in windows:
        day, entry = date.fromisoformat(w["day"]), w["side"] == "entry"
        trades = read(quotes.sample_file(raw, "trades", day, w["symbol"]))
        nbbo = sorted(read(quotes.sample_file(raw, "quotes", day, w["symbol"])),
                      key=lambda q: q["sip_timestamp"])  # fmt: skip
        auction = int(w["entry_ns"]) + (0 if entry else 60 * SECOND)  # 09:30 or 16:00
        wanted = OPEN_CROSS if entry else CLOSE_CROSS
        cross = [t for t in trades if wanted & set(t.get("conditions") or [])]
        cross.sort(key=lambda t: -t["size"])
        near = quote_at(nbbo, auction + (30 if entry else -30) * SECOND)
        bar = float(w["entry_price"])
        rows.append({
            "entry": entry, "big": float(w["adv20_prev"]) >= 1e6, "bar": bar,
            "cross": cross[0]["price"] if cross else np.nan,
            "cross_dollars": sum(t["price"] * t["size"] for t in cross) if cross else 0.0,
            "bid": near[0] if near else np.nan, "ask": near[1] if near else np.nan,
            "ticks": len(trades),
        })  # fmt: skip

    def col(name, keep):
        return np.array([r[name] for r in rows if keep(r)], dtype=float)

    def pct(v):
        return f"{100 * v:+.2f}%"

    print(f"{len(rows)} windows; no trades at all in {sum(r['ticks'] == 0 for r in rows)}")
    for label, group in (("under $1M a day", lambda r: not r["big"]),
                         ("$1M a day and over", lambda r: r["big"]), ("all", lambda r: True)):  # fmt: skip
        print(f"\n== {label}")
        total = 0.0
        for side, entry in (("entry (open)", True), ("exit (close)", False)):
            keep = lambda r, e=entry: group(r) and r["entry"] == e  # noqa: E731
            bar, cross, dollars = col("bar", keep), col("cross", keep), col("cross_dollars", keep)
            bid, ask = col("bid", keep), col("ask", keep)
            has, quoted = ~np.isnan(cross), ~np.isnan(bid)
            mid = (bid + ask) / 2
            sign = 1 if entry else -1
            # What joining the cross costs against the midpoint beside it (positive = a cost).
            fair = sign * (cross - mid) / mid
            # What a market order beside the auction pays against the bar's price.
            market = (ask / bar - 1) if entry else (1 - bid / bar)
            both = has & quoted
            total += np.nanmean(market)
            print(f"  {side}: {len(bar)} windows; a cross print in {100 * has.mean():.0f}%, median "
                  f"${np.median(dollars[has]):,.0f} (a tenth under ${np.quantile(dollars[has], 0.1):,.0f});"
                  f" cross equals the bar's price in {100 * np.mean(np.abs(cross[has] / bar[has] - 1) < 1e-9):.0f}%")  # fmt: skip
            print(f"      cross against the midpoint beside it: mean {pct(np.mean(fair[both]))}, "
                  f"median {pct(np.median(fair[both]))}; half-spread there: mean "
                  f"{pct(np.nanmean((ask - bid) / 2 / mid))}, median {pct(np.nanmedian((ask - bid) / 2 / mid))}")  # fmt: skip
            print(f"      a market order against the bar's price: mean {pct(np.nanmean(market))}, "
                  f"median {pct(np.nanmedian(market))}, worst tenth {pct(np.nanquantile(market, 0.9))}"
                  f" ({int(quoted.sum())} quoted)")  # fmt: skip
        print(f"  both sides, market orders: {pct(total)} a trade")


if __name__ == "__main__":
    main()
