"""strategies/deal_spread/HYPOTHESIS.md: a takeover target bought after its tender-offer or
merger filing and held to the close of the deal. Needs the owner's
`download_edgar_times.py --what other`.

    cd research/claude
    uv run python deal_spread.py table
    uv run python deal_spread.py search
    uv run python deal_spread.py test tender all 60
"""

from __future__ import annotations

import sys
import tempfile
from collections import Counter, defaultdict
from datetime import timedelta

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_earnings import AUCTION, weekly

import sec_times
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

FORMS = {"SC 14D9": "tender", "DEFM14A": "vote"}
PINNED = 0.0075  # the 20-session standard deviation of daily returns at or under which a stock is pinned
SIZES = {"all": 5e7, "larger": 3e8}
CELLS = [("tender", size, hold) for size in SIZES for hold in (20, 60)] + \
        [("pinned", size, hold) for size in SIZES for hold in (60, 120)] + \
        [("unpinned", size, 120) for size in SIZES]  # fmt: skip
HOLDS = (20, 60, 120)
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}


def events_path(name: str = "deals"):
    return load_settings().data_dir / "research" / "swing" / f"{name}.parquet"


def table() -> None:
    """(stock, R, kind) for the first SC 14D9 and the first DEFM14A a company files in 250
    days: R is the first session whose close comes after the SEC accepted it."""
    stocks, days = sec_times.numbers(), sec_times.sessions()
    rows = defaultdict(list)
    for row in sec_times.filings("other_forms.jsonl.gz"):
        if row["form"] in FORMS and row["cik"] in stocks:
            when = sec_times.accepted(row)
            session = sec_times.reaction_session(days, when) if when else None
            if session:
                rows[(row["cik"], FORMS[row["form"]])].append(session)
    found = set()
    for (cik, kind), sessions in rows.items():
        last = None
        for session in sorted(sessions):
            if last is None or session - last > timedelta(days=250):
                for permaticker in stocks[cik]:
                    found.add((permaticker, session, kind))
            last = session
    pq.write_table(pa.table({"permaticker": [k[0] for k in found], "day": [k[1] for k in found],
                             "kind": [k[2] for k in found]}), events_path())  # fmt: skip
    print(f"{len(found)} filings: {Counter(k[2] for k in found)}")


def load(name: str = "deals") -> dict[str, np.ndarray]:
    """Every event in the universe with its return from the next open to the last close it
    trades within each hold, the sessions it was held, and its costs."""
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    ahead = ", ".join(
        f"""last_value(c) over (partition by permaticker order by date
                                rows between current row and {h} following) as c{h},
            count(*) over (partition by permaticker order by date
                           rows between 1 following and {h} following) as n{h}"""
        for h in HOLDS
    )
    returns = ", ".join(f"exp(p.c{h} - p.c_next) / p.next_oc - 1 as g{h}, p.n{h}" for h in HOLDS)
    parts = []
    for tables in ("early", "wide"):
        parts.append(
            f"""select d.day, d.yr, (date_diff('day', DATE '2003-12-29', d.day) // 7) as week,
                       f.kind, d.mcap, d.vol20, {AUCTION} as cost, {returns}
                from read_parquet('{base}/{tables}_*.parquet') d
                join '{events_path(name)}' f on f.permaticker = d.permaticker and f.day = d.day
                join (select permaticker, date, lead(c) over w as c_next,
                             lead(open / close) over w as next_oc, {ahead}
                      from (select permaticker, date, open, close,
                                   sum(ln(close / prev_close)) over (partition by permaticker order by date) as c
                            from read_parquet('{store.root}/panel/*.parquet')
                            where prev_close > 0 and close > 0 and low > 0 and open > 0
                              and category like '%Common Stock%')
                      window w as (partition by permaticker order by date)) p
                  on p.permaticker = d.permaticker and p.date = d.day
                where d.day between DATE '2005-01-03' and DATE '2023-10-13' and d.next_open is not null"""
        )
    table = con.sql(" union all ".join(parts)).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def pick(d, kind, size, period):
    first, last = PERIODS[period]
    vol = d["vol20"].astype(float)
    if kind == "tender":
        mine = d["kind"] == "tender"
    elif kind == "pinned":
        mine = (d["kind"] == "vote") & (vol <= PINNED)
    else:
        mine = (d["kind"] == "vote") & ~(vol <= PINNED)
    return mine & (d["mcap"] >= SIZES[size]) & (d["yr"] >= first) & (d["yr"] <= last)


def measure(d, keep, hold) -> dict:
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    gross = d[f"g{hold}"][keep].astype(float)
    net = gross - d["cost"][keep]
    held = d[f"n{hold}"][keep].astype(float)
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    positive = sum(net[years == y].mean() > 0 for y in set(years))
    return {"n": n, "net": net.mean(), "t": t, "pos": positive, "years": len(set(years)),
            "held": held.mean(), "a_year": net.mean() * 252 / max(held.mean(), 1),
            "worst": net.min(), "worst1": np.sort(net)[: max(1, n // 100)].mean(),
            "wins": (net > 0).mean(), "ended": (held < hold).mean()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:26} {m['n']:>5}"
    return (f"{label:26} {m['n']:>5}  net {100 * m['net']:>6.2f}%  t {m['t']:>5.2f}  yrs {m['pos']} of "
            f"{m['years']}  held {m['held']:>5.1f} sessions ({100 * m['ended']:>3.0f}% stopped trading)  "
            f"a year on the money {100 * m['a_year']:>5.1f}%  worst {100 * m['worst']:>5.0f}%  "
            f"worst 1% {100 * m['worst1']:>5.0f}%  wins {100 * m['wins']:>3.0f}%")  # fmt: skip


def search(name: str = "deals") -> None:
    d = load(name)
    print(f"{len(d['day'])} filings in the universe. Search years 2010 to 2017; buy at the open after R.")
    passed = []
    for kind, size, hold in CELLS:
        m = measure(d, pick(d, kind, size, "search"), hold)
        label = f"{kind} {size} {hold}"
        print(show(label, m))
        if kind != "unpinned" and m["n"] >= 100 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 7:
            passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(kind, size, hold, name: str = "deals") -> None:
    d = load(name)
    for period in ("early", "late"):
        keep = pick(d, kind, size, period)
        print(show(f"{kind} {size} {hold} {period}", measure(d, keep, int(hold))))
        net = d[f"g{hold}"].astype(float) - d["cost"]
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "table":
        table()
    elif command == "search":
        search(*sys.argv[2:3])
    else:
        test(*sys.argv[2:5])
