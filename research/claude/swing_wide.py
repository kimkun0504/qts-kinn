"""The wide daily table for the swing search (addendum of 2026-11-16 13:10 ET in
strategies/swing_search/HYPOTHESIS.md): one row per stock per session from 2010 with price,
volume, calendar, earnings-timing, fundamental and short-interest features known at the close,
and the return of buying at the next open and selling 5, 10 or 15 sessions after the signal
day. Built in twelve parts, then an industry table.

    uv run python research/claude/swing_wide.py
"""

from __future__ import annotations

import sys
import tempfile

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

PARTS = 12
HOLDS = (5, 10, 15)
W = "(partition by permaticker order by day rows between {a} preceding and {b})"


def over(a: int, b: str = "current row") -> str:
    return "over " + W.format(a=a, b=b)


def features() -> str:
    cols = [
        "day",
        "year(day) as yr",
        "symbol",
        "ticker",
        "permaticker",
        "category",
        "sector",
        "industry",
        "close",
        "mcap",
        "adv",
        "dv",
        "age",
        "filings_prev",
        "filings_today",
        "prev_date",
        "dvr",
        "greatest(dvr, lag(dvr) over w) as dvr2",
        "gap",
        "loc",
        "earn",
        "exp(lr) - 1 as ret1",
        f"sum((lr < 0)::int) {over(4)} as down5",
        f"sum((lr < 0)::int) {over(2)} as down3",
        f"stddev_samp(lr) {over(19)} as vol20",
        f"stddev_samp(lr) {over(59)} as vol60",
        f"c - max(c) {over(250, '1 preceding')} as high250",
        f"c - min(c) {over(250, '1 preceding')} as low250",
        f"c - max(c) {over(20, '1 preceding')} as high20",
        f"count(*) {over(250, '1 preceding')} as history",
        f"c - avg(c) {over(19)} as ma20",
        f"c - avg(c) {over(49)} as ma50",
        f"c - avg(c) {over(199)} as ma200",
        f"sum(greatest(lr, 0)) {over(1)} / nullif(sum(abs(lr)) {over(1)}, 0) as rsi2",
        f"sum(greatest(lr, 0)) {over(13)} / nullif(sum(abs(lr)) {over(13)}, 0) as rsi14",
        f"max(lr) {over(19)} as max20",
        f"min(lr) {over(19)} as min20",
        f"sum(night) {over(19)} as night20",
        f"sum(daytime) {over(19)} as day20",
        f"avg(dv) {over(4)} / nullif(adv, 0) as dv5",
        f"avg(rng) {over(13)} as range14",
        "lag(c, 232) over w - lag(c, 252) over w as season",
        f"rn - max(case when earn then rn end) {over(400)} as esince",
        f"252 - (rn - max(case when earn then rn end) {over(400, '200 preceding')}) as epred",
        "lead(open) over w as next_open",
        "ln(lead(close) over w / lead(open) over w) as first_day",
        "lead(c) over w as c_next",
        "count(*) over (partition by permaticker order by day "
        "rows between 1 following and 15 following) as ahead",
        """case when adv < 1e6 then 0.0100 when adv < 1e7 then 0.0043
                when adv < 1e8 then 0.0018 else 0.0005 end as half_spread""",
        "least(0.01, greatest(0.000175, 0.0035 / close)) as commission",
    ]
    for n in (2, 3, 5, 10, 20, 60, 120, 250):
        cols.append(f"exp(c - lag(c, {n}) over w) - 1 as ret{n}")
    for h in HOLDS:
        frame = (
            f"(partition by permaticker order by day rows between 1 following and {h} following)"
        )
        cols.append(f"last_value(c) over {frame} as c_exit{h}")
        cols.append(f"min(c - ln(close / low)) over {frame} as c_low{h}")
    return ",\n".join(cols)


FUND = """(select ticker, datekey,
        netinccmnusd > 0 as ni_pos,
        case when count(*) over y = 4 then sum(netinccmnusd) over y end as ni_ttm,
        case when count(*) over y = 4 then sum(fcf) over y end as fcf_ttm,
        case when count(*) over y = 4 then sum(gp) over y end as gp_ttm,
        case when count(*) over y = 4 then sum(ncfo) over y end as ncfo_ttm,
        case when lag(revenueusd, 4) over w > 0
             then revenueusd / lag(revenueusd, 4) over w - 1 end as rev_yoy,
        netinccmnusd - lag(netinccmnusd, 4) over w as ni_change,
        equityusd as equity, assets, debtusd as debt, cashnequsd as cash,
        case when lag(sharesbas, 4) over w > 0
             then sharesbas / lag(sharesbas, 4) over w - 1 end as issue,
        case when lag(assets, 4) over w > 0 then assets / lag(assets, 4) over w - 1 end as growth
    from '{root}/sharadar/sf1.parquet' where dimension = 'ARQ' and datekey is not null
    window w as (partition by ticker order by calendardate),
           y as (partition by ticker order by calendardate
                 rows between 3 preceding and current row))"""

SHORT = """(select symbol, known, short_interest, days_to_cover,
                 lag(short_interest) over (partition by symbol order by known) as short_prev
          from '{data}/research/recent/short_interest.parquet')"""


def main() -> None:
    early = "--early" in sys.argv  # 2005 to 2009, for the out-of-sample test of two rules
    start, first, last, name = (
        ("2003-09-10", "2005-01-03", "2009-12-31", "early")
        if early
        else ("2008-06-01", "2010-01-04", "2100-01-01", "wide")
    )
    settings = load_settings()
    store = DataStore(settings)
    out = settings.data_dir / "research" / "swing"
    scratch = tempfile.mkdtemp()
    earnings = out / ("earn_early.parquet" if early else "earn.parquet")
    if early and not earnings.exists():
        duckdb.execute(
            f"""copy (
                select distinct q.permaticker, q.date as day
                from read_parquet('{store.root}/panel/*.parquet') q
                join '{store.root}/master/security_master.parquet' s using (permaticker)
                join (select distinct ticker, date from '{store.root}/sharadar/events.parquet'
                      where regexp_matches('|' || eventcodes || '|', '[|]22[|]')) e
                  on e.ticker = s.ticker and e.date >= q.prev_date and e.date < q.date
                where q.date between DATE '{start}' and DATE '{last}'
            ) to '{earnings}' (format parquet)"""
        )
    for part in range(PARTS):
        target = out / f"{name}_{part}.parquet"
        if target.exists():
            continue
        con = duckdb.connect()
        con.execute(f"set threads=2; set memory_limit='2300MB'; set temp_directory='{scratch}'")
        con.execute("set preserve_insertion_order=false")
        tmp = out / f"{name}_{part}.tmp"
        con.execute(
            f"""copy (
                with p as (
                    select p.date as day, p.symbol, s.ticker, p.permaticker, p.category, s.sector,
                           s.industry, p.open, p.low, p.close, p.prev_date,
                           p.marketcap_prev as mcap, p.adv20_prev as adv, p.dollar_volume as dv,
                           p.sessions_prior as age, p.filings_prev, p.filings_today,
                           p.dollar_volume / nullif(p.adv20_prev, 0) as dvr,
                           p.open / p.prev_close - 1 as gap,
                           (p.close - p.low) / nullif(p.high - p.low, 0) as loc,
                           ln(p.close / p.prev_close) as lr, ln(p.open / p.prev_close) as night,
                           ln(p.close / p.open) as daytime, ln(p.high / p.low) as rng,
                           e.permaticker is not null as earn
                    from read_parquet('{store.root}/panel/*.parquet') p
                    left join '{store.root}/master/security_master.parquet' s using (permaticker)
                    left join '{earnings}' e
                      on e.permaticker = p.permaticker and e.day = p.date
                    where p.date >= DATE '{start}' and p.date <= DATE '{last}'
                      and p.permaticker % {PARTS} = {part}
                      and p.prev_close > 0 and p.close > 0 and p.low > 0 and p.open > 0
                      and p.category like '%Common Stock%'),
                q as (select *, sum(lr) over (partition by permaticker order by day) as c,
                             row_number() over (partition by permaticker order by day) as rn
                      from p),
                r as (select {features()} from q
                      window w as (partition by permaticker order by day)),
                k as (select * from r
                      where day >= DATE '{first}' and close >= 1 and adv >= 250000),
                kf as (select k.*, f.datekey >= k.prev_date as fnew,
                              date_diff('day', f.datekey, k.day) as fage, f.ni_pos, f.rev_yoy,
                              f.ni_ttm / nullif(k.mcap, 0) as earn_price,
                              f.fcf_ttm / nullif(k.mcap, 0) as fcf_price,
                              f.equity / nullif(k.mcap, 0) as book_price,
                              (f.cash - f.debt) / nullif(k.mcap, 0) as netcash_price,
                              f.ni_change / nullif(k.mcap, 0) as ni_chg,
                              f.gp_ttm / nullif(f.assets, 0) as gp_assets,
                              f.debt / nullif(f.assets, 0) as debt_assets,
                              (f.ni_ttm - f.ncfo_ttm) / nullif(f.assets, 0) as accruals,
                              f.issue, f.growth
                       from k asof left join {FUND.format(root=store.root)} f
                         on f.ticker = k.ticker and f.datekey < k.day)
                select kf.*, s.days_to_cover,
                       s.short_interest * kf.close / nullif(kf.mcap, 0) as short_share,
                       s.short_interest / nullif(s.short_prev, 0) - 1 as short_chg,
                       date_diff('day', s.known, kf.day) as short_age
                from kf asof left join {SHORT.format(data=settings.data_dir)} s
                  on s.symbol = kf.symbol and s.known <= kf.day
            ) to '{tmp}' (format parquet, compression zstd)"""
        )
        tmp.rename(target)
        con.close()
        print("part", part, "done", flush=True)
    con = duckdb.connect()
    con.execute(
        f"""copy (select day, industry, count(*) as ind_n, avg(ret5) as ind5,
                         avg(ret20) as ind20, avg(ret60) as ind60, avg(ret120) as ind120
                  from read_parquet('{out}/{name}_*.parquet') where industry is not null
                  group by 1, 2) to '{out}/industry_{name}.parquet' (format parquet)"""
    )
    if early:
        con.execute(
            f"""copy (
                select day, avg(exp(first_day + c_exit5 - c_next) - 1) as mk5,
                       avg(exp(first_day + c_exit10 - c_next) - 1) as mk10,
                       avg(exp(first_day + c_exit15 - c_next) - 1) as mk15,
                       avg(ret5) filter (mcap >= 2e9) as m5, avg(ret20) filter (mcap >= 2e9) as m20
                from read_parquet('{out}/early_*.parquet') where next_open is not null
                group by 1 order by 1) to '{out}/market_early.parquet' (format parquet)"""
        )
    print("industry done", flush=True)


if __name__ == "__main__":
    main()
