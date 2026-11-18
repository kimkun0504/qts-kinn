"""strategies/sympathy/HYPOTHESIS.md: peers that gap down after an industry name collapses
after hours on its results.

    cd research/claude
    uv run python sympathy.py table
    uv run python sympathy.py search
    uv run python sympathy.py test 2 1
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import weekly

import after_hours as ah
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from night_bids import folder as shared

PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
BAR = {1: 0.003, 5: 0.01}


def folder():
    out = load_settings().data_dir / "research" / "sympathy"
    out.mkdir(parents=True, exist_ok=True)
    return out


def table() -> None:
    settings = load_settings()
    store = DataStore(settings)
    swing = settings.data_dir / "research" / "swing"
    a = ah.folder()
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.execute(
        f"""copy (
            with trig as (
                select n.day, n.symbol, w.industry
                from read_parquet('{a}/entries_*.parquet') n
                join '{a}/events.parquet' v on v.day = n.day and v.symbol = n.symbol and v.timing = n.timing
                join (select day, symbol, industry from read_parquet('{swing}/wide_*.parquet')
                      union all select day, symbol, industry from read_parquet('{swing}/early_*.parquet')) w
                  on w.day = n.day and w.symbol = n.symbol
                where n.timing = 'after' and v.mcap >= 3e8 and n.reaction <= -0.15 and w.industry is not null),
            peers as (
                select distinct t.day, w.permaticker, w.symbol
                from trig t join (select day, symbol, permaticker, industry, mcap, adv, close, category
                                  from read_parquet('{swing}/wide_*.parquet')
                                  union all select day, symbol, permaticker, industry, mcap, adv, close, category
                                  from read_parquet('{swing}/early_*.parquet')) w
                  on w.day = t.day and w.industry = t.industry and w.symbol <> t.symbol
                where w.mcap >= 3e8 and w.adv >= 1e6 and w.close >= 5 and w.category like '%Common Stock%'
                  and not exists (select 1 from '{shared()}/results_due.parquet' x
                                  where x.permaticker = w.permaticker and x.day = t.day)),
            p as (select permaticker, date, close, adv20_prev as adv, open / close as oc,
                         sum(ln(close / prev_close)) over w as c
                  from read_parquet('{store.root}/panel/*.parquet')
                  where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                    and permaticker in (select permaticker from peers)
                  window w as (partition by permaticker order by date)),
            q as (select *, lead(c, 1) over w as c1, lead(oc, 1) over w as oc1, lead(c, 5) over w as c5
                  from p window w as (partition by permaticker order by date))
            select peers.day, peers.symbol, peers.permaticker, q.adv, q.close,
                   exp(q.c1 - q.c) * q.oc1 - 1 as gap, 1 / q.oc1 - 1 as g1, exp(q.c5 - q.c1) / q.oc1 - 1 as g5,
                   2 * (least(0.01, greatest(0.000175, 0.0035 / q.close))
                        + case when q.adv < 1e6 then 0.0025 when q.adv < 1e7 then 0.0010
                               when q.adv < 1e8 then 0.0005 else 0.0002 end) as cost
            from peers join q on q.permaticker = peers.permaticker and q.date = peers.day
            where q.c5 is not null and peers.day <= DATE '2023-10-13'
        ) to '{folder()}/peers.parquet' (format parquet)"""
    )
    print(con.sql(f"select count(*), count(*) filter (where gap <= -0.02), count(*) filter (where gap <= -0.03) from '{folder()}/peers.parquet'").fetchall())


def run(gap: int, hold: int, period: str):
    a, b = PERIODS[period]
    t = duckdb.sql(
        f"""select day, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week, g{hold} - cost as net
            from '{folder()}/peers.parquet' where gap <= {-gap / 100} and year(day) between {a} and {b}"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    net = d["net"].astype(float)
    if len(net) < 3:
        return f"gap {gap}% hold {hold} {period}: {len(net)}", None
    _, tt, _ = weekly(net, d["week"])
    years = d["yr"]
    yearly = {int(y): net[years == y].mean() for y in sorted(set(years))}
    pos = sum(v > 0 for v in yearly.values())
    ok = len(net) >= 150 and net.mean() >= BAR[hold] and tt >= 3 and pos >= 6
    return (f"gap {gap}% hold {hold} {period:6} {len(net):>5} trades  net {100 * net.mean():6.2f}%  "
            f"median {100 * np.median(net):6.2f}%  t {tt:5.2f}  yrs {pos} of {len(yearly)}"
            + ("  MEETS THE BAR" if period == "search" and ok else "")), yearly  # fmt: skip


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        for gap in (2, 3):
            for hold in (1, 5):
                print(run(gap, hold, "search")[0])
    else:
        for period in ("early", "late"):
            text, yearly = run(int(sys.argv[2]), int(sys.argv[3]), period)
            print(text)
            print("    " + "  ".join(f"{y} {100 * v:.2f}%" for y, v in (yearly or {}).items()))
