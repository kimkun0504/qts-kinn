"""Entries and exits for the earnings rule (addendum of 2026-11-16 in
strategies/swing_search/HYPOTHESIS.md): the plain rule against stops, targets, trailing stops,
moving-average exits, other holds and other entries, on A50's signals of 2005 to October 2023.

    uv run python research/claude/swing_exits.py
"""

from __future__ import annotations

import math
import tempfile
from collections import defaultdict

import duckdb
import numpy as np

import swing_book as book
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_early import PERIODS, RULES

BEFORE, AFTER = 25, 32
SPANS = (("2010-2017", 2010, 2017), ("2005-2009", 2005, 2009), ("2018-2023", 2018, 2023))


def load() -> list[dict]:
    """Each A50 signal with its bars from 25 sessions before to 32 after, as multiples of the
    signal day's close (so splits do not matter)."""
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    out = []
    for period in ("early", "search", "check"):
        name, dates = PERIODS[period]
        market = "market_early" if name == "early" else "market"
        rows = con.sql(
            f"""with p as (
                    select permaticker, date, open / close as o, high / close as h, low / close as l,
                           sum(ln(close / prev_close)) over (partition by permaticker order by date) as c,
                           row_number() over (partition by permaticker order by date) as rn
                    from read_parquet('{store.root}/panel/*.parquet')
                    where prev_close > 0 and close > 0 and low > 0 and open > 0
                      and category like '%Common Stock%'),
                s as (select d.permaticker, d.day, d.symbol, d.adv, d.dvr2, d.commission, p.rn, p.c
                      from read_parquet('{base}/{name}_*.parquet') d
                      left join '{base}/{market}.parquet' m using (day)
                      join p on p.permaticker = d.permaticker and p.date = d.day
                      where {dates} and next_open is not null and ({RULES["A50"]}))
                select s.day, s.symbol, s.adv, s.dvr2, s.commission, p.rn - s.rn as k, p.date,
                       exp(p.c - s.c) as close, p.o, p.h, p.l
                from s join p on p.permaticker = s.permaticker
                             and p.rn between s.rn - {BEFORE} and s.rn + {AFTER}
                order by s.day, s.symbol, p.date"""
        ).fetchall()
        trades: dict = {}
        for day, symbol, adv, volume, commission, k, d, close, o, h, low in rows:
            t = trades.setdefault((day, symbol), {"day": day, "symbol": symbol, "adv": adv,
                                                  "volume": volume, "commission": commission,
                                                  "bars": {}})  # fmt: skip
            t["bars"][k] = (d, close * o, close * h, close * low, close)
        out += list(trades.values())
    return out


def spread(adv: float) -> float:
    return 0.01 if adv < 1e6 else 0.0043 if adv < 1e7 else 0.0018 if adv < 1e8 else 0.0005


def allow(adv: float) -> float:
    return 0.0025 if adv < 1e6 else 0.0010 if adv < 1e7 else 0.0005 if adv < 1e8 else 0.0002


def trade(t: dict, *, hold=15, stop=None, target=None, trail=None, ema=None, sig_low=False,
          entry="open", max_gap=None, min_gap=None, limit=None):  # fmt: skip
    """One signal under one variant: None if never entered, else (entry k, exit k, the marks
    as (date, value) with value a multiple of the entry price, and the exit's extra cost)."""
    bars = t["bars"]
    if 1 not in bars:
        return None
    k0, price = 1, bars[1][1]
    gap = bars[1][1] - 1  # the signal close is 1
    if (max_gap is not None and gap > max_gap) or (min_gap is not None and gap < min_gap):
        return None
    if entry == "close":
        price = bars[1][4]
    if limit is not None:
        level, k0 = 1 - limit, None
        for k in (1, 2, 3):
            if k in bars and bars[k][3] <= level:
                k0, price = k, min(bars[k][1], level)
                break
        if k0 is None:
            return None
    last = hold if (trail is None and ema is None) else 30
    last = min(last, max(bars))
    stop_at = price * (1 - stop) if stop else (bars[0][3] if sig_low else None)
    target_at = price * (1 + target) if target else None
    average = None
    if ema:
        alpha = 2 / (ema + 1)
        for k in sorted(k for k in bars if k <= k0):
            average = bars[k][4] if average is None else alpha * bars[k][4] + (1 - alpha) * average
    marks, peak, leave_next_open = [], price, False
    for k in range(k0, last + 1):
        if k not in bars:
            break
        d, o, h, low, c = bars[k]
        inside = not (k == k0 and entry == "close")  # bought at this close: the day is over
        if leave_next_open:
            return k0, k, marks + [(d, o / price)], 0.0
        if inside and stop_at is not None and (k > k0 or limit is None or o > stop_at):
            if o <= stop_at and k > k0:
                return k0, k, marks + [(d, o / price)], 0.0
            if low <= stop_at:
                return k0, k, marks + [(d, stop_at / price)], spread(t["adv"]) - allow(t["adv"])
        if inside and target_at is not None:
            if o >= target_at and k > k0:
                return k0, k, marks + [(d, o / price)], 0.0
            if h >= target_at * 1.002:
                return k0, k, marks + [(d, target_at / price)], 0.0
        marks.append((d, c / price))
        peak = max(peak, c)
        if ema and k > k0:
            average = alpha * c + (1 - alpha) * average
        if (trail and c < peak * (1 - trail)) or (ema and k > k0 and c < average):
            leave_next_open = True
    return k0, min(last, max(bars)), marks, 0.0


VARIANTS = {
    "plain: next open, close after 15": {},
    "hold 5": {"hold": 5}, "hold 10": {"hold": 10}, "hold 20": {"hold": 20},
    "hold 30": {"hold": 30},
    "stop 8%": {"stop": 0.08}, "stop 12%": {"stop": 0.12}, "stop 20%": {"stop": 0.20},
    "stop at the signal day's low": {"sig_low": True},
    "target 15%": {"target": 0.15}, "target 25%": {"target": 0.25}, "target 40%": {"target": 0.40},
    "stop 12% and target 25%": {"stop": 0.12, "target": 0.25},
    "stop 12%, hold 30": {"stop": 0.12, "hold": 30},
    "trailing 15%, to 30": {"trail": 0.15}, "trailing 20%, to 30": {"trail": 0.20},
    "trailing 25%, to 30": {"trail": 0.25},
    "under the 9-day average, to 30": {"ema": 9}, "under the 20-day average, to 30": {"ema": 20},
    "entry: gap up of 5% at most": {"max_gap": 0.05},
    "entry: no gap down": {"min_gap": 0.0},
    "entry: limit 3% under, 3 days": {"limit": 0.03},
    "entry: limit 5% under, 3 days": {"limit": 0.05},
    "entry: the next close": {"entry": "close"},
}  # fmt: skip


def main() -> None:
    signals = load()
    print(f"{len(signals)} signals")
    head = "".join(f" | {name}: n   mean  median  win" for name, _, _ in SPANS)
    print(f"{'variant':34}{head} | days | book: $/yr Sharpe drawdown taken")
    for label, options in VARIANTS.items():
        found, stats = {}, defaultdict(list)
        held = []
        for t in signals:
            result = trade(t, **options)
            if result is None:
                continue
            k0, k1, marks, extra = result
            if not marks:
                continue
            side = t["commission"] + allow(t["adv"])
            net = marks[-1][1] * (1 - side - extra) - (1 + side)
            held.append(k1 - k0 + 1)
            for name, a, b in SPANS:
                if a <= t["day"].year <= b:
                    stats[name].append(net)
            values = [1.0] + [v for _, v in marks]
            returns = [math.log(values[i + 1] / values[i]) for i in range(len(marks))]
            returns[-1] += math.log(1 - extra)
            found[(t["day"], t["symbol"])] = {"priority": t["volume"], "costs": (side, side, side),
                                              "dates": [d for d, _ in marks], "r": returns}  # fmt: skip
        line = f"{label:34}"
        for name, _, _ in SPANS:
            r = np.array(stats[name])
            line += (f" | {len(r):5d} {100 * r.mean():6.2f}% {100 * np.median(r):6.2f}% "
                     f"{100 * (r > 0).mean():3.0f}%")  # fmt: skip
        days, pnl, taken, _, _ = book.run(found, 0)
        equity = np.cumsum(pnl)
        drawdown = (np.maximum.accumulate(equity) - equity).max()
        years = (days[-1] - days[0]).days / 365.25
        sharpe = pnl.mean() / pnl.std(ddof=1) * math.sqrt(252)
        print(f"{line} | {np.mean(held):4.1f} | {equity[-1] / years:7,.0f} {sharpe:5.2f} "
              f"{drawdown:8,.0f} {taken:5d}")  # fmt: skip


if __name__ == "__main__":
    main()
