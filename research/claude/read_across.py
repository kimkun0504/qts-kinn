"""strategies/read_across/HYPOTHESIS.md: after a confirmed jump on results, buy the industry
peers that have not reported yet.

    cd research/claude
    uv run python read_across.py table
    uv run python read_across.py search
    uv run python read_across.py test all mid 10
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import weekly

from kinn.core.settings import load_settings

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
STATES = {"all": "true", "unmoved": "ret2 < 0.03"}
HOLDS = (5, 10, 15)
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
TRIGGER = "earn and ret2 >= 0.15 and dvr2 >= 5 and mcap >= 5e7"
COST = """2 * (case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                    when adv < 1e8 then 0.0005 else 0.0002 end)
          + 2 * least(0.01, greatest(0.000175, 0.0035 / close))"""


def base():
    return load_settings().data_dir / "research" / "swing"


def folder():
    out = load_settings().data_dir / "research" / "read_across"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    for name, market in (("wide", "market"), ("early", "market_early")):
        con.execute(
            f"""copy (
                with d as (select * from read_parquet('{base()}/{name}_*.parquet')),
                t as (select day, industry, count(*) as triggers from d where {TRIGGER} and industry is not null
                      group by 1, 2),
                c as (select d.*, t.triggers from d join t using (day, industry)
                      where not d.earn and not ({TRIGGER}) and d.esince between 40 and 75
                        and d.mcap >= 5e7 and d.next_open is not null and d.category like '%Common Stock%'),
                once as (select * from c
                         qualify coalesce(day - lag(day) over (partition by permaticker order by day), 999) > 20)
                select o.day, o.yr, o.symbol, o.permaticker, o.mcap, o.adv, o.ret2, o.triggers,
                       (date_diff('day', DATE '2003-12-29', o.day) // 7) as week,
                       {", ".join(f"exp(first_day + c_exit{h} - c_next) - 1 as g{h}, m.mk{h}" for h in HOLDS)},
                       {COST} as cost
                from once o left join '{base()}/{market}.parquet' m using (day)
                order by o.day, o.symbol
            ) to '{folder()}/peers_{name}.parquet' (format parquet)"""
        )
        print(name, con.sql(f"select count(*), min(day), max(day) from '{folder()}/peers_{name}.parquet'").fetchall())


def load(state: str) -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""select * from read_parquet('{folder()}/peers_*.parquet')
            where {STATES[state]} and day <= DATE '2023-10-13' order by day, symbol"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def pick(d, size, period):
    small, big = SIZES[size]
    first, last = PERIODS[period]
    return (d["mcap"] >= small) & (d["mcap"] < big) & (d["yr"] >= first) & (d["yr"] <= last)


def measure(d, keep, hold) -> dict:
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    gross = d[f"g{hold}"][keep].astype(float)
    net = gross - d["cost"][keep]
    _, t, _ = weekly(net, d["week"][keep])
    excess = gross - d[f"mk{hold}"][keep].astype(float)
    _, xt, _ = weekly(excess, d["week"][keep])
    years = d["yr"][keep]
    return {"n": n, "net": net.mean(), "median": np.median(net), "t": t, "wins": (net > 0).mean(),
            "pos": sum(net[years == y].mean() > 0 for y in set(years)), "years": len(set(years)),
            "excess": np.nanmean(excess), "xt": xt}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:26} {m['n']:>6}"
    return (f"{label:26} {m['n']:>6}  net {100 * m['net']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%  "
            f"over the average stock {100 * m['excess']:>6.2f}% (t {m['xt']:>5.2f})")  # fmt: skip


def search() -> None:
    passed = []
    for state in STATES:
        d = load(state)
        for size in SIZES:
            keep = pick(d, size, "search")
            for hold in HOLDS:
                m = measure(d, keep, hold)
                label = f"{state} {size} {hold}"
                print(show(label, m))
                if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(state, size, hold) -> None:
    d = load(state)
    net = d[f"g{hold}"].astype(float) - d["cost"]
    for period in ("early", "late"):
        keep = pick(d, size, period)
        print(show(f"{state} {size} {hold} {period}", measure(d, keep, int(hold))))
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
