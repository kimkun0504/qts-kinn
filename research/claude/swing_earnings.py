"""Family 17 of the swing search: earnings drift in small stocks, refined (addendum of
2026-11-16 in strategies/swing_search/HYPOTHESIS.md). The rule is chosen on signals of 2010 to
2017 and then tested, once, on 2018 to 2022.

    uv run python research/claude/swing_earnings.py choose
    uv run python research/claude/swing_earnings.py test same 0.15 5 0.5 micro 3 15
"""

from __future__ import annotations

import argparse
import itertools
import sys
import tempfile
from collections import defaultdict

import duckdb
import numpy as np

from kinn.core.settings import load_settings

READS = ("same", "next")
JUMPS = (0.05, 0.10, 0.15, 0.25)
VOLUMES = (0.0, 2.0, 5.0)
CLOSES = (0.0, 0.5, 0.8)
CAPS = ("micro", "small", "both")
PRICES = (1.0, 3.0, 5.0)
HOLDS = (5, 10, 15)
AUCTION = """2 * (commission + case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                                   when adv < 1e8 then 0.0005 else 0.0002 end)"""


def rows(period: str) -> dict[str, np.ndarray]:
    settings = load_settings()
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    holds = ", ".join(
        f"exp(first_day + c_exit{h} - c_next) - 1 as g{h}, m.mk{h}, (ahead < {h})::int as gone{h}"
        for h in HOLDS
    )
    table = con.sql(
        f"""select d.day::varchar as day, d.symbol, yr,
                   (date_diff('day', DATE '2009-12-28', d.day) // 7) as week,
                   e0.permaticker is not null as same,
                   case when e0.permaticker is not null then ret1 else ret2 end as jump,
                   case when e0.permaticker is not null then dvr else dvr2 end as volume,
                   loc, mcap, close, adv, {AUCTION} as cost,
                   2 * (2 * half_spread + commission) as cost2, {holds}
            from read_parquet('{base}/wide_*.parquet') d
            left join '{base}/market.parquet' m using (day)
            left join '{base}/earn0.parquet' e0 using (permaticker, day)
            where {period} and next_open is not null and mcap < 2e9
              and (e0.permaticker is not null and ret1 >= 0.05
                   or earn and e0.permaticker is null and ret2 >= 0.05)"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def pick(d: dict, read: str, jump: float, volume: float, closed: float, cap: str, price: float):
    keep = (d["same"] == (read == "same")) & (d["jump"] >= jump) & (d["close"] >= price)
    if volume:
        keep &= d["volume"] >= volume
    if closed:
        keep &= d["loc"] >= closed
    if cap == "micro":
        keep &= d["mcap"] < 3e8
    elif cap == "small":
        keep &= d["mcap"] >= 3e8
    return keep


def weekly(values: np.ndarray, weeks: np.ndarray) -> tuple[float, float, int]:
    """Mean of the weekly means, its t-statistic, and the number of weeks."""
    sums: dict[int, list[float]] = defaultdict(lambda: [0.0, 0])
    for v, w in zip(values, weeks, strict=True):
        sums[w][0] += v
        sums[w][1] += 1
    means = np.array([s / n for s, n in sums.values()])
    if len(means) < 3:
        return 0.0, 0.0, len(means)
    return means.mean(), means.mean() / (means.std(ddof=1) / len(means) ** 0.5), len(means)


def choose() -> None:
    d = rows("d.day between DATE '2010-01-04' and DATE '2017-12-08'")
    print(f"{len(d['day'])} earnings jumps of 5%+ in small stocks, 2010-2017")
    found = []
    grid = itertools.product(READS, JUMPS, VOLUMES, CLOSES, CAPS, PRICES)
    for read, jump, volume, closed, cap, price in grid:
        keep = pick(d, read, jump, volume, closed, cap, price)
        if keep.sum() < 300:
            continue
        for h in HOLDS:
            net = d[f"g{h}"][keep] - d["cost"][keep]
            _, t, weeks = weekly(net, d["week"][keep])
            found.append((t, net.mean(), int(keep.sum()), weeks, read, jump, volume, closed, cap,
                          price, h))  # fmt: skip
    eligible = [f for f in found if f[1] >= 0.02]
    print(f"{len(found)} cells with 300+ trades (of 1,944); {len(eligible)} with a mean of 2%+")
    print("     t   mean  trades weeks  read  jump volume closed    cap price hold")
    for f in sorted(eligible, reverse=True)[:25]:
        t, mean, n, weeks, read, jump, volume, closed, cap, price, h = f
        print(f"{t:6.2f} {100 * mean:5.2f}% {n:7d} {weeks:5d}  {read:4}  {100 * jump:3.0f}% "
              f"{volume:5.0f}x {closed:6.1f} {cap:>6} ${price:3.0f} {h:4d}")  # fmt: skip


def test(read, jump, volume, closed, cap, price, hold, period, label) -> None:
    d = rows(period)
    keep = pick(d, read, jump, volume, closed, cap, price)
    g, cost, cost2 = d[f"g{hold}"][keep], d["cost"][keep], d["cost2"][keep]
    weeks, years = d["week"][keep], d["yr"][keep]
    net = g - cost
    mean, t, n_weeks = weekly(net, weeks)
    xm, xt, _ = weekly(g - d[f"mk{hold}"][keep], weeks)
    print(f"{label}: {keep.sum()} trades in {n_weeks} weeks")
    print(f"  gross {100 * g.mean():.2f}%  auction basis {100 * net.mean():.2f}%  "
          f"spread crossed twice over {100 * (g - cost2).mean():.2f}%  "
          f"over all stocks {100 * (g - d[f'mk{hold}'][keep]).mean():.2f}%")  # fmt: skip
    print(f"  weekly: mean {100 * mean:.2f}%, t {t:.2f}; over all stocks t {xt:.2f}; "
          f"winners {100 * (net > 0).mean():.0f}%; median {100 * np.median(net):.2f}%; "
          f"stopped trading {100 * d[f'gone{hold}'][keep].mean():.1f}%")  # fmt: skip
    for y in sorted(set(years)):
        m = years == y
        print(f"  {y}: {m.sum():5d} trades  auction basis {100 * net[m].mean():6.2f}%  "
              f"gross {100 * g[m].mean():6.2f}%  winners {100 * (net[m] > 0).mean():3.0f}%")  # fmt: skip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=("choose", "test", "old", "check"))
    parser.add_argument("cell", nargs="*")
    a = parser.parse_args()
    if a.what == "choose":
        choose()
        return
    read, jump, volume, closed, cap, price, hold = a.cell
    periods = {
        "old": ("d.day between DATE '2010-01-04' and DATE '2017-12-08'", "2010-2017 (chosen on)"),
        "test": ("d.day between DATE '2018-01-02' and DATE '2022-11-30'", "2018-2022 (test)"),
        "check": ("d.day between DATE '2023-01-03' and DATE '2023-10-13'", "2023 (check)"),
    }
    period, label = periods[a.what]
    test(read, float(jump), float(volume), float(closed), cap, float(price), int(hold),
         period, label)  # fmt: skip


if __name__ == "__main__":
    sys.exit(main())
