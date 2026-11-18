"""strategies/before_report/HYPOTHESIS.md: buy five sessions before results, chosen by how
the stock reacted to the company's last reports.

    cd research/claude
    uv run python before_report.py table
    uv run python before_report.py search
    uv run python before_report.py test repeater small after
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
GROUPS = {"repeater": "last1 >= 0.10 and gap1 between 40 and 90",
          "streak": "last1 >= 0.05 and last2 >= 0.05 and gap1 between 40 and 90 and gap2 between 40 and 90",
          "all": "true"}  # fmt: skip
EXITS = ("before", "after")
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder():
    out = load_settings().data_dir / "research" / "before_report"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table(ahead: int = 5, name: str = "reports") -> None:
    settings = load_settings()
    store = DataStore(settings)
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, category, adv20_prev as adv, marketcap_prev as mcap, close,
                       sum(ln(close / prev_close)) over w as c, row_number() over w as rn
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0
                window w as (partition by permaticker order by date)),
            q as (select *, lag(c, {ahead}) over w as c_in, lag(c, 1) over w as c_before, lead(c, 1) over w as c_after,
                         lag(mcap, {ahead}) over w as mcap_in, lag(adv, {ahead}) over w as adv_in,
                         lag(close, {ahead}) over w as price_in, lag(date, {ahead}) over w as day_in
                  from p window w as (partition by permaticker order by date)),
            r as (select q.* from q join '{settings.data_dir}/research/swing/timed.parquet' t
                  on t.permaticker = q.permaticker and t.day = q.date),
            once as (select * from r qualify rn - coalesce(lag(rn) over (partition by permaticker order by rn), -999) >= 30),
            h as (select *, exp(c_after - c_before) - 1 as reaction,
                         lag(exp(c_after - c_before) - 1, 1) over w as last1,
                         lag(exp(c_after - c_before) - 1, 2) over w as last2,
                         rn - lag(rn, 1) over w as gap1, lag(rn, 1) over w - lag(rn, 2) over w as gap2
                  from once window w as (partition by permaticker order by rn))
            select date as day, day_in, symbol, permaticker, mcap_in as mcap, adv_in as adv, price_in,
                   last1, last2, gap1, gap2, reaction,
                   exp(c_before - c_in) - 1 as g_before, exp(c_after - c_in) - 1 as g_after
            from h
            where date between DATE '2005-01-03' and DATE '2023-10-13' and category like '%Common Stock%'
              and mcap_in >= 5e7 and adv_in >= 250000 and price_in >= 1 and c_after is not null and c_in is not null
        ) to '{folder()}/{name}.parquet' (format parquet)"""
    )
    print(con.sql(f"select count(*), count(last1), min(day), max(day) from '{folder()}/{name}.parquet'").fetchall())


def load(group: str, name: str = "reports") -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""select day, year(day) as yr, (date_diff('day', DATE '2003-12-29', day_in) // 7) as week, mcap,
                   g_before, g_after,
                   2 * (case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                             when adv < 1e8 then 0.0005 else 0.0002 end)
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / price_in)) as cost
            from '{folder()}/{name}.parquet' where {GROUPS[group]} order by day, symbol"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def pick(d, size, period):
    small, big = SIZES[size]
    first, last = PERIODS[period]
    return (d["mcap"] >= small) & (d["mcap"] < big) & (d["yr"] >= first) & (d["yr"] <= last)


def measure(d, keep, exit_) -> dict:
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    net = d[f"g_{exit_}"][keep].astype(float) - d["cost"][keep]
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    ordered = np.sort(net)
    return {"n": n, "net": net.mean(), "median": np.median(net), "t": t, "wins": (net > 0).mean(),
            "pos": sum(net[years == y].mean() > 0 for y in set(years)), "years": len(set(years)),
            "worst": ordered[0], "worst1": ordered[: max(1, n // 100)].mean()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:28} {m['n']:>6}"
    return (f"{label:28} {m['n']:>6}  net {100 * m['net']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%  "
            f"worst {100 * m['worst']:>4.0f}%  worst 1% {100 * m['worst1']:>4.0f}%")  # fmt: skip


def search(name: str = "reports") -> None:
    passed = []
    for group in GROUPS:
        d = load(group, name)
        for size in SIZES:
            keep = pick(d, size, "search")
            for exit_ in EXITS:
                m = measure(d, keep, exit_)
                label = f"{group} {size} {exit_}"
                print(show(label, m))
                if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(group, size, exit_, name: str = "reports") -> None:
    d = load(group, name)
    net = d[f"g_{exit_}"].astype(float) - d["cost"]
    for period in ("early", "late"):
        keep = pick(d, size, period)
        print(show(f"{group} {size} {exit_} {period}", measure(d, keep, exit_)))
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
