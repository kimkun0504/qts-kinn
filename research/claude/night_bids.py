"""strategies/night_bids/HYPOTHESIS.md: a buy order resting below the official close in
after-hours trading, sold at the next open or close.

    cd research/claude
    uv run python night_bids.py daily
    uv run python night_bids.py filings
    uv run python night_bids.py collect 2005 2023
    uv run python night_bids.py search
    uv run python night_bids.py test 5 mid open
"""

from __future__ import annotations

import bisect
import sys
import tempfile

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_earnings import weekly

import sec_times
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

DEPTHS = (3, 5, 8)
SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
EXITS = ("open", "close")
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
FIRST, LAST = 965, 1199  # 16:05 to 19:59
MIN_TRADES, MIN_DOLLARS = 5, 5000.0


def folder():
    out = load_settings().data_dir / "research" / "night_bids"
    out.mkdir(parents=True, exist_ok=True)
    return out


def connect():
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    return con


def daily() -> None:
    """One row a stock a session in the universe: the official close and what the next
    session's open and close were against it (split-safe)."""
    store = DataStore(load_settings())
    connect().execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, close, adv20_prev as adv, marketcap_prev as mcap,
                       category, open / close as oc, sum(ln(close / prev_close)) over w as c
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                window w as (partition by permaticker order by date)),
            q as (select *, lead(c) over w as c_next, lead(oc) over w as oc_next, lead(date) over w as next_day
                  from p window w as (partition by permaticker order by date))
            select date as day, symbol, permaticker, close as ref, adv, mcap, next_day,
                   exp(c_next - c) * oc_next as to_open, exp(c_next - c) as to_close
            from q
            where date between DATE '2005-01-03' and DATE '2023-10-13' and c_next is not null
              and category like '%Common Stock%' and mcap >= 5e7 and adv >= 250000 and close >= 1
            qualify row_number() over (partition by symbol, date order by adv desc) = 1
        ) to '{folder()}/daily.parquet' (format parquet)"""
    )
    print(duckdb.sql(f"select count(*), min(day), max(day) from '{folder()}/daily.parquet'").fetchall())


def filings() -> None:
    """Per (stock, session): whether results were due that evening or the next morning, and
    every filing accepted from 16:00 on the session to 09:30 on the next (as minutes after
    midnight of the session; the next morning counts from 1440)."""
    stocks, days = sec_times.numbers(), sec_times.sessions()
    day_set = set(days)
    results, evening = set(), []
    for name in ("8k.jsonl.gz", "other_forms.jsonl.gz"):
        for row in sec_times.filings(name):
            if row["cik"] not in stocks:
                continue
            when = sec_times.accepted(row)
            if not when:
                continue
            day, minute = when
            if day in day_set and minute >= 570:
                session, at = day, minute
            else:  # before the open, or not a session: it belongs to the night of the session before
                i = bisect.bisect_left(days, day) - 1
                if i < 0:
                    continue
                session, at = days[i], 1440 + minute
            is_results = row["form"] == "8-K" and "2.02" in (row.get("items") or "").split(",")
            for permaticker in stocks[row["cik"]]:
                if is_results and at >= 720:
                    results.add((permaticker, session))
                if at >= 960:
                    evening.append((permaticker, session, at, row["form"]))
    out = folder()
    pq.write_table(pa.table({"permaticker": [r[0] for r in results], "day": [r[1] for r in results]}), out / "results_due.parquet")
    pq.write_table(pa.table({"permaticker": [r[0] for r in evening], "day": [r[1] for r in evening],
                             "at": [r[2] for r in evening], "form": [r[3] for r in evening]}), out / "evening_filings.parquet")  # fmt: skip
    print(len(results), "results nights;", len(evening), "filings between 16:00 and the next open")


def collect(first: int, last: int) -> None:
    store = DataStore(load_settings())
    out = folder()
    con = connect()
    depth_columns = ", ".join(
        f"""min(minute_et) filter (where minute_et >= {FIRST} and high < ref * {1 - x / 100}) as first_{x},
            sum(transactions) filter (where minute_et >= {FIRST} and high < ref * {1 - x / 100}) as trades_{x},
            sum(b.close * volume) filter (where minute_et >= {FIRST} and high < ref * {1 - x / 100}) as dollars_{x}"""
        for x in DEPTHS
    )
    for year in range(first, last + 1):
        target = out / f"fills_{year}.parquet"
        if target.exists():
            continue
        files = str(store.bars_roots[0] / "minute" / f"year={year}" / "*.parquet")
        con.execute(
            f"""copy (
                with b as (
                    select symbol, cast(regexp_extract(filename, '(\\d{{4}}-\\d{{2}}-\\d{{2}})\\.parquet', 1) as date) as day,
                           minute_et, high, close, volume, transactions
                    from read_parquet('{files}', filename = true)
                    where minute_et between 955 and {LAST})
                select b.day, b.symbol, any_value(d.permaticker) as permaticker, any_value(d.ref) as ref,
                       any_value(d.mcap) as mcap, any_value(d.adv) as adv,
                       any_value(d.to_open) as to_open, any_value(d.to_close) as to_close,
                       min(abs(b.close / ref - 1)) filter (where minute_et <= 960) as close_gap,
                       {depth_columns}
                from b join '{out}/daily.parquet' d on d.day = b.day and d.symbol = b.symbol
                group by b.day, b.symbol
                having dollars_{DEPTHS[0]} > 0
            ) to '{target}' (format parquet)"""
        )
        print(year, con.sql(f"select count(*) from '{target}'").fetchall()[0][0], flush=True)


def load(depth: int) -> dict[str, np.ndarray]:
    """The fills of one depth, with the plan's exclusions applied."""
    out = folder()
    x = depth
    table = duckdb.sql(
        f"""with f as (
                select *, first_{x} as fill_at from read_parquet('{out}/fills_*.parquet')
                where trades_{x} >= {MIN_TRADES} and dollars_{x} >= {MIN_DOLLARS} and close_gap <= 0.02),
            e as (select permaticker, day, min("at") as filed_at from '{out}/evening_filings.parquet' group by 1, 2),
            m as (select f.day, f.symbol, count(*) as later
                  from f join '{out}/evening_filings.parquet' g on g.permaticker = f.permaticker and g.day = f.day
                  where g."at" > f.fill_at group by 1, 2)
            select f.day, f.symbol, year(f.day) as yr, (date_diff('day', DATE '2003-12-29', f.day) // 7) as week,
                   f.mcap, f.fill_at, coalesce(m.later, 0) as later,
                   f.to_open / {1 - x / 100} - 1 as g_open, f.to_close / {1 - x / 100} - 1 as g_close,
                   case when f.adv < 1e6 then 0.0025 when f.adv < 1e7 then 0.0010
                        when f.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / (f.ref * {1 - x / 100}))) as cost
            from f
            left join e on e.permaticker = f.permaticker and e.day = f.day
            left join m on m.day = f.day and m.symbol = f.symbol
            where not exists (select 1 from '{out}/results_due.parquet' r
                              where r.permaticker = f.permaticker and r.day = f.day)
              and (e.filed_at is null or e.filed_at > f.fill_at)
            order by f.day, f.symbol"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


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
            "worst": ordered[0], "worst1": ordered[: max(1, n // 100)].mean(),
            "later": (d["later"][keep] > 0).mean()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:24} {m['n']:>6}"
    return (f"{label:24} {m['n']:>6}  net {100 * m['net']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%  "
            f"worst {100 * m['worst']:>4.0f}%  worst 1% {100 * m['worst1']:>4.0f}%  filed later {100 * m['later']:>3.0f}%")  # fmt: skip


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
    command = sys.argv[1]
    if command == "daily":
        daily()
    elif command == "filings":
        filings()
    elif command == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif command == "search":
        search()
    else:
        test(*sys.argv[2:5])
