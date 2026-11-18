"""strategies/insider_confirmed/HYPOTHESIS.md: an insider purchase, then a strong rise on volume.

    cd research/claude
    uv run python insider_confirmed.py search
    uv run python insider_confirmed.py test 10 3 20
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import AUCTION, weekly

from kinn.core.settings import load_settings

CELLS = [(10, 3, 10), (10, 3, 20), (15, 5, 10), (15, 5, 20)]  # rise %, volume x, window
PERIODS = {"search": ("2010-01-04", "2017-12-31"), "early": ("2006-01-03", "2009-12-31"),
           "late": ("2018-01-02", "2022-12-31"), "check": ("2023-01-03", "2023-10-13")}  # fmt: skip


def trades(rise: int, volume: int, window: int) -> dict[str, np.ndarray]:
    settings = load_settings()
    swing = settings.data_dir / "research" / "swing"
    insider = settings.data_dir / "research" / "insider"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    rows = con.execute(
        f"""select day, permaticker, date_diff('day', DATE '1970-01-01', day) as ordinal
            from read_parquet('{insider}/signals_*.parquet')
            where mcap >= 5e7 and mcap < 3e8 and dollars >= 1e5 and insiders >= 1
              and day between DATE '2006-01-03' and DATE '2023-10-13'
            order by day, symbol"""
    ).fetchall()
    kept, last = [], {}
    for day, company, ordinal in rows:  # one a company in any 21 days, as rule I
        if ordinal - last.get(company, -(10**9)) >= 21:
            last[company] = ordinal
            kept.append((day, company))
    con.execute("create table sig (day date, permaticker bigint)")
    con.executemany("insert into sig values (?, ?)", kept)
    t = con.sql(
        f"""with w as (
                select day, permaticker, age, ret2, dvr2, mcap, earn, first_day, c_exit15, c_next, next_open,
                       {AUCTION} as cost
                from read_parquet('{swing}/early_*.parquet') where permaticker in (select permaticker from sig)
                union all
                select day, permaticker, age, ret2, dvr2, mcap, earn, first_day, c_exit15, c_next, next_open, {AUCTION}
                from read_parquet('{swing}/wide_*.parquet') where permaticker in (select permaticker from sig)),
            s as (select sig.day as signal, sig.permaticker, w.age as age0
                  from sig join w on w.permaticker = sig.permaticker and w.day = sig.day),
            c as (select s.signal, w.*,
                         row_number() over (partition by s.permaticker, s.signal order by w.age) as k
                  from s join w on w.permaticker = s.permaticker and w.age between s.age0 + 1 and s.age0 + {window}
                  where w.ret2 >= {rise / 100} and w.dvr2 >= {volume} and w.mcap >= 5e7 and w.mcap < 3e8
                    and w.next_open is not null)
            select day, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week, permaticker,
                   exp(first_day + c_exit15 - c_next) - 1 - cost as net,
                   (earn and ret2 >= 0.15 and dvr2 >= 5) as a50
            from c where k = 1 and day <= DATE '2023-10-13'
            qualify row_number() over (partition by permaticker, day order by signal) = 1
            order by day"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def show(label, d, period):
    a, b = (int(PERIODS[period][0][:4]), int(PERIODS[period][1][:4]))
    keep = (d["yr"] >= a) & (d["yr"] <= b) & ~np.isnan(d["net"].astype(float))
    net = d["net"][keep].astype(float)
    if len(net) < 3:
        return f"{label:24} {len(net)}", {}
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    yearly = {int(y): net[years == y].mean() for y in sorted(set(years))}
    pos = sum(v > 0 for v in yearly.values())
    return (f"{label:24} {len(net):>4} trades  net {100 * net.mean():6.2f}%  median {100 * np.median(net):6.2f}%  "
            f"t {t:5.2f}  yrs {pos} of {len(yearly)}  A50 {d['a50'][keep].sum()}"), yearly  # fmt: skip


def search() -> None:
    for rise, volume, window in CELLS:
        line, _ = show(f"{rise}% {volume}x within {window}", trades(rise, volume, window), "search")
        print(line)


def test(rise, volume, window) -> None:
    d = trades(int(rise), int(volume), int(window))
    for period in ("early", "late"):
        line, yearly = show(f"{rise}% {volume}x within {window} {period}", d, period)
        print(line)
        print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in yearly.items()))


if __name__ == "__main__":
    search() if sys.argv[1] == "search" else test(*sys.argv[2:5])
