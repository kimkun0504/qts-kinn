"""Family 11c of the search (strategies/recent_search/HYPOTHESIS.md): short interest as a
second cut on the premarket runners of family 9. Search years only (2018-2022)."""

from __future__ import annotations

import duckdb

from kinn.core.settings import load_settings


def main() -> None:
    base = load_settings().data_dir / "research" / "recent"
    con = duckdb.connect()
    con.execute("set threads=3; set memory_limit='2500MB'")
    con.execute(
        f"""create table runners as
            select b.day, b.yr, b.symbol, b.prev_close, b.mcap, b.half_spread, b.commission,
                   b.official_close, t.t, t.e, t.sofar
            from read_parquet('{base}/base_*.parquet') b
            join (select day, symbol, 480 as t, e480 as e, em480 as em,
                         c480 / nullif(dv480, 0) * 0 + c480 as c, dv480 as dv
                  from read_parquet('{base}/premarket/*.parquet')
                  union all
                  select day, symbol, 540, e540, em540, c540, dv540
                  from read_parquet('{base}/premarket/*.parquet')) p using (day, symbol)
            cross join lateral (select p.t as t, p.e as e, p.c / b.prev_close - 1 as sofar) t
            where b.yr <= 2022 and p.em <= p.t + 15 and p.em < 570
              and p.c / b.prev_close - 1 >= 0.20 and p.dv / b.adv >= 0.10"""
    )
    rows = con.execute(
        f"""with x as (
                select r.*, s.short_interest * r.prev_close / nullif(r.mcap, 0) as short_share,
                       s.days_to_cover
                from runners r asof left join '{base}/short_interest.parquet' s
                  on s.symbol = r.symbol and s.known <= r.day),
            y as (select t, case when sofar >= 0.5 then 'up 50%+' else 'up 20-50%' end as move,
                         case when short_share is null then 'unknown'
                              when short_share < 0.05 then 'under 5%'
                              when short_share < 0.15 then '5-15%' else 'over 15%' end as short,
                         case when days_to_cover is null then 'unknown'
                              when days_to_cover < 2 then 'under 2' when days_to_cover < 5
                              then '2-5' else 'over 5' end as cover,
                         day, yr, official_close / e - 1 as r,
                         6 * half_spread + 2 * commission as cost from x),
            d as (select t, move, short, cover, day, any_value(yr) as yr, count(*) as n,
                         avg(r) as gross, avg(r - cost) as net from y group by 1, 2, 3, 4, 5)
            select t, move, short, cover, sum(n), sum(gross * n) / sum(n),
                   sum(net * n) / sum(n),
                   avg(net) / nullif(stddev_samp(net) / sqrt(count(*)), 0),
                   sum((yr >= 2021)::int * gross * n) / nullif(sum((yr >= 2021)::int * n), 0)
            from d group by 1, 2, 3, 4 order by 6 desc"""
    ).fetchall()
    print(f"cells: {len(rows)}; with 100+ trades: {sum(r[4] >= 100 for r in rows)}")
    print(f"{'time':>5} {'move':10}{'short':>10}{'cover':>9}{'trades':>8}{'gross%':>8}{'net%':>8}"
          f"{'t':>6}{'gross 2021-22':>15}")  # fmt: skip
    for t, move, short, cover, n, gross, net, tstat, late in rows:
        if n >= 100:
            print(f"{t // 60:02d}:00 {move:10}{short:>10}{cover:>9}{n:>8.0f}{100 * gross:>8.2f}"
                  f"{100 * net:>8.2f}{tstat or 0:>6.1f}{100 * (late or 0):>15.2f}")  # fmt: skip


if __name__ == "__main__":
    main()
