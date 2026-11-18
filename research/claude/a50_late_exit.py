"""strategies/intraday_shape/HYPOTHESIS.md, addendum "an exit for the earnings rule".

    cd research/claude
    uv run python a50_late_exit.py
"""

from __future__ import annotations

import tempfile

import duckdb
import numpy as np

from intraday_shape import folder as shape
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

A50 = "earn and ret2 >= 0.15 and dvr2 >= 5 and mcap >= 5e7 and mcap < 3e8"
AUCTION = """2 * (least(0.01, greatest(0.000175, 0.0035 / s.close)) + case when s.adv < 1e6 then 0.0025
              when s.adv < 1e7 then 0.0010 when s.adv < 1e8 then 0.0005 else 0.0002 end)"""
SPANS = {"2010-2017": (2010, 2017), "2005-2009": (2005, 2009), "2018-2022": (2018, 2022), "2023": (2023, 2023)}


def main() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
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
                         sum(ln(close / prev_close)) over w as c, row_number() over w as rn
                  from read_parquet('{store.root}/panel/*.parquet')
                  where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                  and permaticker in (select permaticker from s)
                  window w as (partition by permaticker order by date)),
            q as (select p.*, ln(p.close / g.p1530) as late
                  from p left join read_parquet('{shape()}/segments_*.parquet') g on g.symbol = p.symbol and g.day = p.date)
            select s.day, year(s.day) as yr, {AUCTION} as cost, q.rn - d.rn as k, q.c, q.oc, q.late
            from s join q d on d.permaticker = s.permaticker and d.date = s.day
            join q on q.permaticker = s.permaticker and q.rn between d.rn + 1 and d.rn + 15
            order by s.day, s.permaticker, k"""
    ).fetchall()
    trades: dict = {}
    for day, yr, cost, k, c, oc, late in rows:
        trades.setdefault((day, cost), {"yr": yr, "cost": cost})[k] = (c, oc, late)
    out = {name: [] for name in ("plain", "late 4%", "late 2%", "3 sessions 6%", "3 sessions 3%")}
    years = []
    for (day, cost), t in trades.items():
        if not all(k in t for k in range(1, 16)):
            continue
        c1, oc1 = t[1][0], t[1][1]
        plain = np.exp(t[15][0] - c1) / oc1 - 1
        out["plain"].append(plain - cost)
        years.append(t["yr"])
        lates = [t[k][2] for k in range(1, 16)]

        def exit_after(test):
            for k in range(1, 15):
                if test(k):
                    return np.exp(t[k + 1][0] - c1) * t[k + 1][1] / oc1 - 1 - cost
            return plain - cost

        def ok(v):
            return v is not None and not np.isnan(v)

        out["late 4%"].append(exit_after(lambda k: ok(lates[k - 1]) and lates[k - 1] >= np.log(1.04)))
        out["late 2%"].append(exit_after(lambda k: ok(lates[k - 1]) and lates[k - 1] >= np.log(1.02)))
        three = lambda k, x: k >= 3 and all(ok(lates[j]) for j in range(k - 3, k)) and sum(lates[k - 3 : k]) >= np.log(1 + x)  # noqa: E731
        out["3 sessions 6%"].append(exit_after(lambda k: three(k, 0.06)))
        out["3 sessions 3%"].append(exit_after(lambda k: three(k, 0.03)))
    years = np.array(years)
    print(f"{len(years)} A50 trades with a full 15-session path")
    plain = np.array(out["plain"])
    for name in ("late 4%", "3 sessions 6%"):
        diff = np.array(out[name]) - plain
        for span, (a, b) in SPANS.items():
            m = (years >= a) & (years <= b) & (diff != 0)
            if m.sum() > 2:
                print(f"  {name:14} {span}: fired in {m.sum():>3} trades, mean change {100 * diff[m].mean():6.2f} points, "
                      f"t {diff[m].mean() / (diff[m].std(ddof=1) / m.sum() ** 0.5):5.2f}")
    for name, values in out.items():
        v = np.array(values)
        cells = [f"{span} {100 * v[(years >= a) & (years <= b)].mean():6.2f}% ({((years >= a) & (years <= b)).sum()})"
                 for span, (a, b) in SPANS.items()]  # fmt: skip
        print(f"{name:15} " + "  ".join(cells))


if __name__ == "__main__":
    main()
