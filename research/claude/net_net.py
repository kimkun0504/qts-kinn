"""strategies/net_net/HYPOTHESIS.md: small companies priced under their net current assets.

    cd research/claude
    uv run python net_net.py table
    uv run python net_net.py search
    uv run python net_net.py test 1.0 250 all
"""

from __future__ import annotations

import csv
import io
import sys
import tempfile
import zipfile

import duckdb
import numpy as np
import pyarrow as pa
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

HOLDS = (120, 250)
BAR = {120: 0.04, 250: 0.08}
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def folder():
    return load_settings().data_dir / "research" / "net_net"


def table() -> None:
    settings = load_settings()
    store = DataStore(settings)
    raw = max((settings.raw_dir / "sharadar").iterdir())
    places = {}
    with zipfile.ZipFile(next(raw.glob("SHARADAR_TICKERS_*.zip"))) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            if row["table"] == "SF1":
                places[row["ticker"]] = row.get("location") or ""
    china = [t for t, loc in places.items() if "china" in loc.lower() or "hong kong" in loc.lower()]
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    con.register("china", pa.table({"ticker": china}))
    parts = []
    for hold in HOLDS:
        con.execute(
            f"""copy (
                with p as (
                    select permaticker, date, ticker, category, close, adv20_prev as adv, marketcap_prev as mcap,
                           open / close as oc, sum(ln(close / prev_close)) over w as c, row_number() over w as rn
                    from read_parquet('{store.root}/panel/*.parquet')
                    where date <= DATE '2023-11-08' and prev_close > 0 and close > 0 and open > 0
                    window w as (partition by permaticker order by date))
                select permaticker, date, ticker, category, close, adv, mcap, rn,
                       lead(date) over w as entry, lead(oc) over w as oc1, lead(c) over w as c1,
                       last_value(c) over (w rows between 1 following and {hold} following) as c_end,
                       lead(c, {hold}) over w as c_full
                from p window w as (partition by permaticker order by date)
                qualify mcap >= 3e7 and mcap < 2e9 and adv >= 250000 and close >= 1
                ) to '{folder()}/h{hold}.parquet' (format parquet)"""
        )
        con.execute(f"create or replace view h{hold} as select * from '{folder()}/h{hold}.parquet'")
        con.execute(
            f"""create or replace table bench{hold} as
                select entry as date, avg(exp(c_full - c1) / oc1 - 1) as everyone
                from h{hold} where category like '%Common Stock%' and mcap >= 3e7 and mcap < 3e8
                  and adv >= 250000 and close >= 1 and c_full is not null group by 1"""
        )
        parts.append(
            f"""select {hold} as hold, a.datekey, h.date as day, h.entry, h.ticker, h.permaticker, h.rn, h.mcap, h.adv,
                       h.close, a.assetsc - a.liabilities as ncav, h.mcap / (a.assetsc - a.liabilities) as ratio,
                       h.ticker in (select ticker from china) as china,
                       exp(h.c_end - h.c1) / h.oc1 - 1 as g, b.everyone,
                       2 * (least(0.01, greatest(0.000175, 0.0035 / h.close))
                            + case when h.adv < 1e6 then 0.0025 when h.adv < 1e7 then 0.0010
                                   when h.adv < 1e8 then 0.0005 else 0.0002 end) as cost
                from '{folder()}/ncav.parquet' a asof join h{hold} h on h.ticker = a.ticker and h.date >= a.datekey
                left join bench{hold} b on b.date = h.entry
                where a.datekey between DATE '2005-01-01' and DATE '2023-10-13' and a.assetsc - a.liabilities > 0
                  and h.date <= a.datekey + 7 and h.category like '%Common Stock%' and h.mcap >= 3e7
                  and h.adv >= 250000 and h.close >= 1 and h.c1 is not null
                  and h.mcap < a.assetsc - a.liabilities"""
        )
    con.execute(f"copy ({' union all '.join(parts)}) to '{folder()}/events.parquet' (format parquet)")
    print(con.sql(f"select hold, count(*), sum(china::int), min(day), max(day) from '{folder()}/events.parquet' group by 1").fetchall())


def load(hold: int, cut: float, which: str) -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week
            from '{folder()}/events.parquet' where hold = {hold} and ratio < {cut}
            {"and not china" if which == "exchina" else ""} order by permaticker, day"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    keep = np.zeros(len(d["day"]), bool)
    last: dict = {}
    for i in range(len(keep)):  # one event a company in 250 sessions
        company, rn = d["permaticker"][i], d["rn"][i]
        if rn - last.get(company, -(10**9)) >= 250:
            keep[i] = True
            last[company] = rn
    return {k: v[keep] for k, v in d.items()}


def measure(d, period) -> dict:
    first, last = PERIODS[period]
    keep = (d["yr"] >= first) & (d["yr"] <= last) & ~np.isnan(d["everyone"].astype(float))
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    over = d["g"][keep].astype(float) - d["everyone"][keep].astype(float)
    net = d["g"][keep].astype(float) - d["cost"][keep]
    _, t, _ = weekly(over, d["week"][keep])
    years = d["yr"][keep]
    return {"n": n, "over": over.mean(), "median": np.median(over), "net": net.mean(), "t": t,
            "pos": sum(over[years == y].mean() > 0 for y in set(years)), "years": len(set(years)),
            "yearly": {int(y): over[years == y].mean() for y in sorted(set(years))}}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:26} {m['n']}"
    return (f"{label:26} {m['n']:>4} trades  over the average stock {100 * m['over']:>6.2f}% (median {100 * m['median']:>6.2f}%)  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  after costs {100 * m['net']:>6.2f}%")  # fmt: skip


def search() -> None:
    for cut in (1.0, 0.67):
        for hold in HOLDS:
            for which in ("all", "exchina"):
                m = measure(load(hold, cut, which), "search")
                ok = m["n"] >= 3 and m["over"] >= BAR[hold] and m["t"] >= 3 and m["pos"] >= 6 and m["net"] > 0
                print(show(f"under {cut} {hold} {which}", m) + ("  MEETS THE BAR" if ok else ""))


def test(cut, hold, which) -> None:
    d = load(int(hold), float(cut), which)
    for period in ("early", "late"):
        m = measure(d, period)
        print(show(f"under {cut} {hold} {which} {period}", m))
        if m["n"] >= 3:
            print("    " + "  ".join(f"{y} {100 * v:.1f}%" for y, v in m["yearly"].items()))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:5])
