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
        target = folder() / f"falls2_{year}.parquet"
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
                           arg_min(close, minute_et) filter (where minute_et between 966 and 980) as later
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
            from read_parquet('{folder()}/falls2_*.parquet') f
            where f.late <= {-depth / 100} and f.late >= -0.30 and f.auction >= {MIN_AUCTION}
              and f.ref between f.print_low and f.print_high
              and not exists (select 1 from '{shared()}/results_due.parquet' r
                              where r.permaticker = f.permaticker and r.day = f.day)
            order by f.day, f.symbol"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


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
    if sys.argv[1] == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
