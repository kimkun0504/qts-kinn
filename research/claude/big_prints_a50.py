"""strategies/big_prints/HYPOTHESIS.md, follow-up 3: the footprint as a filter on rule A50.

    cd research/claude
    uv run python big_prints_a50.py
"""

from __future__ import annotations

import tempfile

import duckdb
import numpy as np

from a50_late_exit import A50, AUCTION, SPANS
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly


def main() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    bars = store.bars_roots[0] / "daily"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    rows = con.sql(
        f"""with s as (
                select day, permaticker, close, adv from read_parquet('{base}/early_*.parquet')
                where {A50} and next_open is not null and day >= DATE '2005-01-03'
                union all
                select day, permaticker, close, adv from read_parquet('{base}/wide_*.parquet')
                where {A50} and next_open is not null and day <= DATE '2023-10-13'),
            p as (select permaticker, date, symbol, close, open / close as oc,
                         sum(ln(close / prev_close)) over w as c
                  from read_parquet('{store.root}/panel/*.parquet')
                  where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                  and permaticker in (select permaticker from s)
                  window w as (partition by permaticker order by date)),
            b as (select p.*, d.volume / d.transactions as ats
                  from p left join read_parquet('{bars}/*.parquet') d on d.symbol = p.symbol and d.date = p.date
                  and d.transactions > 0 and d.volume > 0),
            q as (select *, ats / exp(avg(ln(ats)) over (partition by permaticker order by date
                                rows between 60 preceding and 1 preceding)) as fp,
                         lead(c, 1) over w as c1, lead(oc, 1) over w as oc1,
                         last_value(c) over (partition by permaticker order by date
                                             rows between current row and 15 following) as c15
                  from b window w as (partition by permaticker order by date))
            select s.day, year(s.day) as yr, (date_diff('day', DATE '2003-12-29', s.day) // 7) as week,
                   q.fp, exp(q.c15 - q.c1) / q.oc1 - 1 - {AUCTION} as net
            from s join q on q.permaticker = s.permaticker and q.date = s.day
            where q.c1 is not null"""
    ).fetchnumpy()
    for name, (first, last) in SPANS.items():
        k = (rows["yr"] >= first) & (rows["yr"] <= last)
        fp = rows["fp"][k]
        net = rows["net"][k]
        has = ~np.isnan(fp)
        out = []
        for label, keep in (("all A50", np.ones(len(net), bool)), ("footprint 1+", has & (fp >= 1)),
                            ("footprint under 1", has & (fp < 1))):  # fmt: skip
            _, t, _ = weekly(net[keep], rows["week"][k][keep])
            out.append(f"{label} {keep.sum()} {100 * net[keep].mean():+.2f}% (t {t:.2f})")
        print(f"{name}: " + "; ".join(out) + f"; footprint median {np.nanmedian(fp):.2f}")


if __name__ == "__main__":
    main()
