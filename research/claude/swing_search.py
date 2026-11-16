"""The swing search (strategies/swing_search/HYPOTHESIS.md). Each family is a grid of
conditions on the daily table; every cell is measured on signals of 2010-01-04 to 2022-11-30,
net of costs at twice the modelled spread, for holds of 5, 10 and 15 sessions. The check on
2023 is a separate, explicit call.

    uv run python research/claude/swing_search.py prep            # once: side tables
    uv run python research/claude/swing_search.py family 1        # one family
    uv run python research/claude/swing_search.py cell "<sql condition>" [--by "<expr>"]
"""

from __future__ import annotations

import argparse
import sys
import tempfile

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

HOLDS = (5, 10, 15)
SEARCH = "day between DATE '2010-01-04' and DATE '2022-11-30'"
CHECK = "day between DATE '2023-01-03' and DATE '2023-10-13'"
CAP = """case when mcap is null then 'cap?' when mcap < 3e8 then 'micro'
              when mcap < 2e9 then 'small' when mcap < 1e10 then 'mid' else 'large' end"""


def cut(column: str, edges: list[float], unit: float = 100.0) -> str:
    """A bucket label for `column` from ascending edges, e.g. '<-10', '-10..-5', '>=20'."""
    parts = [
        f"when {column} is null then null",
        f"when {column} < {edges[0]} then '<{edges[0] * unit:g}'",
    ]
    for a, b in zip(edges, edges[1:], strict=False):
        parts.append(f"when {column} < {b} then '{a * unit:g}..{b * unit:g}'")
    return "case " + " ".join(parts) + f" else '>={edges[-1] * unit:g}' end"


FAMILIES = {
    1: (
        "ret5 <= -0.05 and history >= 60",
        {
            "fall5": cut("ret5", [-0.30, -0.20, -0.10]),
            "trend60": cut("ret60", [-0.30, 0.0, 0.30]),
            "cap": CAP,
        },
    ),
    2: (
        "react2 is not null",
        {
            "react": cut("react2", [-0.15, -0.05, 0.0, 0.05, 0.15]),
            "volume": cut("dvr2", [2, 5], 1),
            "cap": CAP,
        },
    ),
    3: (
        "high250 > 0 and history >= 200",
        {"volume": cut("dvr", [1, 2, 5], 1), "run20": cut("ret20", [0.10, 0.30]), "cap": CAP},
    ),
    4: (
        "ret120 >= 0.30 and ret5 <= -0.05 and history >= 120",
        {"up120": cut("ret120", [0.50, 1.00]), "fall5": cut("ret5", [-0.20, -0.10]), "cap": CAP},
    ),
    5: (
        "dvr >= 5 and filings_today = 0 and filings_prev = 0 and react2 is null",
        {
            "day": cut("ret1", [-0.10, -0.03, 0.03, 0.10]),
            "closed": cut("loc", [0.3, 0.7], 1),
            "cap": CAP,
        },
    ),
    6: (
        "low250 <= 0.05 and history >= 200",
        {
            "newlow": "case when low250 < 0 then 'new low' else 'within 5%' end",
            "fall20": cut("ret20", [-0.30, -0.15]),
            "closed": cut("loc", [0.3, 0.7], 1),
            "cap": CAP,
        },
    ),
    7: (
        "short_share is not null and yr >= 2018",
        {
            "short": cut("short_share", [0.02, 0.05, 0.10, 0.20]),
            "cover": cut("days_to_cover", [2, 5, 10], 1),
            "move5": cut("ret5", [-0.10, 0.10]),
        },
    ),
    8: (
        "rev_yoy is not null",
        {
            "revenue": cut("rev_yoy", [-0.10, 0.0, 0.10, 0.30]),
            "earnings": cut("ni_chg", [-0.02, -0.002, 0.002, 0.02]),
            "react": cut("freact", [-0.05, 0.05]),
            "cap": CAP,
        },
    ),
}


def connect(settings, short: bool = False) -> duckdb.DuckDBPyConnection:
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='2400MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    con.execute("set preserve_insertion_order=false")
    joins = f"""from read_parquet('{base}/daily_*.parquet') d
        left join '{base}/market.parquet' m using (day)
        left join '{base}/earn.parquet' e using (permaticker, day)
        left join '{base}/fund.parquet' f using (permaticker, day)"""
    if short:
        joins += f""" asof left join '{settings.data_dir}/research/recent/short_interest.parquet' s
            on s.symbol = d.symbol and s.known <= d.day"""
        con.execute(
            f"""create view t as select d.*, m.* exclude (day), e.* exclude (permaticker, day),
                f.* exclude (permaticker, day), s.days_to_cover,
                s.short_interest * d.close / nullif(d.mcap, 0) as short_share {joins}"""
        )
    else:
        con.execute(
            f"""create view t as select d.*, m.* exclude (day), e.* exclude (permaticker, day),
                f.* exclude (permaticker, day) {joins}"""
        )
    return con


def prep() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='2400MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    panel = f"""(select p.date as day, p.permaticker, p.prev_date, s.ticker,
                        p.marketcap_prev as mcap,
                        ln(p.close / p.prev_close) as lr,
                        p.dollar_volume / nullif(p.adv20_prev, 0) as dvr
                 from read_parquet('{store.root}/panel/*.parquet') p
                 join '{store.root}/master/security_master.parquet' s using (permaticker)
                 where p.date >= DATE '2009-06-01' and p.prev_close > 0 and p.close > 0)"""
    con.execute(
        f"""copy (
            with q as (select *, lag(lr) over w as lr_prev, lag(dvr) over w as dvr_prev
                       from {panel} window w as (partition by permaticker order by day)),
            e as (select distinct ticker, date from '{store.root}/sharadar/events.parquet'
                  where regexp_matches('|' || eventcodes || '|', '[|]22[|]'))
            select q.permaticker, q.day, any_value(exp(q.lr + q.lr_prev) - 1) as react2,
                   any_value(greatest(q.dvr, q.dvr_prev)) as dvr2
            from q join e on e.ticker = q.ticker and e.date >= q.prev_date and e.date < q.day
            group by 1, 2) to '{base}/earn.parquet' (format parquet)"""
    )
    con.execute(
        f"""copy (
            with a as (select ticker, calendardate, datekey, revenueusd as rev,
                              netinccmnusd as ni, gp, opinc, ncfo, fcf, equityusd as equity,
                              assets,
                              lag(revenueusd, 4) over w as rev4, lag(netinccmnusd, 4) over w as ni4,
                              lag(gp, 4) over w as gp4, lag(calendardate, 4) over w as cal4,
                              lag(revenueusd, 1) over w as rev1, lag(revenueusd, 5) over w as rev5
                       from '{store.root}/sharadar/sf1.parquet' where dimension = 'ARQ'
                       window w as (partition by ticker order by calendardate)),
            q as (select *, lag(lr) over w as lr_prev
                  from {panel} window w as (partition by permaticker order by day))
            select q.permaticker, q.day,
                   any_value(case when a.rev4 > 0 and a.cal4 = a.calendardate - interval 1 year
                                  then a.rev / a.rev4 - 1 end) as rev_yoy,
                   any_value(case when a.cal4 = a.calendardate - interval 1 year
                                  then (a.ni - a.ni4) / nullif(q.mcap, 0) end) as ni_chg,
                   any_value(case when a.rev4 > 0 and a.rev5 > 0 and a.rev1 > 0
                                  then a.rev / a.rev4 - a.rev1 / a.rev5 end) as rev_accel,
                   any_value(a.ni > 0) as ni_pos,
                   any_value(4 * a.fcf / nullif(q.mcap, 0)) as fcf_yield,
                   any_value(a.equity / nullif(q.mcap, 0)) as book_price,
                   any_value((a.ni - a.ncfo) / nullif(a.assets, 0)) as accruals,
                   any_value(a.gp / nullif(a.assets, 0)) as gp_assets,
                   any_value(exp(q.lr + q.lr_prev) - 1) as freact
            from q join a on a.ticker = q.ticker and a.datekey >= q.prev_date and a.datekey < q.day
            group by 1, 2) to '{base}/fund.parquet' (format parquet)"""
    )
    daily = f"read_parquet('{base}/daily_*.parquet')"
    con.execute(
        f"""copy (
            select day,
                   avg(exp(first_day + c_exit5 - c_next) - 1) as mk5,
                   avg(exp(first_day + c_exit10 - c_next) - 1) as mk10,
                   avg(exp(first_day + c_exit15 - c_next) - 1) as mk15,
                   avg(ret5) filter (mcap >= 2e9) as m5, avg(ret20) filter (mcap >= 2e9) as m20,
                   avg(ret60) filter (mcap >= 2e9) as m60,
                   avg(ret250) filter (mcap >= 2e9) as m250,
                   avg((ret60 > 0)::int) as breadth, avg(vol20) as mvol,
                   avg((high250 > 0)::int) as highs, avg((low250 < 0)::int) as lows
            from {daily} where next_open is not null group by 1 order by 1
        ) to '{base}/market.parquet' (format parquet)"""
    )
    for name in ("earn", "fund", "market"):
        print(name, con.sql(f"select count(*) from '{base}/{name}.parquet'").fetchall())


def measure(con, where: str, keys: dict[str, str], period: str = SEARCH) -> list[dict]:
    names = list(keys)
    exprs = "".join(f"{expr} as {name}, " for name, expr in keys.items())
    group = "".join(f"{n}, " for n in names)
    years = "".join(
        f"sum(s2) filter (yr = {y}) / nullif(sum(n) filter (yr = {y}), 0) as y{y}, "
        for y in range(2018, 2024)
    )
    rows = []
    for h in HOLDS:
        sql = f"""
            with b as (select {exprs} yr, date_trunc('week', day) as wk,
                              exp(first_day + c_exit{h} - c_next) - 1 as g,
                              exp(first_day + c_low{h} - c_next) - 1 as low,
                              2 * (half_spread + commission) as c1,
                              2 * (2 * half_spread + commission) as c2,
                              (ahead < {h})::int as gone, mk{h} as mk
                       from t where {period} and next_open is not null and ({where})),
            w as (select {group} yr, wk, count(*) as n, sum(g) as sg, sum(g - c1) as s1,
                         sum(g - c2) as s2, sum(gone) as gone, sum(g - mk) as sx,
                         sum(low) as slow, sum((g - c2 > 0)::int) as wins
                  from b group by all)
            select {group}
                   coalesce(sum(n) filter (yr <= 2017), 0) as n_old,
                   coalesce(sum(n) filter (yr >= 2018), 0) as n_new,
                   sum(sg) filter (yr >= 2018) / nullif(sum(n) filter (yr >= 2018), 0) as gross,
                   sum(s1) filter (yr >= 2018) / nullif(sum(n) filter (yr >= 2018), 0) as net1,
                   sum(s2) filter (yr >= 2018) / nullif(sum(n) filter (yr >= 2018), 0) as net2,
                   sum(s2) filter (yr <= 2017) / nullif(sum(n) filter (yr <= 2017), 0) as old2,
                   {years}
                   avg(s2 / n) filter (yr >= 2018) as wm,
                   stddev_samp(s2 / n) filter (yr >= 2018) as wsd,
                   count(*) filter (yr >= 2018) as weeks,
                   sum(sx) filter (yr >= 2018) / nullif(sum(n) filter (yr >= 2018), 0) as excess,
                   sum(gone) / sum(n) as gone,
                   sum(slow) filter (yr >= 2018) / nullif(sum(n) filter (yr >= 2018), 0) as low,
                   sum(wins) filter (yr >= 2018) / nullif(sum(n) filter (yr >= 2018), 0) as wins
            from w group by all"""
        cols = [d[0] for d in con.execute(sql).description]
        for r in con.fetchall():
            row = dict(zip(cols, r, strict=True))
            row["h"] = h
            row["cell"] = " | ".join(str(row[n]) for n in names)
            row["t"] = (
                row["wm"] / (row["wsd"] / row["weeks"] ** 0.5)
                if row["wsd"] and row["weeks"] and row["weeks"] > 2
                else 0.0
            )
            rows.append(row)
    return rows


def passes(r: dict) -> bool:
    return (
        r["n_new"] >= 300
        and r["n_old"] >= 300
        and (r["net2"] or 0) >= 0.01
        and r["t"] >= 4
        and all((r[f"y{y}"] or -1) > 0 for y in range(2018, 2023))
        and (r["old2"] or -1) > 0
    )


def show(rows: list[dict], minimum: int = 300, top: int = 40, key: str = "net2") -> None:
    kept = [r for r in rows if r["n_new"] >= minimum]
    kept.sort(key=lambda r: -(r[key] or -9))
    print(
        f"{len(rows)} cells measured; {len(kept)} with {minimum}+ trades in 2018-2022; "
        f"{sum(passes(r) for r in rows)} pass every rule"
    )
    print(
        "  h   n10-17  n18-22  gross  net1x  net2x  10-17 |   18    19    20    21    22 |"
        "     t  excess  gone   low  wins  cell"
    )

    def pct(v):
        return "    ." if v is None else f"{100 * v:5.1f}"

    for r in kept[:top]:
        mark = "**" if passes(r) and r["net2"] >= 0.03 else "* " if passes(r) else "  "
        print(
            f"{mark}{r['h']:2d} {r['n_old']:8d} {r['n_new']:7d}  {pct(r['gross'])}  "
            f"{pct(r['net1'])}  {pct(r['net2'])}  {pct(r['old2'])} | "
            + " ".join(pct(r[f"y{y}"]) for y in range(2018, 2023))
            + f" | {r['t']:5.1f}   {pct(r['excess'])} {pct(r['gone'])} {pct(r['low'])} "
            f"{pct(r['wins'])}  {r['cell']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=("prep", "family", "cell"))
    parser.add_argument("arg", nargs="?")
    parser.add_argument("--by", action="append", default=[])
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--top", type=int, default=40)
    parser.add_argument("--min", type=int, default=300)
    parser.add_argument("--sort", default="net2")
    a = parser.parse_args()
    if a.what == "prep":
        prep()
        return
    settings = load_settings()
    if a.what == "family":
        where, keys = FAMILIES[int(a.arg)]
        con = connect(settings, short=int(a.arg) == 7)
    else:
        where = a.arg
        keys = {f"k{i}": expr for i, expr in enumerate(a.by)} or {"k0": "'all'"}
        con = connect(settings, short="short_share" in where + " ".join(a.by))
    rows = measure(con, where, keys, CHECK if a.check else SEARCH)
    show(rows, a.min, a.top, a.sort)


if __name__ == "__main__":
    sys.exit(main())
