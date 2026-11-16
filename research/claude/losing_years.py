"""What the losing development years (2013-2015) of x_o4 have in common. Development period
only (2003-2016): nothing here reads a date after 2016-12-30. Reads the run store, the order
listing made for the fill check, and processed data; starts no run.

    uv run python research/claude/losing_years.py build   # trade table with context (resumable)
    uv run python research/claude/losing_years.py report
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

RUN = "20261115T232205Z_claude_rebound_limit_84ff9c3d"
END = date(2016, 12, 30)
OUT = Path.home() / "work" / "losing_years"
LOSING = (2013, 2014, 2015)


def build() -> None:
    s = load_settings()
    store = DataStore(s)
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    work = s.data_dir / "quotes_sample" / "fillcheck_x_o4" / "work" / RUN
    panel = f"read_parquet('{store.root}/panel/*.parquet')"
    con.execute(f"create table o as select * from read_parquet('{work}/*.parquet')")
    assert con.execute("select max(day) from o").fetchone()[0] <= END
    con.execute(
        f"""create table t as
            select t.*, o.limit_price, o.prev_close, o.adv20_prev, o.marketcap_prev,
                   m.sector, m.industry,
                   (select count(*) from o o2 where o2.day = t.day) as day_signals,
                   (select count(*) from o o2 where o2.day = t.day
                      and o2.signal_minute < t.signal_minute) as earlier_signals,
                   (select count(*) from o o2 where o2.day = t.day and o2.kind = 'filled')
                     as day_bar_fills
            from '{s.runs_dir}/{RUN}/trades.parquet' t
            join o on o.day = t.day and o.symbol = t.symbol
            left join '{store.root}/master/security_master.parquet' m
              on m.permaticker = t.permaticker"""
    )
    # The stock's own past: return over the 20 and 60 sessions before the event day, from the
    # panel's split-adjusted day-to-day returns; and the day's dollar volume against its norm.
    con.execute(
        f"""create table past as
            with r as (
                select permaticker, date, ln(close / prev_close) as lr, dollar_volume, adv20_prev
                from {panel}
                where date <= DATE '{END}' and prev_close > 0 and close > 0
                  and permaticker in (select distinct permaticker from t)),
            w as (
                select permaticker, date, dollar_volume / nullif(adv20_prev, 0) as volume_ratio,
                       sum(lr) over (partition by permaticker order by date
                                     rows between 20 preceding and 1 preceding) as lr20,
                       sum(lr) over (partition by permaticker order by date
                                     rows between 60 preceding and 1 preceding) as lr60
                from r)
            select * from w"""
    )
    con.execute(
        """create table tt as
           select t.*, exp(p.lr20) - 1 as ret20_before, exp(p.lr60) - 1 as ret60_before,
                  p.volume_ratio as day_volume_ratio
           from t left join past p on p.permaticker = t.permaticker and p.date = t.day"""
    )
    # The market: SPY's 20-day realised volatility before the day, and its return from the
    # previous close to the minute of the signal.
    spy = store.daily(date(2003, 9, 10), END, symbols=["SPY"]).to_pylist()
    days = [r["date"] for r in spy]
    close = np.array([r["close"] for r in spy], dtype=float)
    lr = np.r_[np.nan, np.diff(np.log(close))]
    vol20 = {d: float(np.std(lr[i - 20:i], ddof=1) * np.sqrt(252)) for i, d in enumerate(days)
             if i >= 21}  # fmt: skip
    prev = {d: close[i - 1] for i, d in enumerate(days) if i >= 1}
    ret20 = {d: float(close[i - 1] / close[i - 21] - 1) for i, d in enumerate(days) if i >= 21}
    rows = con.sql("select * from tt order by day, symbol").to_arrow_table().to_pylist()
    by_day: dict[date, list[dict]] = {}
    for row in rows:
        by_day.setdefault(row["day"], []).append(row)
    for day, group in by_day.items():
        bars = store.minute(day, symbols=["SPY"], columns="minute_et, close").to_pylist()
        minute = np.array([b["minute_et"] for b in bars])
        price = np.array([b["close"] for b in bars], dtype=float)
        names = [r["symbol"] for r in group]
        own = store.minute(day, symbols=names, columns="symbol, minute_et, close, volume")
        own_symbol = np.array(own["symbol"].to_pylist())
        own_minute = own["minute_et"].to_numpy()
        own_dollars = own["close"].to_numpy() * own["volume"].to_numpy()
        for row in group:
            # Dollar volume from the open to the signal bar, in multiples of a normal full day.
            mine = (own_symbol == row["symbol"]) & (own_minute >= 570)
            upto = mine & (own_minute <= row["signal_minute"])
            last15 = upto & (own_minute > row["signal_minute"] - 15)
            adv = row["adv20_prev"] or float("nan")
            row["volume_to_signal"] = float(own_dollars[upto].sum() / adv)
            row["volume_last15"] = float(own_dollars[last15].sum() / adv)
            known = minute <= row["signal_minute"]
            row["spy_vol20"] = vol20.get(day)
            row["spy_ret20"] = ret20.get(day)
            row["spy_ret_at_signal"] = (
                float(price[known][-1] / prev[day] - 1) if known.any() and day in prev else None
            )
    pq.write_table(pa.Table.from_pylist(rows), OUT / "trades.parquet")
    print(len(rows), "trades written to", OUT / "trades.parquet")


def report() -> None:
    con = duckdb.connect()
    years = ", ".join(str(y) for y in LOSING)
    con.execute(
        f"""create table t as select *, year(day) in ({years}) as losing,
                   limit_price / 0.96 / prev_close - 1 as drop_at_event
            from '{OUT}/trades.parquet'"""
    )
    print("year | trades | total 1x | net/trade 2x | win | avg win | avg loss | median | "
          "SPY vol20 med | day signals med | trades on days with 30+ signals")  # fmt: skip
    for r in con.execute(
        """select year(day), count(*), sum(net), avg(net_2x / notional), avg((net > 0)::int),
                  avg(net / notional) filter (net > 0), avg(net / notional) filter (net <= 0),
                  median(net / notional), median(spy_vol20), median(day_signals),
                  avg((day_signals >= 30)::int)
           from t group by 1 order by 1"""
    ).fetchall():
        print(f"{r[0]} | {r[1]} | {r[2]:+,.0f} | {100 * r[3]:+.2f}% | {100 * r[4]:.0f}% | "
              f"{100 * r[5]:+.2f}% | {100 * r[6]:+.2f}% | {100 * r[7]:+.2f}% | {100 * r[8]:.0f}% | "
              f"{r[9]:.0f} | {100 * r[10]:.0f}%")  # fmt: skip
    eras = """case when year(day) <= 2007 then '1 2003-07' when year(day) <= 2009 then '2 2008-09'
                   when year(day) <= 2012 then '3 2010-12' when year(day) <= 2015 then '4 2013-15'
                   else '5 2016' end"""
    features = {
        "the stock over the 60 sessions before": """case when ret60_before is null then '9 unknown'
            when ret60_before < -0.3 then '1 down over 30%' when ret60_before < 0 then '2 down'
            when ret60_before < 0.5 then '3 up to 50%' else '4 up over 50%' end""",
        "the stock over the 20 sessions before": """case when ret20_before is null then '9 unknown'
            when ret20_before < -0.2 then '1 down over 20%' when ret20_before < 0 then '2 down'
            when ret20_before < 0.2 then '3 up to 20%' else '4 up over 20%' end""",
        "dollar volume from the open to the signal, in normal days": """case
            when volume_to_signal < 0.5 then '1 under 0.5' when volume_to_signal < 1 then '2 0.5-1'
            when volume_to_signal < 2 then '3 1-2' when volume_to_signal < 4 then '4 2-4'
            else '5 4+' end""",
        "dollar volume in the 15 minutes to the signal, in normal days": """case
            when volume_last15 < 0.1 then '1 under 0.1' when volume_last15 < 0.3 then '2 0.1-0.3'
            when volume_last15 < 1 then '3 0.3-1' else '4 1+' end""",
        "the day's dollar volume against the norm (known only after the close)": """case
            when day_volume_ratio < 2 then '1 under 2x' when day_volume_ratio < 5 then '2 2-5x'
            when day_volume_ratio < 15 then '3 5-15x' else '4 15x+' end""",
        "SPY from previous close to the signal minute": """case
            when spy_ret_at_signal < -0.01 then '1 down over 1%'
            when spy_ret_at_signal < -0.003 then '2 down 0.3-1%'
            when spy_ret_at_signal < 0.003 then '3 flat' else '4 up over 0.3%' end""",
        "signals that session": """case when day_signals < 10 then '1 under 10'
            when day_signals < 30 then '2 10-29' when day_signals < 100 then '3 30-99'
            else '4 100+' end""",
        "SPY 20-day realised volatility before": """case when spy_vol20 < 0.10 then '1 under 10%'
            when spy_vol20 < 0.15 then '2 10-15%' when spy_vol20 < 0.25 then '3 15-25%'
            else '4 25%+' end""",
        "SPY over the 20 sessions before": """case when spy_ret20 < -0.05 then '1 down over 5%'
            when spy_ret20 < 0 then '2 down' when spy_ret20 < 0.03 then '3 up to 3%'
            else '4 up over 3%' end""",
        "sector": """case when industry ilike '%biotech%' or industry ilike '%drug%'
            then 'Biotech and drugs' when sector in ('Healthcare', 'Technology', 'Energy',
            'Financial Services', 'Consumer Cyclical', 'Basic Materials', 'Industrials')
            then sector else 'Other' end""",
        "market cap": """case when marketcap_prev is null then '4 unknown'
            when marketcap_prev < 3e8 then '1 under $300M'
            when marketcap_prev < 2e9 then '2 $300M-$2B' else '3 over $2B' end""",
        "time of the signal": """case when signal_minute < 600 then '1 before 10:00'
            when signal_minute < 690 then '2 10:00-11:30' when signal_minute < 810
            then '3 11:30-13:30' else '4 after 13:30' end""",
        "size of the drop at the event bar": """case when drop_at_event > -0.12 then '1 10-12%'
            when drop_at_event > -0.15 then '2 12-15%' else '3 over 15%' end""",
        "previous close": """case when prev_close < 2 then '1 $1-2' when prev_close < 5
            then '2 $2-5' when prev_close < 10 then '3 $5-10' else '4 $10+' end""",
    }
    names = [r[0] for r in con.execute(f"select distinct {eras} from t order by 1").fetchall()]
    for title, expr in features.items():
        print(f"\n### {title}: trades, net/trade at 2x, total net at 1x")
        print("bucket | " + " | ".join(names) + " | all")
        rows = con.execute(
            f"""select {expr} b, {eras} e, count(*), avg(net_2x / notional), sum(net)
                from t group by grouping sets ((1, 2), (1)) order by 1, 2"""
        ).fetchall()
        cells: dict[str, dict[str, str]] = {}
        for b, e, k, r, total in rows:
            cells.setdefault(b, {})[e or "all"] = f"{k}, {100 * r:+.2f}%, {total:+,.0f}"
        for b, row in cells.items():
            print(f"{b} | " + " | ".join(row.get(e, "0") for e in [*names, "all"]))


if __name__ == "__main__":
    {"build": build, "report": report}[sys.argv[1]]()
