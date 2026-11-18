"""strategies/overnight_hold/HYPOTHESIS.md: hold only at night (closing auction to opening
auction) the stocks whose gains have come at night, or only by day the ones whose gains have
come in the session.

    cd research/claude
    uv run python night_bids.py filings        # results nights, shared
    uv run python overnight_hold.py table
    uv run python overnight_hold.py search
    uv run python overnight_hold.py test night 20 large
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from night_bids import folder as shared

SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
BOOK = 10
COST = """2 * (least(0.01, greatest(0.000175, 0.0035 / close))
               + case when adv < 1e6 then 0.0025 when adv < 1e7 then 0.0010
                      when adv < 1e8 then 0.0005 else 0.0002 end)"""


def folder():
    out = load_settings().data_dir / "research" / "overnight_hold"
    out.mkdir(parents=True, exist_ok=True)
    return out


def connect():
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    return con


def table() -> None:
    store = DataStore(load_settings())
    connect().execute(
        f"""copy (
            with q as (
                select permaticker, date, category, open, close, adv20_prev as adv, marketcap_prev as mcap,
                       ln(open / prev_close) as n, ln(close / open) as d,
                       coalesce(date - prev_date <= 5, false) as fresh
                from read_parquet('{store.root}/panel/*.parquet')
                where date <= DATE '2023-11-08' and prev_close > 0 and open > 0 and close > 0),
            r as (
                select *, sum(n) over (w rows 19 preceding) as n20, sum(n) over (w rows 59 preceding) as n60,
                       sum(d) over (w rows 19 preceding) as d20, sum(d) over (w rows 59 preceding) as d60,
                       count(*) over (w rows 59 preceding) as h60, bool_and(fresh) over (w rows 59 preceding) as steady,
                       lead(exp(n)) over w as next_night, lead(exp(d)) over w as next_day,
                       lead(fresh) over w as next_fresh
                from q window w as (partition by permaticker order by date))
            select date as day, permaticker, mcap, adv, close, n20, n60, d20, d60,
                   next_night - 1 as night, next_day - 1 as session, {COST} as cost
            from r
            where date between DATE '2005-01-03' and DATE '2023-10-13' and category like '%Common Stock%'
              and mcap >= 5e7 and adv >= 250000 and close >= 5 and fresh and next_fresh and steady and h60 = 60
              and next_night between 0.5 and 1.5 and next_day between 0.5 and 1.5
              and not exists (select 1 from '{shared()}/results_due.parquet' x
                              where x.permaticker = r.permaticker and x.day = r.date)
        ) to '{folder()}/stocks.parquet' (format parquet)"""
    )
    print(duckdb.sql(f"select count(*), min(day), max(day) from '{folder()}/stocks.parquet'").fetchall())


def books(score: str, ret: str, size: str) -> dict[str, np.ndarray]:
    """The book's return each session: the top BOOK stocks by score in the size group."""
    small, big = SIZES[size]
    t = duckdb.sql(
        f"""with s as (
                select day, {ret} - cost as net, {ret} as gross,
                       row_number() over (partition by day order by {score} desc) as rk
                from '{folder()}/stocks.parquet' where mcap >= {small} and mcap < {big})
            select day, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week,
                   avg(net) as net, avg(gross) as gross, count(*) as n
            from s where rk <= {BOOK} group by day order by day"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def measure(b, keep) -> dict:
    net = b["net"][keep].astype(float)
    if len(net) < 3:
        return {"n": len(net)}
    _, t, _ = weekly(net, b["week"][keep])
    years = b["yr"][keep]
    wealth = np.cumsum(np.log1p(net))
    drawdown = float(np.exp((wealth - np.maximum.accumulate(wealth)).min()) - 1)
    yearly = {int(y): float(np.expm1(np.log1p(net[years == y]).sum())) for y in sorted(set(years))}
    return {"n": len(net), "net": net.mean(), "gross": b["gross"][keep].mean(), "t": t,
            "pos": sum(v > 0 for v in yearly.values()), "years": len(yearly), "dd": drawdown, "yearly": yearly}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:20} {m['n']}"
    return (f"{label:20} {m['n']:>5} sessions  gross {100 * m['gross']:>6.3f}%  net {100 * m['net']:>6.3f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  worst drawdown {100 * m['dd']:>4.0f}%")  # fmt: skip


CELLS = {("night", w): (f"n{w}", "night") for w in (20, 60)} | {("day", w): (f"d{w}", "session") for w in (20, 60)}


def period(b, name):
    first, last = PERIODS[name]
    return (b["yr"] >= first) & (b["yr"] <= last)


def search() -> None:
    passed = []
    for (book, window), (score, ret) in CELLS.items():
        for size in SIZES:
            b = books(score, ret, size)
            m = measure(b, period(b, "search"))
            label = f"{book} {window} {size}"
            print(show(label, m))
            if m["n"] >= 3 and m["net"] >= 0.0008 and m["t"] >= 3 and m["pos"] >= 6:
                passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(book, window, size) -> None:
    score, ret = CELLS[(book, int(window))]
    b = books(score, ret, size)
    for name in ("early", "late"):
        m = measure(b, period(b, name))
        print(show(f"{book} {window} {size} {name}", m))
        print("    " + "  ".join(f"{y} {100 * v:.1f}%" for y, v in m["yearly"].items()))


def picks() -> None:
    """Every stock in a night book (both windows, every size), with the raw prices needed to
    price it again from minute bars."""
    store = DataStore(load_settings())
    sizes = " ".join(f"when mcap >= {lo} and mcap < {hi} then '{name}'" for name, (lo, hi) in SIZES.items())
    connect().execute(
        f"""copy (
            with s as (select *, case {sizes} end as size from '{folder()}/stocks.parquet'),
            r as (select *, row_number() over (partition by day, size order by n20 desc) as r20,
                            row_number() over (partition by day, size order by n60 desc) as r60 from s),
            k as (select * from r where r20 <= {BOOK} or r60 <= {BOOK}),
            p as (select permaticker, date, symbol, open, close,
                         lead(date) over w as next_date, lead(symbol) over w as next_symbol, lead(open) over w as next_open
                  from read_parquet('{store.root}/panel/*.parquet')
                  where date <= DATE '2023-11-08' window w as (partition by permaticker order by date))
            select k.day, k.permaticker, k.size, k.r20 <= {BOOK} as in20, k.r60 <= {BOOK} as in60, k.night, k.close as price,
                   p.symbol, p.close as raw_close, p.next_date, p.next_symbol, p.next_open
            from k join p on p.permaticker = k.permaticker and p.date = k.day
        ) to '{folder()}/picks.parquet' (format parquet)"""
    )
    print(duckdb.sql(f"select count(*), count(distinct day) from '{folder()}/picks.parquet'").fetchall())


def minutes(first: int, last: int) -> None:
    """The closing prints of D and the first regular minute of D+1 for every pick."""
    store = DataStore(load_settings())
    con = connect()
    for year in range(first, last + 1):
        target = folder() / f"prints_{year}.parquet"
        if target.exists():
            continue
        files = str(store.bars_roots[0] / "minute" / f"year={year}" / "*.parquet")
        con.execute(
            f"""copy (
                with need as (
                    select day as date, symbol from '{folder()}/picks.parquet' where year(day) = {year}
                    union select next_date, next_symbol from '{folder()}/picks.parquet' where year(next_date) = {year}),
                b as (select symbol, cast(regexp_extract(filename, '(\\d{{4}}-\\d{{2}}-\\d{{2}})\\.parquet', 1) as date) as date,
                             minute_et, open, high, low, close, volume
                      from read_parquet('{files}', filename = true)
                      where minute_et = 570 or minute_et between 960 and 965)
                select b.date, b.symbol,
                       min(low) filter (where minute_et >= 960) as close_low, max(high) filter (where minute_et >= 960) as close_high,
                       sum(close * volume) filter (where minute_et >= 960) as close_dollars,
                       min(low) filter (where minute_et = 570) as open_low, max(open) filter (where minute_et = 570) as open_first,
                       sum(close * volume) filter (where minute_et = 570) as open_dollars
                from b join need n on n.date = b.date and n.symbol = b.symbol group by 1, 2
            ) to '{target}' (format parquet)"""
        )
        print(year, con.sql(f"select count(*) from '{target}'").fetchall()[0][0], flush=True)


REPRICE_COST = "2 * greatest(0.000175, 0.0045 / price)"


def repriced(window: int, size: str) -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""with k as (
                select k.day, k.night, k.price,
                       (1 + k.night) * c2.open_low / k.next_open - 1 as night_low,
                       c1.close_low <= k.raw_close and k.raw_close <= c1.close_high and c1.close_dollars >= 100000 as closed,
                       c2.open_dollars >= 50000 as opened
                from '{folder()}/picks.parquet' k
                left join read_parquet('{folder()}/prints_*.parquet') c1 on c1.date = k.day and c1.symbol = k.symbol
                left join read_parquet('{folder()}/prints_*.parquet') c2 on c2.date = k.next_date and c2.symbol = k.next_symbol
                where k.in{window} and k.size = '{size}')
            select day, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week,
                   avg(night_low - {REPRICE_COST}) as net, avg(night_low) as gross, avg(night) as official,
                   count(*) as n, avg(opened::int) as opened
            from k where closed and night_low is not null group by day order by day"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def crossed(window: int, size: str) -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""with k as (
                select k.day, k.night, k.price
                from '{folder()}/picks.parquet' k
                join read_parquet('{folder()}/prints_*.parquet') c1 on c1.date = k.day and c1.symbol = k.symbol
                join read_parquet('{folder()}/prints_*.parquet') c2 on c2.date = k.next_date and c2.symbol = k.next_symbol
                where k.in{window} and k.size = '{size}'
                  and k.raw_close between c1.close_low and c1.close_high
                  and abs(c2.open_first / k.next_open - 1) <= 0.002)
            select day, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week,
                   avg(night - {REPRICE_COST}) as net, avg(night) as gross, avg(night) as official,
                   count(*) as n, 1.0 as opened
            from k group by day order by day"""
    ).to_arrow_table()
    return {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}


def crossed_test(window, size) -> None:
    b = crossed(int(window), size)
    for name in ("early", "late"):
        m = measure(b, period(b, name))
        print(show(f"night {window} {size} {name}", m) + f"  stocks a night {b['n'][period(b, name)].mean():.1f}")
        print("    " + "  ".join(f"{y} {100 * v:.1f}%" for y, v in m["yearly"].items()))


def reprice(*periods, source=repriced) -> None:
    passed = []
    for window in (20, 60):
        for size in SIZES:
            b = source(window, size)
            for name in periods:
                keep = period(b, name)
                m = measure(b, keep)
                extra = (f"  official open {100 * b['official'][keep].mean():.3f}%  stocks a night {b['n'][keep].mean():.1f}"
                         f"  first minute $50k+ {100 * b['opened'][keep].mean():.0f}%")  # fmt: skip
                label = f"night {window} {size} {name}"
                print(show(label, m) + extra)
                if name != "search":
                    print("    " + "  ".join(f"{y} {100 * v:.1f}%" for y, v in m["yearly"].items()))
                elif m["n"] >= 3 and m["net"] >= 0.0008 and m["t"] >= 3 and m["pos"] >= 6:
                    passed.append(label)
    if passed:
        print("\nMeet the search bar:", passed)


if __name__ == "__main__":
    if sys.argv[1] == "picks":
        picks()
    elif sys.argv[1] == "minutes":
        minutes(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "reprice":
        reprice(*sys.argv[2:])
    elif sys.argv[1] == "crossed_test":
        crossed_test(*sys.argv[2:4])
    elif sys.argv[1] == "crossed":
        reprice(*sys.argv[2:], source=crossed)
    elif sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
