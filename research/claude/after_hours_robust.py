"""strategies/after_hours/HYPOTHESIS.md, addendum "how robust is the short to the fill, and how
crowded is it".

    cd research/claude
    uv run python after_hours_robust.py lows5 2005 2023
    uv run python after_hours_robust.py read
"""

from __future__ import annotations

import sys
from collections import defaultdict

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_earnings import weekly

import after_hours as ah
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

SPANS = {"2005-2009": (2005, 2009), "2010-2017": (2010, 2017), "2018-2022": (2018, 2022), "2023": (2023, 2023)}


def lows5(first: int, last: int) -> None:
    """The lowest price of the five minutes from the entry minute, for the short's events."""
    store = DataStore(load_settings())
    out = ah.folder()
    d = ah.load_short()
    keep = np.zeros(len(d["day"]), bool)
    for period in ("early", "search", "late", "check"):
        keep |= ah.pick(d, "after", "mid", "down15", period, ah.SHORT_REACTIONS)
    events = {(r["day"], r["symbol"]): r["minute"] for r in pq.read_table(out / "events.parquet").to_pylist() if r["timing"] == "after"}
    entries = duckdb.sql(f"select day, symbol from read_parquet('{out}/entries_*.parquet') where timing = 'after'").fetchall()
    wanted = {(day, sym) for day, sym in entries}
    days = set(d["day"][keep].astype(object))
    by_day = defaultdict(list)
    for day, sym in wanted:
        if day in days and first <= day.year <= last:
            by_day[day].append(sym)
    found = []
    for day, symbols in sorted(by_day.items()):
        bars = store.minute(day, symbols=symbols, columns="symbol, minute_et, low, close")
        sym = bars.column("symbol").to_pylist()
        cols = {n: bars.column(n).to_numpy(zero_copy_only=False) for n in ("minute_et", "low", "close")}
        where: dict = {}
        for i, s in enumerate(sym):
            where.setdefault(s, [i, i])[1] = i
        for s in symbols:
            if s not in where:
                continue
            a, b = where[s]
            minute, low, price = (cols[n][a : b + 1].astype(float) for n in ("minute_et", "low", "close"))
            regular = np.flatnonzero((minute >= ah.OPEN) & (minute <= ah.CLOSE))
            if not len(regular):
                continue
            at = min(max(events[(day, s)] + 30, 990), 1170)
            e = int(np.searchsorted(minute, at))
            if e >= len(minute):
                continue
            span = (minute >= minute[e]) & (minute <= minute[e] + 4)
            found.append({"day": day, "symbol": s, "rel_low5": float(low[span].min() / price[regular[-1]])})
    pq.write_table(pa.Table.from_pylist(found, schema=pa.schema([("day", pa.date32()), ("symbol", pa.string()), ("rel_low5", pa.float64())])),
                   out / "lows5_short.parquet")  # fmt: skip
    print(len(found), "events")


def read() -> None:
    out = ah.folder()
    t = duckdb.sql(
        f"""select n.day, n.symbol, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week,
                   v.mcap, n.reaction, n.bar_dollars, w.rel_low, f.rel_low5,
                   exp(v.c_next - v.c) * v.oc_next as to_open,
                   case when v.adv < 1e6 then 0.0025 when v.adv < 1e7 then 0.0010
                        when v.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / n.paid)) + {ah.BORROW_NIGHT} as cost
            from read_parquet('{out}/entries_*.parquet') n
            join read_parquet('{out}/lows_*.parquet') w on w.day = n.day and w.symbol = n.symbol
            join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
            left join '{out}/lows5_short.parquet' f on f.day = n.day and f.symbol = n.symbol
            where n.timing = 'after' and v.mcap >= 3e8 and v.mcap < 2e9 and n.reaction < -0.15"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    plain = 1 - d["to_open"] / d["rel_low"] - d["cost"]
    harsh = 1 - d["to_open"] / d["rel_low5"].astype(float) - d["cost"]
    variants = {"plain": (plain, np.ones(len(plain), bool)), "entry minute $5,000+": (plain, d["bar_dollars"] >= 5000),
                "worst of five minutes": (harsh, ~np.isnan(harsh))}  # fmt: skip
    for name, (values, ok) in variants.items():
        cells = []
        for span, (a, b) in SPANS.items():
            k = ok & (d["yr"] >= a) & (d["yr"] <= b)
            _, tt, _ = weekly(values[k], d["week"][k])
            cells.append(f"{span} {100 * values[k].mean():5.2f}% ({k.sum()}, t {tt:4.2f})")
        print(f"{name:22} " + "  ".join(cells))
    swing = load_settings().data_dir / "research" / "swing"
    crowd = duckdb.sql(
        f"""with s as (select day, symbol from (select unnest(?::date[]) as day, unnest(?::varchar[]) as symbol)
                       where day >= DATE '2018-01-12'),
            w as (select day, symbol, short_share, days_to_cover from read_parquet('{swing}/wide_*.parquet')
                  where day >= DATE '2018-01-12' and day <= DATE '2023-10-13' and mcap >= 3e8 and mcap < 2e9)
            select median(w.short_share) filter (where s.symbol is not null), median(w.days_to_cover) filter (where s.symbol is not null),
                   quantile_cont(w.short_share, 0.9) filter (where s.symbol is not null),
                   median(w.short_share), median(w.days_to_cover), quantile_cont(w.short_share, 0.9),
                   count(*) filter (where s.symbol is not null)
            from w left join s on s.day = w.day and s.symbol = w.symbol""",
        params=[list(d["day"].astype(object)), list(d["symbol"])],
    ).fetchall()[0]
    print(f"short interest at the last report before the signal, 2018-2023 ({crowd[6]} signals): "
          f"median {100 * crowd[0]:.1f}% of shares, {crowd[1]:.1f} days to cover, 90th percentile {100 * crowd[2]:.1f}%; "
          f"all stocks of $300M-$2B: median {100 * crowd[3]:.1f}%, {crowd[4]:.1f} days, 90th percentile {100 * crowd[5]:.1f}%")





def before_lows(first: int, last: int) -> None:
    """For results filed before the open: the low of the entry minute against the previous
    close, and the session's close against the previous close."""
    store = DataStore(load_settings())
    out = ah.folder()
    rows = [r for r in pq.read_table(out / "events.parquet").to_pylist() if r["timing"] == "before"]
    entries = set(duckdb.sql(
        f"select day, symbol from read_parquet('{out}/entries_*.parquet') where timing = 'before'").fetchall())  # fmt: skip
    by_day = defaultdict(list)
    for r in rows:
        if (r["day"], r["symbol"]) in entries and first <= r["day"].year <= last:
            by_day[r["day"]].append(r)
    found = []
    for day, items in sorted(by_day.items()):
        bars = store.minute(day, symbols=[r["symbol"] for r in items], columns="symbol, minute_et, low, close")
        sym = bars.column("symbol").to_pylist()
        cols = {n: bars.column(n).to_numpy(zero_copy_only=False) for n in ("minute_et", "low", "close")}
        where: dict = {}
        for i, s in enumerate(sym):
            where.setdefault(s, [i, i])[1] = i
        for r in items:
            if r["symbol"] not in where:
                continue
            a, b = where[r["symbol"]]
            minute, low, price = (cols[n][a : b + 1].astype(float) for n in ("minute_et", "low", "close"))
            regular = np.flatnonzero((minute >= ah.OPEN) & (minute <= ah.CLOSE))
            if not len(regular):
                continue
            last_price = price[regular[-1]]
            prev = last_price / float(np.exp(r["c"] - r["c_prev"]))
            e = int(np.searchsorted(minute, 540))
            if e >= len(minute) or minute[e] >= ah.OPEN or minute[e] > 560:
                continue
            found.append({"day": day, "symbol": r["symbol"], "low_rel": float(low[e] / prev), "close_rel": float(last_price / prev)})
    schema = pa.schema([("day", pa.date32()), ("symbol", pa.string()), ("low_rel", pa.float64()), ("close_rel", pa.float64())])
    pq.write_table(pa.Table.from_pylist(found, schema=schema), out / "before_lows.parquet")
    print(len(found), "events")


def before_search(*periods) -> None:
    out = ah.folder()
    t = duckdb.sql(
        f"""select n.day, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week, v.mcap,
                   n.reaction, 1 - b.close_rel / b.low_rel as g,
                   case when v.adv < 1e6 then 0.0025 when v.adv < 1e7 then 0.0010
                        when v.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / n.paid)) + {ah.BORROW_NIGHT} as cost
            from read_parquet('{out}/entries_*.parquet') n
            join '{out}/before_lows.parquet' b on b.day = n.day and b.symbol = n.symbol
            join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
            where n.timing = 'before' and n.reaction <= -0.15"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    net = d["g"] - d["cost"]
    for size, (lo, hi) in ah.SIZES.items():
        for period in periods:
            a, b = ah.PERIODS[period]
            k = (d["mcap"] >= lo) & (d["mcap"] < hi) & (d["yr"] >= a) & (d["yr"] <= b)
            if k.sum() < 3:
                print(f"before short {size} {period}: {k.sum()}")
                continue
            _, tt, _ = weekly(net[k], d["week"][k])
            years = d["yr"][k]
            pos = sum(net[k][years == y].mean() > 0 for y in set(years))
            print(f"before short {size:5} {period:6} {k.sum():>4} trades  net {100 * net[k].mean():6.2f}%  median "
                  f"{100 * np.median(net[k]):6.2f}%  t {tt:5.2f}  yrs {pos} of {len(set(years))}  worst {100 * net[k].min():.0f}%")  # fmt: skip


def exits() -> None:
    """The short bought back at the next open, 10:00, 15:30 and the close."""
    out = ah.folder()
    shape = load_settings().data_dir / "research" / "intraday_shape"
    store = DataStore(load_settings())
    t = duckdb.sql(
        f"""with n as (
                select n.day, n.symbol, year(n.day) as yr, (date_diff('day', DATE '2003-12-29', n.day) // 7) as week,
                       v.mcap, v.adv, n.reaction, n.paid, w.rel_low, exp(v.c_next - v.c) * v.oc_next as to_open,
                       exp(v.c_next - v.c) as to_close
                from read_parquet('{out}/entries_*.parquet') n
                join read_parquet('{out}/lows_*.parquet') w on w.day = n.day and w.symbol = n.symbol
                join '{out}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
                where n.timing = 'after' and v.mcap >= 3e8 and v.mcap < 2e9 and n.reaction < -0.15),
            nx as (select n.*, (select min(date) from read_parquet('{store.root}/panel/*.parquet') p
                                where p.symbol = n.symbol and p.date > n.day) as next_day from n)
            select nx.*, g.p1000, g.p1530, p.open as next_open
            from nx left join read_parquet('{shape}/segments_*.parquet') g on g.symbol = nx.symbol and g.day = nx.next_day
            left join read_parquet('{store.root}/panel/*.parquet') p on p.symbol = nx.symbol and p.date = nx.next_day"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    adv = d["adv"].astype(float)
    tier = np.where(adv < 1e6, 0.0025, np.where(adv < 1e7, 0.0010, np.where(adv < 1e8, 0.0005, 0.0002)))
    half = np.where(adv < 1e6, 0.0065, np.where(adv < 1e7, 0.0018, np.where(adv < 1e8, 0.0010, 0.0005)))
    comm = 2 * np.minimum(0.01, np.maximum(0.000175, 0.0035 / d["paid"].astype(float))) + ah.BORROW_NIGHT
    entry = d["rel_low"].astype(float)
    scale = d["to_open"].astype(float) / d["next_open"].astype(float)  # prices of the next session, against the reading's base
    rows = {
        "open": 1 - d["to_open"].astype(float) / entry - tier - comm,
        "10:00": 1 - d["p1000"].astype(float) * scale / entry - half - comm,
        "15:30": 1 - d["p1530"].astype(float) * scale / entry - half - comm,
        "close": 1 - d["to_close"].astype(float) / entry - tier - comm,
    }
    ok = ~np.isnan(rows["10:00"]) & ~np.isnan(rows["15:30"])
    for name, values in rows.items():
        cells = []
        for span, (a, b) in SPANS.items():
            k = ok & (d["yr"] >= a) & (d["yr"] <= b)
            _, tt, _ = weekly(values[k], d["week"][k])
            cells.append(f"{span} {100 * values[k].mean():5.2f}% ({k.sum()}, t {tt:4.2f})")
        print(f"bought back at {name:6} " + "  ".join(cells))


if __name__ == "__main__":
    if sys.argv[1] == "lows5":
        lows5(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "before_lows":
        before_lows(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "exits":
        exits()
    elif sys.argv[1] == "before_search":
        before_search(*sys.argv[2:])
    else:
        read()
