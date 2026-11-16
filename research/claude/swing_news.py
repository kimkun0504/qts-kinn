"""Family 18 of the swing search: jumps on news in companies under $300M (addendum of
2026-11-16 in strategies/swing_search/HYPOTHESIS.md). Cells are chosen on signals of 2010 to
2017 and tested on 2005 to 2009 and 2018 to 2022.

    uv run python research/claude/swing_news.py tables          # once: 8-K tables for 2005-2009
    uv run python research/claude/swing_news.py choose
    uv run python research/claude/swing_news.py test earnings-next 0.15 5 0 15
"""

from __future__ import annotations

import itertools
import sys
import tempfile

import duckdb
import numpy as np

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import AUCTION, weekly

KINDS = ("earnings-same", "earnings-next", "other-8k", "other-filing", "no-filing")
JUMPS = (0.10, 0.15, 0.25)
VOLUMES = (2.0, 5.0, 10.0)
FLOORS = (0.0, 5e7)
HOLDS = (10, 15)
PERIODS = {
    "choose": ("wide", "d.day between DATE '2010-01-04' and DATE '2017-12-08'"),
    "early": ("early", "d.day between DATE '2005-01-03' and DATE '2009-12-08'"),
    "late": ("wide", "d.day between DATE '2018-01-02' and DATE '2022-11-30'"),
    "check": ("wide", "d.day between DATE '2023-01-03' and DATE '2023-10-13'"),
}


def tables() -> None:
    """Earnings days and 8-K days for 2005 to 2009, as swing_search.py prep does for 2010 on."""
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    panel = f"""(select p.date as day, p.permaticker, p.prev_date, s.ticker
                 from read_parquet('{store.root}/panel/*.parquet') p
                 join '{store.root}/master/security_master.parquet' s using (permaticker)
                 where p.date between DATE '2005-01-03' and DATE '2009-12-31')"""
    events = f"'{store.root}/sharadar/events.parquet'"
    duckdb.execute(
        f"""copy (select q.permaticker, q.day,
                         list_distinct(flatten(list(string_split(e.eventcodes, '|')))) as codes
                  from {panel} q join {events} e
                    on e.ticker = q.ticker and e.date >= q.prev_date and e.date < q.day
                  group by 1, 2) to '{base}/codes_early.parquet' (format parquet)"""
    )
    duckdb.execute(
        f"""copy (select distinct q.permaticker, q.day
                  from {panel} q join {events} e on e.ticker = q.ticker and e.date = q.day
                  where regexp_matches('|' || e.eventcodes || '|', '[|]22[|]')
        ) to '{base}/earn0_early.parquet' (format parquet)"""
    )
    for name in ("codes_early", "earn0_early"):
        print(name, duckdb.sql(f"select count(*) from '{base}/{name}.parquet'").fetchall())


def rows(period: str) -> dict[str, np.ndarray]:
    settings = load_settings()
    base = settings.data_dir / "research" / "swing"
    name, dates = PERIODS[period]
    tail = "_early" if name == "early" else ""
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    holds = ", ".join(f"exp(first_day + c_exit{h} - c_next) - 1 as g{h}, m.mk{h}" for h in HOLDS)
    table = con.sql(
        f"""select d.day::varchar as day, d.symbol, yr,
                   (date_diff('day', DATE '2003-12-29', d.day) // 7) as week,
                   case when e0.permaticker is not null then 0 when earn then 1
                        when k.permaticker is not null then 2
                        when filings_prev > 0 or filings_today > 0 then 3 else 4 end as kind,
                   ret1, ret2, dvr, dvr2, mcap, close, adv, {AUCTION} as cost,
                   2 * (half_spread + commission) as cost1, {holds}
            from read_parquet('{base}/{name}_*.parquet') d
            left join '{base}/market{tail}.parquet' m using (day)
            left join '{base}/earn0{tail}.parquet' e0 using (permaticker, day)
            left join '{base}/codes{tail}.parquet' k using (permaticker, day)
            where {dates} and next_open is not null and mcap < 3e8
              and (ret1 >= 0.10 or ret2 >= 0.10)"""
    ).to_arrow_table()
    d = {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}
    # Same-day earnings and days without an 8-K before them are read on the day's own move;
    # the kinds read the session after are read on the two-day move.
    own = np.isin(d["kind"], (0, 3, 4))
    d["jump"] = np.where(own, d["ret1"], d["ret2"])
    d["volume"] = np.where(own, d["dvr"], d["dvr2"])
    return d


def pick(d: dict, kind: str, jump: float, volume: float, floor: float) -> np.ndarray:
    return (
        (d["kind"] == KINDS.index(kind))
        & (d["jump"] >= jump)
        & (d["volume"] >= volume)
        & (d["mcap"] >= floor)
    )


def choose() -> None:
    d = rows("choose")
    print(f"{len(d['day'])} jumps of 10%+ in companies under $300M, 2010-2017")
    found = []
    for kind, jump, volume, floor, h in itertools.product(KINDS, JUMPS, VOLUMES, FLOORS, HOLDS):
        keep = pick(d, kind, jump, volume, floor)
        if keep.sum() < 300:
            continue
        net = d[f"g{h}"][keep] - d["cost"][keep]
        _, t, weeks = weekly(net, d["week"][keep])
        found.append((t, net.mean(), int(keep.sum()), weeks, kind, jump, volume, floor, h))
    eligible = sorted((f for f in found if f[1] >= 0.02 and f[0] >= 3), reverse=True)
    print(f"{len(found)} cells with 300+ trades (of 180); {len(eligible)} with 2%+ and t of 3+")
    print("     t   mean  trades weeks  kind            jump volume  floor hold")
    for t, mean, n, weeks, kind, jump, volume, floor, h in sorted(found, reverse=True)[:30]:
        mark = "*" if (t, mean, n, weeks, kind, jump, volume, floor, h) in eligible[:5] else " "
        print(f"{mark}{t:5.2f} {100 * mean:5.2f}% {n:7d} {weeks:5d}  {kind:14} {100 * jump:3.0f}% "
              f"{volume:5.0f}x ${floor / 1e6:3.0f}M {h:4d}")  # fmt: skip


def test(kind: str, jump: float, volume: float, floor: float, hold: int, periods) -> None:
    pooled_net, pooled_week = [], []
    for period in periods:
        d = rows(period)
        keep = pick(d, kind, jump, volume, floor)
        g, net = d[f"g{hold}"][keep], d[f"g{hold}"][keep] - d["cost"][keep]
        mean, t, weeks = weekly(net, d["week"][keep])
        print(f"{period}: {keep.sum()} trades in {weeks} weeks; gross {100 * g.mean():.2f}%  "
              f"auction basis {100 * net.mean():.2f}%  spread crossed "
              f"{100 * (g - d['cost1'][keep]).mean():.2f}%  weekly t {t:.2f}  "
              f"winners {100 * (net > 0).mean():.0f}%  median {100 * np.median(net):.2f}%")  # fmt: skip
        years = d["yr"][keep]
        print("   " + "  ".join(f"{y}: {100 * net[years == y].mean():.1f}% ({(years == y).sum()})"
                                for y in sorted(set(years))))  # fmt: skip
        pooled_net.append(net)
        pooled_week.append(d["week"][keep])
    if len(periods) > 1:
        net, week = np.concatenate(pooled_net), np.concatenate(pooled_week)
        mean, t, weeks = weekly(net, week)
        print(f"together: {len(net)} trades, mean {100 * net.mean():.2f}%, weekly t {t:.2f}")


if __name__ == "__main__":
    if sys.argv[1] == "tables":
        tables()
    elif sys.argv[1] == "choose":
        choose()
    else:
        kind, jump, volume, floor, hold = sys.argv[2:7]
        periods = sys.argv[7:] or ["early", "late"]
        test(kind, float(jump), float(volume), float(floor), int(hold), periods)
