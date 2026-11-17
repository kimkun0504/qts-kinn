"""Families 19 and 20 of the swing search: the quality test on jumps other than A50's
(strategies/swing_search/HYPOTHESIS.md, addendum of 2026-11-16 23:40 ET).

    cd research/claude && uv run python swing_quality_more.py
"""

from __future__ import annotations

import tempfile

import duckdb
import numpy as np

from kinn.core.settings import load_settings
from swing_earnings import AUCTION

KINDS = ("earnings, same day", "earnings, next day", "another 8-K", "another filing", "no filing")
PERIODS = {
    "2010-17": ("wide", "d.day between DATE '2010-01-04' and DATE '2017-12-08'"),
    "2005-09": ("early", "d.day between DATE '2005-01-03' and DATE '2009-12-08'"),
    "2018-23": ("wide", """(d.day between DATE '2018-01-02' and DATE '2022-11-30'
                           or d.day between DATE '2023-01-03' and DATE '2023-10-13')"""),
}


def rows(period: str) -> dict[str, np.ndarray]:
    base = load_settings().data_dir / "research" / "swing"
    name, dates = PERIODS[period]
    tail = "_early" if name == "early" else ""
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    table = con.sql(
        f"""select yr, case when e0.permaticker is not null then 0 when earn then 1
                            when k.permaticker is not null then 2
                            when filings_prev > 0 or filings_today > 0 then 3 else 4 end as kind,
                   ret1, ret2, dvr, dvr2, ret250, netcash_price,
                   exp(first_day + c_exit15 - c_next) - 1 - ({AUCTION}) as net,
                   exp(first_day + c_exit15 - c_next) - 1 - 2 * (half_spread + commission) as crossed
            from read_parquet('{base}/{name}_*.parquet') d
            left join '{base}/earn0{tail}.parquet' e0 using (permaticker, day)
            left join '{base}/codes{tail}.parquet' k using (permaticker, day)
            where {dates} and next_open is not null and mcap >= 5e7 and mcap < 3e8
              and (ret1 >= 0.10 or ret2 >= 0.10)"""
    ).to_arrow_table()
    d = {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}
    own = np.isin(d["kind"], (0, 3, 4))  # read on the day's own move; the others on two days
    d["jump"] = np.where(own, d["ret1"], d["ret2"]).astype(float)
    d["volume"] = np.where(own, d["dvr"], d["dvr2"]).astype(float)
    year = d["ret250"].astype(float)
    cash = d["netcash_price"].astype(float)
    d["up"], d["debt"] = year > 0, cash < 0  # a missing fact is NaN: neither up nor net debt
    d["fallen_rich"] = (year <= 0) & (cash >= 0)
    return d


CELLS = [
    ("19 earnings, same day: 15%+, 5x+", 0, (0.15, 9), (5, 1e9)),
    ("19 another 8-K: 15%+, 5x+", 2, (0.15, 9), (5, 1e9)),
    ("19 another filing: 15%+, 5x+", 3, (0.15, 9), (5, 1e9)),
    ("19 no filing: 15%+, 5x+", 4, (0.15, 9), (5, 1e9)),
    ("20 earnings, next day: 15%+, 2x-5x", 1, (0.15, 9), (2, 5)),
    ("20 earnings, next day: 10%-15%, 5x+", 1, (0.10, 0.15), (5, 1e9)),
    ("A50 itself, for reference", 1, (0.15, 9), (5, 1e9)),
]
GROUPS = {
    "all": lambda d: np.ones(len(d["net"]), bool),
    "up or net debt": lambda d: d["up"] | d["debt"],
    "up and net debt": lambda d: d["up"] & d["debt"],
    "down and net cash": lambda d: d["fallen_rich"],
}


def main() -> None:
    data = {p: rows(p) for p in PERIODS}
    for label, kind, (j0, j1), (v0, v1) in CELLS:
        print(label)
        for group, test in GROUPS.items():
            cells, by_year = [], {}
            for period, d in data.items():
                keep = ((d["kind"] == kind) & (d["jump"] >= j0) & (d["jump"] < j1)
                        & (d["volume"] >= v0) & (d["volume"] < v1) & test(d))  # fmt: skip
                net = d["net"][keep].astype(float)
                cells.append(f"{period} {100 * net.mean() if len(net) else float('nan'):6.2f}% "
                             f"({len(net):4d})")  # fmt: skip
                if period == "2018-23":
                    no20 = net[d["yr"][keep] != 2020]
                    cells.append(f"no-2020 {100 * no20.mean() if len(no20) else float('nan'):6.2f}%")
                    crossed = d["crossed"][keep].astype(float)
                for y in sorted(set(d["yr"][keep])):
                    by_year[int(y)] = float(net[d["yr"][keep] == y].mean())
            wins = sum(v > 0 for v in by_year.values())
            print(f"   {group:18} " + "  ".join(cells) + f"  yrs+ {wins}/{len(by_year)}"
                  f"  crossed 2018-23 {100 * crossed.mean() if len(crossed) else float('nan'):5.2f}%")  # fmt: skip


def larger() -> None:
    """Family 22: A50's kind of jump in companies of $300M to $2B."""
    base = load_settings().data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    data = {}
    for period, (name, dates) in PERIODS.items():
        table = con.sql(
            f"""select yr, ret2, dvr2, ret250, netcash_price, high250,
                       exp(first_day + c_exit15 - c_next) - 1 - ({AUCTION}) as net,
                       exp(first_day + c_exit15 - c_next) - 1 - 2 * (half_spread + commission)
                           as crossed
                from read_parquet('{base}/{name}_*.parquet') d
                where {dates} and next_open is not null and earn and mcap >= 3e8 and mcap < 2e9
                  and ret2 >= 0.10 and dvr2 >= 5"""
        ).to_arrow_table()
        d = {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}
        year, cash = d["ret250"].astype(float), d["netcash_price"].astype(float)
        d["up"], d["debt"], d["high"] = year > 0, cash < 0, d["high250"].astype(float) > 0
        d["fallen_rich"] = (year <= 0) & (cash >= 0)
        data[period] = d
    groups = {
        "all": lambda d: np.ones(len(d["net"]), bool),
        "up and net debt": lambda d: d["up"] & d["debt"],
        "at a 250-day high": lambda d: d["high"],
        "up or net debt": lambda d: d["up"] | d["debt"],
        "down and net cash": lambda d: d["fallen_rich"],
    }
    for jump in (0.10, 0.15):
        print(f"$300M to $2B, earnings, two-day jump of {100 * jump:.0f}% or more on 5x volume")
        for group, test in groups.items():
            cells, by_year = [], {}
            for period, d in data.items():
                keep = (d["ret2"].astype(float) >= jump) & test(d)
                net = d["net"][keep].astype(float)
                cells.append(f"{period} {100 * net.mean() if len(net) else float('nan'):6.2f}% "
                             f"({len(net):4d})")  # fmt: skip
                if period == "2018-23":
                    no20 = net[d["yr"][keep] != 2020]
                    cells.append(f"no-2020 {100 * no20.mean() if len(no20) else float('nan'):6.2f}%")
                    crossed = d["crossed"][keep].astype(float)
                for y in sorted(set(d["yr"][keep])):
                    by_year[int(y)] = float(net[d["yr"][keep] == y].mean())
            wins = sum(v > 0 for v in by_year.values())
            print(f"   {group:18} " + "  ".join(cells) + f"  yrs+ {wins}/{len(by_year)}"
                  f"  crossed 2018-23 {100 * crossed.mean() if len(crossed) else float('nan'):5.2f}%")  # fmt: skip


if __name__ == "__main__":
    import sys

    larger() if sys.argv[1:] == ["larger"] else main()
