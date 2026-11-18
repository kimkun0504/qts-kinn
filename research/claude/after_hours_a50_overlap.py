"""strategies/after_hours addendum: overlap of the small-company long (large pieces, next open)
with A50.

    cd research/claude
    uv run python after_hours_footprint.py small_open   # writes small_large_open.parquet
    uv run python after_hours_a50_overlap.py
"""

from __future__ import annotations

import duckdb

from a50_late_exit import A50
from after_hours import folder
from kinn.core.settings import load_settings
from kinn.data.store import DataStore


def main() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    print(duckdb.sql(
        f"""with e as (select * from '{folder()}/small_large_open.parquet'),
            m as (select e.*, p.permaticker from e join read_parquet('{store.root}/panel/*.parquet') p
                  on p.symbol = e.symbol and p.date = e.day),
            a as (select day, permaticker from read_parquet('{base}/early_*.parquet') where {A50}
                  union all select day, permaticker from read_parquet('{base}/wide_*.parquet') where {A50}),
            f as (select m.*, exists (select 1 from a where a.permaticker = m.permaticker
                                      and a.day > m.day and a.day <= m.day + 5) as in_a50 from m)
            select case when yr <= 2009 then '2005-2009' when yr <= 2017 then '2010-2017'
                        when yr <= 2022 then '2018-2022' else '2023' end as period,
                   count(*) as n, sum(in_a50::int) as also_a50,
                   round(100 * avg(net) filter (where not in_a50), 2) as rest_mean,
                   round(100 * avg(net) filter (where in_a50), 2) as a50_mean
            from f group by 1 order by 1"""
    ).fetchall())


if __name__ == "__main__":
    main()
