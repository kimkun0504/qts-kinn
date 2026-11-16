"""Rule I (insider buying) beside the earnings rule in one book
(strategies/insider_buying/HYPOTHESIS.md, addendum of 2026-11-16).

    uv run python research/claude/insider_book.py
"""

from __future__ import annotations

import tempfile
from collections import defaultdict

import duckdb
import numpy as np

import insider_study as study
import swing_book as book
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

RULE_I = ("$50M-$300M", 1e5, 1, False, False)
HOLD = 15


def insider_paths() -> dict:
    kept = []
    for period in ("early", "choose", "late", "check"):
        d = study.rows(period)
        keep = study.pick(d, *RULE_I)
        kept += [(int(p), str(day)[:10], float(dollars), float(c) / 2, float(c1) / 2)
                 for p, day, dollars, c, c1 in zip(d["permaticker"][keep], d["day"][keep],
                                                   d["dollars"][keep], d["cost"][keep],
                                                   d["cost1"][keep], strict=True)]  # fmt: skip
    store = DataStore(load_settings())
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    con.execute(
        "create table s (permaticker bigint, day date, dollars double, c0 double, c1 double)"
    )
    con.executemany("insert into s values (?, ?, ?, ?, ?)", kept)
    rows = con.sql(
        f"""with p as (
                select permaticker, date, symbol, ln(close / prev_close) as lr,
                       ln(close / open) as first,
                       row_number() over (partition by permaticker order by date) as rn
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'),
            k as (select s.*, p.rn, p.symbol from s join p
                  on p.permaticker = s.permaticker and p.date = s.day)
            select k.day, k.symbol, k.dollars, k.c0, k.c1, p.date,
                   case when p.rn = k.rn + 1 then p.first else p.lr end as r
            from k join p on p.permaticker = k.permaticker
                         and p.rn between k.rn + 1 and k.rn + {HOLD}
            order by k.day, k.symbol, p.date"""
    ).fetchall()
    found: dict = {}
    for day, symbol, dollars, c0, c1, session, r in rows:
        t = found.setdefault((day, symbol, "I"), {"priority": dollars, "costs": (c0, c1, c1),
                                                  "dates": [], "r": []})  # fmt: skip
        t["dates"].append(session)
        t["r"].append(r)
    return found


def show(found: dict, label: str) -> None:
    for basis, name in ((0, "auction basis"), (1, "spread crossed")):
        days, pnl, taken, skipped, _ = book.run(found, basis)
        keep = np.array([d.year >= 2006 for d in days])
        days, pnl = [d for d in days if d.year >= 2006], pnl[keep]
        equity = np.cumsum(pnl)
        drawdown = (np.maximum.accumulate(equity) - equity).max()
        years = (days[-1] - days[0]).days / 365.25
        by = defaultdict(float)
        for d, x in zip(days, pnl, strict=True):
            by[d.year] += x
        losing = [y for y, v in by.items() if v < 0]
        print(f"{label:28} {name:14} taken {taken:5d}  ${equity[-1] / years:7,.0f} a year  Sharpe "
              f"{pnl.mean() / pnl.std(ddof=1) * 252**0.5:4.2f}  drawdown ${drawdown:7,.0f}  "
              f"losing years {len(losing)} {sorted(losing)}")  # fmt: skip
        if basis == 0:
            print("      " + "  ".join(f"{y}: {v:,.0f}" for y, v in sorted(by.items())))


def main() -> None:
    earnings: dict = {}
    for period in ("early", "search", "check"):
        earnings.update(book.paths("A50", period, "dvr2"))
    earnings = {k: v for k, v in earnings.items() if k[0].year >= 2006}
    for t in earnings.values():
        t["priority"] = 1e12 + (t["priority"] or 0)  # the earnings rule takes a slot first
    insiders = insider_paths()
    print(len(earnings), "earnings signals;", len(insiders), "insider signals")
    show(earnings, "earnings rule alone")
    show(insiders, "rule I alone")
    show({**insiders, **earnings}, "both, earnings first")


if __name__ == "__main__":
    main()
