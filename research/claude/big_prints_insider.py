"""strategies/big_prints/HYPOTHESIS.md, follow-up 8: the footprint beside rule I.

    cd research/claude
    uv run python big_prints_insider.py
"""

from __future__ import annotations

import tempfile
from datetime import date

import duckdb
import numpy as np
import pyarrow as pa

import insider_study as study
from insider_book import RULE_I
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_earnings import weekly


def main() -> None:
    kept = []
    for period in ("early", "choose", "late", "check"):
        d = study.rows(period)
        keep = study.pick(d, *RULE_I)
        kept += [(period, int(p), date.fromisoformat(str(day)[:10]), float(g) - float(c), int(w))
                 for p, day, g, c, w in zip(d["permaticker"][keep], d["day"][keep], d["g15"][keep],
                                            d["cost"][keep], d["week"][keep], strict=True)]  # fmt: skip
    signals = pa.table({k: [r[i] for r in kept] for i, k in enumerate(("period", "permaticker", "day", "net", "week"))})
    store = DataStore(load_settings())
    bars = store.bars_roots[0] / "daily"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("s", signals)
    t = con.sql(
        f"""with p as (select permaticker, date, symbol from read_parquet('{store.root}/panel/*.parquet')
                       where date <= DATE '2023-11-08' and permaticker in (select permaticker from s)),
            b as (select p.permaticker, p.date, d.volume / d.transactions as ats
                  from p join read_parquet('{bars}/*.parquet') d on d.symbol = p.symbol and d.date = p.date
                  where d.transactions > 0 and d.volume > 0),
            f as (select permaticker, date, ats / exp(avg(ln(ats)) over (partition by permaticker order by date
                         rows between 60 preceding and 1 preceding)) as fp from b)
            select s.*, f.fp from s left join f on f.permaticker = s.permaticker and f.date = s.day"""
    ).fetchnumpy()
    fp = t["fp"].filled(np.nan) if np.ma.isMaskedArray(t["fp"]) else t["fp"]
    for period in ("early", "choose", "late", "check"):
        k = t["period"] == period
        out = []
        for label, keep in (("rule I", k), ("footprint 1.5+", k & (fp >= 1.5)), ("under 1.5", k & (fp < 1.5))):
            _, tt, _ = weekly(t["net"][keep], t["week"][keep])
            out.append(f"{label} {keep.sum()} {100 * t['net'][keep].mean():+.2f}% (t {tt:.2f})")
        print(f"{period}: " + "; ".join(out))


if __name__ == "__main__":
    main()
