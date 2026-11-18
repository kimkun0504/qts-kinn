"""strategies/intraday_shape/HYPOTHESIS.md, addendum "the warning as a filter on the two rules
that work": skip A50 and rule I signals in stocks pushed up into the close.

    cd research/claude
    uv run python late_push_filter.py
"""

from __future__ import annotations

import tempfile

import duckdb
import numpy as np
from swing_earnings import AUCTION

from intraday_shape import folder as shape
from kinn.core.settings import load_settings

A50 = "earn and ret2 >= 0.15 and dvr2 >= 5 and mcap >= 5e7 and mcap < 3e8"
SPANS = {"2010-2017": (2010, 2017), "2005-2009": (2005, 2009), "2018-2022": (2018, 2022), "2023": (2023, 2023)}


def main() -> None:
    settings = load_settings()
    swing = settings.data_dir / "research" / "swing"
    insider = settings.data_dir / "research" / "insider"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""create table rank as
            select day, permaticker, percent_rank() over (partition by day order by l10) as pct
            from '{shape()}/scores.parquet' where mcap >= 5e7 and mcap < 3e8"""
    )
    a50 = con.sql(
        f"""with s as (
                select day, permaticker, exp(first_day + c_exit15 - c_next) - 1 - ({AUCTION}) as net
                from read_parquet('{swing}/early_*.parquet') where {A50} and next_open is not null and day >= DATE '2005-01-03'
                union all
                select day, permaticker, exp(first_day + c_exit15 - c_next) - 1 - ({AUCTION})
                from read_parquet('{swing}/wide_*.parquet') where {A50} and next_open is not null and day <= DATE '2023-10-13')
            select year(s.day), s.net, r.pct from s left join rank r using (day, permaticker)
            where s.net is not null"""
    ).fetchall()
    rows = con.sql(
        f"""select day, permaticker, ordinal, g15 - cost as net from (
                select *, date_diff('day', DATE '1970-01-01', day) as ordinal
                from read_parquet('{insider}/signals_*.parquet')
                where mcap >= 5e7 and mcap < 3e8 and dollars >= 1e5 and insiders >= 1 and g15 is not null
                  and day between DATE '2006-01-03' and DATE '2023-09-29')
            order by day, symbol"""
    ).fetchall()
    kept, last = [], {}
    for day, company, ordinal, net in rows:  # one signal a company in any 21 days, as rule I
        if ordinal - last.get(company, -(10**9)) >= 21:
            last[company] = ordinal
            kept.append((day, company, net))
    con.execute("create table ri (day date, permaticker bigint, net double)")
    con.executemany("insert into ri values (?, ?, ?)", kept)
    rule_i = con.sql("select year(ri.day), ri.net, r.pct from ri left join rank r using (day, permaticker)").fetchall()
    for name, data in (("A50", a50), ("rule I", rule_i)):
        years = np.array([r[0] for r in data])
        net = np.array([r[1] for r in data], dtype=float)
        pct = np.array([np.nan if r[2] is None else r[2] for r in data], dtype=float)
        print(f"{name}: {len(net)} signals, {np.isnan(pct).mean() * 100:.0f}% without a score (kept)")
        for cut in (0.8, 0.9):
            skip = pct >= cut
            cells = []
            for span, (a, b) in SPANS.items():
                inside = (years >= a) & (years <= b)
                cells.append(f"{span}: all {100 * net[inside].mean():5.2f}% ({inside.sum()})  kept {100 * net[inside & ~skip].mean():5.2f}%  "
                             f"skipped {100 * net[inside & skip].mean():6.2f}% ({(inside & skip).sum()})")  # fmt: skip
            print(f"  skip top {100 * (1 - cut):.0f}%:\n    " + "\n    ".join(cells))


if __name__ == "__main__":
    main()
