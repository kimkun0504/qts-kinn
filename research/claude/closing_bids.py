"""strategies/closing_bids/HYPOTHESIS.md: a limit-on-close buy order under the 15:49 price,
sold at the next open or close.

    cd research/claude
    uv run python night_bids.py daily      # the daily table and results nights are shared
    uv run python night_bids.py filings
    uv run python closing_bids.py collect 2005 2023
    uv run python closing_bids.py search
    uv run python closing_bids.py test 3 mid open
"""

from __future__ import annotations

import sys

import duckdb
import numpy as np
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from night_bids import PERIODS, SIZES, connect, pick
from night_bids import folder as shared

DEPTHS = (2, 3, 5)
EXITS = ("open", "close")
MIN_AUCTION = 50000.0


def folder():
    out = load_settings().data_dir / "research" / "closing_bids"
    out.mkdir(parents=True, exist_ok=True)
    return out


def collect(first: int, last: int) -> None:
    """Every stock-day whose official close is 2% or more under its 15:49 price."""
    store = DataStore(load_settings())
    con = connect()
    for year in range(first, last + 1):
        target = folder() / f"falls3_{year}.parquet"
        if target.exists():
            continue
        files = str(store.bars_roots[0] / "minute" / f"year={year}" / "*.parquet")
        con.execute(
            f"""copy (
                with b as (
                    select symbol, cast(regexp_extract(filename, '(\\d{{4}}-\\d{{2}}-\\d{{2}})\\.parquet', 1) as date) as day,
                           arg_max(close, minute_et) filter (where minute_et between 940 and 949) as before,
                           sum(close * volume) filter (where minute_et between 960 and 965) as auction,
                           min(low) filter (where minute_et between 960 and 965) as print_low,
                           max(high) filter (where minute_et between 960 and 965) as print_high,
                           arg_max(close, minute_et) filter (where minute_et between 955 and 959) as last,
                           arg_min(high, minute_et) filter (where minute_et between 966 and 980) as later
                    from read_parquet('{files}', filename = true)
                    where minute_et between 940 and 980 group by 1, 2)
                select b.day, b.symbol, d.permaticker, d.ref, d.mcap, d.adv, d.to_open, d.to_close,
                       b.before, b.auction, d.ref / b.before - 1 as late, b.print_low, b.print_high,
                       b.last, b.later
                from b join '{shared()}/daily.parquet' d on d.day = b.day and d.symbol = b.symbol
                where b.before is not null and d.ref <= b.before * 0.98
            ) to '{target}' (format parquet)"""
        )
        print(year, con.sql(f"select count(*) from '{target}'").fetchall()[0][0], flush=True)


def load(depth: int) -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""select f.day, f.symbol, year(f.day) as yr, (date_diff('day', DATE '2003-12-29', f.day) // 7) as week,
                   f.mcap, f.late, f.last / f.ref - 1 as last_gap, f.later / f.ref - 1 as later_gap,
                   f.to_open - 1 as g_open, f.to_close - 1 as g_close,
                   2 * (case when f.adv < 1e6 then 0.0025 when f.adv < 1e7 then 0.0010
                             when f.adv < 1e8 then 0.0005 else 0.0002 end)
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / f.ref)) as cost
            from read_parquet('{folder()}/falls3_*.parquet') f
            where f.late <= {-depth / 100} and f.late >= -0.30 and f.auction >= {MIN_AUCTION}
              and f.ref between f.print_low and f.print_high
              and not exists (select 1 from '{shared()}/results_due.parquet' r
                              where r.permaticker = f.permaticker and r.day = f.day)
            order by f.day, f.symbol"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def followups() -> None:
    """The two cells of the addendum, by period: bought after the close, and hedged with SPY."""
    store = DataStore(load_settings())
    spy = duckdb.sql(
        f"""select date, lead(open) over (order by date) / close - 1 as r
            from read_parquet('{store.bars_roots[0]}/daily/*.parquet') where symbol = 'SPY'"""
    ).fetchall()
    market = {day: r for day, r in spy if r is not None}
    d = load(2)
    fund = np.array([market.get(day, np.nan) for day in d["day"].astype(object)])
    d["g_hedged"] = d["g_open"].astype(float) - fund - 0.0003
    d["g_later"] = (1 + d["g_open"].astype(float)) / (1 + d["later_gap"].astype(float)) - 1
    for period in ("search", "early", "late"):
        keep = pick(d, "large", period)
        print(show(f"auction {period}", measure(d, keep, "open")))
        print(show(f"hedged {period}", measure(d, keep & ~np.isnan(fund), "hedged")))
        after = keep & ~np.isnan(d["later_gap"].astype(float))
        print(show(f"after close {period}", measure(d, after, "later"))
              + f"  of {keep.sum()}; paid {100 * np.median(d['later_gap'][after].astype(float)):.2f}% over the close")
        days = d["day"][keep]
        counts = np.unique(days, return_counts=True)[1]
        print(f"    {len(counts)} days; {100 * counts[counts >= 10].sum() / max(1, len(days)):.0f}% of fills on days with 10 or more; "
              f"SPY overnight on those fills {100 * np.nanmean(fund[keep]):.2f}%; "
              f"15:59 price against the close {100 * np.nanmedian(d['last_gap'][keep].astype(float)):.2f}%")


def alone() -> None:
    """The addendum's three cells: the stock's late fall 2% or more under SPY's."""
    store = DataStore(load_settings())
    root = store.bars_roots[0]
    rows = duckdb.sql(
        f"""with b as (
                select cast(regexp_extract(filename, '(\\d{{4}}-\\d{{2}}-\\d{{2}})\\.parquet', 1) as date) as day,
                       arg_max(close, minute_et) as before
                from read_parquet('{root}/minute/year=*/*.parquet', filename = true)
                where symbol = 'SPY' and minute_et between 940 and 949 group by 1),
            d as (select date, close, lead(open) over (order by date) / close - 1 as night
                  from read_parquet('{root}/daily/*.parquet') where symbol = 'SPY')
            select b.day, d.close / b.before - 1 as late, d.night from b join d on d.date = b.day"""
    ).fetchall()
    fund_late = {day: late for day, late, _ in rows}
    fund_night = {day: night for day, _, night in rows if night is not None}
    t = duckdb.sql(
        f"""select f.day, f.symbol, year(f.day) as yr, (date_diff('day', DATE '2003-12-29', f.day) // 7) as week,
                   f.mcap, f.ref / f.before - 1 as late, f.later / f.ref - 1 as later_gap, f.to_open - 1 as g_open,
                   2 * (case when f.adv < 1e6 then 0.0025 when f.adv < 1e7 then 0.0010
                             when f.adv < 1e8 then 0.0005 else 0.0002 end)
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / f.ref)) as cost
            from read_parquet('{folder()}/falls3_*.parquet') f
            where f.late >= -0.30 and f.auction >= {MIN_AUCTION} and f.ref between f.print_low and f.print_high
              and f.mcap >= 2e9
              and not exists (select 1 from '{shared()}/results_due.parquet' r
                              where r.permaticker = f.permaticker and r.day = f.day)
            order by f.day, f.symbol"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    days = d["day"].astype(object)
    market = np.array([fund_late.get(day, np.nan) for day in days])
    night = np.array([fund_night.get(day, np.nan) for day in days])
    d["g_hedged"] = d["g_open"].astype(float) - night - 0.0003
    d["g_later"] = (1 + d["g_open"].astype(float)) / (1 + d["later_gap"].astype(float)) - 1
    picked = (d["late"] - market <= -0.02) & ~np.isnan(night)
    for period in ("search", "early", "late"):
        keep = picked & pick(d, "large", period)
        print(show(f"alone auction {period}", measure(d, keep, "open")))
        print(show(f"alone hedged {period}", measure(d, keep, "hedged")))
        after = keep & ~np.isnan(d["later_gap"].astype(float))
        print(show(f"alone after close {period}", measure(d, after, "later")) + f"  of {keep.sum()}")
        net = d["g_hedged"] - d["cost"]
        print("    hedged by year: " + "  ".join(f"{y} {100 * net[keep & (d['yr'] == y)].mean():.2f}% ({(keep & (d['yr'] == y)).sum()})"
                                                  for y in sorted(set(d["yr"][keep]))))


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
            "worst": ordered[0], "worst1": ordered[: max(1, n // 100)].mean(),
            "late": np.median(d["late"][keep])}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:22} {m['n']:>6}"
    return (f"{label:22} {m['n']:>6}  net {100 * m['net']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%  "
            f"worst {100 * m['worst']:>4.0f}%  worst 1% {100 * m['worst1']:>4.0f}%  "
            f"late fall {100 * m['late']:>5.1f}%")  # fmt: skip


def search() -> None:
    passed = []
    for depth in DEPTHS:
        d = load(depth)
        for size in SIZES:
            keep = pick(d, size, "search")
            for exit_ in EXITS:
                m = measure(d, keep, exit_)
                label = f"{depth}% {size} {exit_}"
                print(show(label, m))
                if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(depth, size, exit_) -> None:
    d = load(int(depth))
    net = d[f"g_{exit_}"].astype(float) - d["cost"]
    for period in ("early", "late"):
        keep = pick(d, size, period)
        print(show(f"{depth}% {size} {exit_} {period}", measure(d, keep, exit_)))
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


if __name__ == "__main__":
    if sys.argv[1] == "alone":
        alone()
    elif sys.argv[1] == "followups":
        followups()
    elif sys.argv[1] == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
