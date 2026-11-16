"""A rule of the swing search run as a book: $20,000, at most 10 positions of $2,000, no
leverage (strategies/swing_search/HYPOTHESIS.md). A signal read at a close is bought at the
next open if a slot is free (the larger jump first when several arrive together) and sold at
the close 15 sessions after the signal day.

    uv run python research/claude/swing_book.py A early search
"""

from __future__ import annotations

import sys
import tempfile
from collections import defaultdict

import duckdb
import numpy as np

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_early import PERIODS, RULES

HOLD, SLOTS, SIZE, CAPITAL = 15, 10, 2000.0, 20000.0
BASES = {
    "auction basis": """commission + case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                                         when adv < 1e8 then 0.0005 else 0.0002 end""",
    "spread crossed": "commission + half_spread",
    "spread crossed, doubled": "commission + 2 * half_spread",
}


def paths(rule: str, period: str, rank: str = "ret2"):
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    name, dates = PERIODS[period]
    market = "market_early" if name == "early" else "market"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    costs = ", ".join(f"{expr} as cost{i}" for i, expr in enumerate(BASES.values()))
    rows = con.sql(
        f"""with p as (
                select permaticker, date, ln(close / prev_close) as lr, ln(close / open) as first,
                       row_number() over (partition by permaticker order by date) as rn
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'),
            s as (select d.permaticker, d.day, d.symbol, {rank} as priority, {costs}, p.rn
                  from read_parquet('{base}/{name}_*.parquet') d
                  left join '{base}/{market}.parquet' m using (day)
                  join p on p.permaticker = d.permaticker and p.date = d.day
                  where {dates} and next_open is not null and ({RULES.get(rule, rule)}))
            select s.day, s.symbol, s.priority, s.cost0, s.cost1, s.cost2, p.date,
                   case when p.rn = s.rn + 1 then p.first else p.lr end as r
            from s join p on p.permaticker = s.permaticker
                         and p.rn between s.rn + 1 and s.rn + {HOLD}
            order by s.day, s.symbol, p.date"""
    ).fetchall()
    found: dict = {}
    for day, symbol, priority, c0, c1, c2, date, r in rows:
        t = found.setdefault((day, symbol), {"priority": priority, "costs": (c0, c1, c2),
                                             "dates": [], "r": []})  # fmt: skip
        t["dates"].append(date)
        t["r"].append(r)
    return found


def run(found: dict, basis: int, slots: int = SLOTS):
    """Daily profit of the book, and the trades it took."""
    by_entry = defaultdict(list)
    for key, t in found.items():
        by_entry[t["dates"][0]].append((-(t["priority"] or 0), key))
    days = sorted({d for t in found.values() for d in t["dates"]})
    open_until: dict = {}
    daily = dict.fromkeys(days, 0.0)
    taken, skipped, results = 0, 0, []
    for day in days:
        for key in [k for k, last in open_until.items() if last < day]:
            del open_until[key]
        for _, key in sorted(by_entry.get(day, [])):
            if len(open_until) >= slots:
                skipped += 1
                continue
            t = found[key]
            taken += 1
            open_until[key] = t["dates"][-1]
            cost = t["costs"][basis]
            value = SIZE * (1 - cost)
            daily[t["dates"][0]] -= SIZE * cost
            for date, r in zip(t["dates"], t["r"], strict=True):
                moved = value * (np.exp(r) - 1)
                daily[date] += moved
                value += moved
            daily[t["dates"][-1]] -= value * cost
            results.append((key[0], value * (1 - cost) / SIZE - 1))
    return days, np.array([daily[d] for d in days]), taken, skipped, results


def report(found: dict, label: str) -> None:
    print(f"{label}: {len(found)} signals")
    for basis, name in enumerate(BASES):
        days, pnl, taken, skipped, results = run(found, basis)
        equity = np.cumsum(pnl)
        drawdown = (np.maximum.accumulate(equity) - equity).max()
        years = (days[-1] - days[0]).days / 365.25
        sharpe = pnl.mean() / pnl.std(ddof=1) * np.sqrt(252)
        r = np.array([x for _, x in results])
        print(f"  {name:24}: {taken} trades taken, {skipped} skipped; profit ${equity[-1]:,.0f} over "
              f"{years:.1f} years (${equity[-1] / years:,.0f} a year, "
              f"{100 * equity[-1] / years / CAPITAL:.1f}% of ${CAPITAL:,.0f}); a trade "
              f"{100 * r.mean():.2f}%; Sharpe {sharpe:.2f}; worst drawdown ${drawdown:,.0f}")  # fmt: skip
        if basis != 1:
            continue
        by_year = defaultdict(float)
        for d, x in zip(days, pnl, strict=True):
            by_year[d.year] += x
        print("    by year, spread crossed: "
              + "  ".join(f"{y} ${v:,.0f}" for y, v in sorted(by_year.items())))  # fmt: skip


if __name__ == "__main__":
    rule = sys.argv[1]
    found: dict = {}
    for period in sys.argv[2:]:
        found.update(paths(rule, period))
    report(found, f"rule {rule}, {' + '.join(sys.argv[2:])}")
