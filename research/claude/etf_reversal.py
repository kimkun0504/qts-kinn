"""Short falls in index funds (strategies/etf_reversal/HYPOTHESIS.md): eight cells, chosen on
2004 to 2014 and tested on 2015 to October 2023.

    cd research/claude && uv run python etf_reversal.py
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date

import numpy as np

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly

FUNDS = ["SPY", "QQQ", "IWM", "DIA", "MDY", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU",
         "XLV", "XLY"]  # fmt: skip
COST, MAX_HOLD, ACCOUNT, SLOTS = 0.0003, 10, 20000.0, 4
SPANS = {"chosen 2004-14": (2004, 2014), "tested 2015-23": (2015, 2023)}


def load() -> dict[str, dict[str, np.ndarray]]:
    """Each fund's sessions with an adjusted close and open (log, splits removed)."""
    store = DataStore(load_settings())
    table = store.daily(date(2003, 9, 10), date(2023, 10, 13), symbols=[*FUNDS, "QQQQ"])
    rows = defaultdict(list)
    for r in table.to_pylist():
        rows["QQQ" if r["symbol"] == "QQQQ" else r["symbol"]].append(r)
    out = {}
    for symbol, bars in rows.items():
        bars.sort(key=lambda r: r["date"])
        days = np.array([r["date"] for r in bars])
        o = np.array([float(r["open"]) for r in bars])
        c = np.array([float(r["close"]) for r in bars])
        night = np.r_[0.0, np.log(o[1:] / c[:-1])]
        actions = np.abs(night) > 0.12
        night[actions] = 0.0  # a split or a special distribution, not a move
        inside = np.log(c / o)
        close = np.cumsum(night + inside)  # adjusted log close
        out[symbol] = {"day": days, "close": close, "open": close - inside,
                       "actions": int(actions.sum())}  # fmt: skip
    return out


def signals(f: dict, kind: str, n: int, trend: bool) -> np.ndarray:
    c = f["close"]
    k = len(c)
    hit = np.zeros(k, bool)
    for i in range(210, k - 1):
        if kind == "low":
            ok = c[i] < c[i - n : i].min()
        else:
            ok = all(c[i - j] < c[i - j - 1] for j in range(n))
        if ok and trend:
            ok = c[i] > math.log(np.exp(c[i - 199 : i + 1]).mean())
        hit[i] = ok
    return hit


def trades(f: dict, hit: np.ndarray) -> list[tuple]:
    """(signal day, entry day, exit day, net return, the fall that set it off) for each
    signal; no new trade in a fund while one is open."""
    c, o, days = f["close"], f["open"], f["day"]
    out, busy_until = [], -1
    for i in np.flatnonzero(hit):
        if i <= busy_until or i + 1 >= len(c):
            continue
        entry = i + 1
        last = min(entry + MAX_HOLD - 1, len(c) - 1)
        leave = last
        for j in range(entry, last + 1):
            if c[j] > math.log(np.exp(c[j - 4 : j + 1]).mean()):
                leave = j
                break
        gross = math.exp(c[leave] - o[entry])
        net = gross * (1 - COST) - (1 + COST)
        out.append((days[i], days[entry], days[leave], net, c[i] - c[i - 5],
                    [(days[j], math.exp(c[j] - o[entry])) for j in range(entry, leave + 1)]))  # fmt: skip
        busy_until = leave
    return out


def book(found: list[tuple]) -> dict[int, float]:
    """Profit by year of the $20,000 book: at most four positions, the largest fall first,
    marked at each close."""
    by_entry = defaultdict(list)
    for t in found:
        by_entry[t[1]].append(t)
    open_until: list = []
    year = defaultdict(float)
    for day in sorted(by_entry):
        open_until = [d for d in open_until if d >= day]
        for t in sorted(by_entry[day], key=lambda t: t[4]):
            if len(open_until) >= SLOTS:
                continue
            open_until.append(t[2])
            size, before = ACCOUNT / SLOTS, 1.0
            year[day.year] -= size * COST
            for d, value in t[5]:
                year[d.year] += size * (value - before)
                before = value
            year[t[2].year] -= size * t[5][-1][1] * COST
    return year


def main() -> None:
    funds = load()
    print("funds:", ", ".join(f"{s} ({len(f['day'])} sessions, {f['actions']} adjustments)"
                              for s, f in sorted(funds.items())))  # fmt: skip
    for kind, n, trend in [(k, n, t) for k, ns in (("low", (5, 10)), ("falls", (3, 4)))
                           for n in ns for t in (True, False)]:  # fmt: skip
        found = []
        for f in funds.values():
            found += trades(f, signals(f, kind, n, trend))
        label = (f"{'a new ' + str(n) + '-day low close' if kind == 'low' else str(n) + ' falling closes'}"
                 f"{', above the 200-day average' if trend else ''}")  # fmt: skip
        print(label)
        totals = book(found)
        for name, (a, b) in SPANS.items():
            part = [t for t in found if a <= t[0].year <= b]
            net = np.array([t[3] for t in part])
            week = np.array([(t[0] - date(2003, 12, 29)).days // 7 for t in part])
            _, tstat, _ = weekly(net, week)
            held = np.mean([len(t[5]) for t in part])
            by = {y: np.mean([t[3] for t in part if t[0].year == y]) for y in range(a, b + 1)
                  if any(t[0].year == y for t in part)}  # fmt: skip
            money = [totals.get(y, 0.0) for y in range(a, b + 1)]
            print(f"   {name}: {len(net):5d} trades, {100 * net.mean():5.2f}% a trade, weekly t "
                  f"{tstat:5.2f}, winners {100 * (net > 0).mean():3.0f}%, held {held:.1f} sessions, "
                  f"years positive {sum(v > 0 for v in by.values())}/{len(by)}; book ${np.mean(money):6,.0f} "
                  f"a year, worst year ${min(money):7,.0f}, losing years {sum(m < 0 for m in money)}")  # fmt: skip


if __name__ == "__main__":
    main()
