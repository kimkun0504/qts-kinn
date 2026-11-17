"""strategies/stake_filings/HYPOTHESIS.md: buying after an initial Schedule 13D (13G as the
control). Needs the owner's `download_edgar_times.py --what other`.

    cd research/claude
    uv run python stake_filings.py table
    uv run python stake_filings.py search
    uv run python stake_filings.py test "SC 13D" small up2 40
"""

from __future__ import annotations

import sys
import tempfile
from collections import Counter

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_earnings import AUCTION, weekly

import sec_times
import swing_overnight as so
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

FORMS = ("SC 13D", "SC 13G")
SIZES = {"small": (5e7, 3e8), "mid": (3e8, 2e9), "large": (2e9, 1e18)}
REACTIONS = {"any": lambda d: np.ones(len(d["ret1"]), bool),
             "up2": lambda d: d["ret1"] >= 0.02,
             "up5": lambda d: (d["ret1"] >= 0.05) & (d["dvr"] >= 2)}  # fmt: skip
HOLDS = {15: 0.02, 40: 0.04}  # the hold in sessions and the search bar's mean after costs
PERIODS = {"search": (2010, 2017), "early": (2005, 2009), "late": (2018, 2022), "check": (2023, 2023)}
MAX_A_YEAR = 6


def events_path(name: str = "stakes"):
    return load_settings().data_dir / "research" / "swing" / f"{name}.parquet"


def table() -> None:
    """(stock, R, form) for every initial 13D and 13G: R is the first session whose close
    comes after the SEC accepted it. Companies with more than six initial 13Ds in a calendar
    year are left out (they are mostly filers about others, not subjects)."""
    stocks, days = sec_times.numbers(), sec_times.sessions()
    rows, a_year = [], Counter()
    for row in sec_times.filings("other_forms.jsonl.gz"):
        if row["form"] not in FORMS or row["cik"] not in stocks:
            continue
        when = sec_times.accepted(row)
        session = sec_times.reaction_session(days, when) if when else None
        if session:
            rows.append((row["cik"], session, row["form"]))
            if row["form"] == "SC 13D":
                a_year[(row["cik"], session.year)] += 1
    busy = {cik for (cik, _), n in a_year.items() if n > MAX_A_YEAR}
    found = {(p, session, form) for cik, session, form in rows if cik not in busy for p in stocks[cik]}
    pq.write_table(pa.table({"permaticker": [k[0] for k in found], "day": [k[1] for k in found],
                             "form": [k[2] for k in found]}), events_path())  # fmt: skip
    print(f"{len(found)} filings ({Counter(k[2] for k in found)}); {len(busy)} companies left out as filers")


def load(name: str = "stakes") -> dict[str, np.ndarray]:
    """Every event in the universe with its returns from the next open to the close 15 and
    40 sessions after R, its costs, and the index fund over the same days."""
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'")
    parts = []
    for tables in ("early", "wide"):
        parts.append(
            f"""select d.day, d.yr, (date_diff('day', DATE '2003-12-29', d.day) // 7) as week,
                       f.form, d.mcap, d.ret1, d.dvr, d.sector, {AUCTION} as cost,
                       exp(d.first_day + d.c_exit15 - d.c_next) - 1 as g15,
                       exp(p.c40 - p.c_next) / p.next_oc - 1 as g40, p.d15, p.d40, p.d1
                from read_parquet('{base}/{tables}_*.parquet') d
                join '{events_path(name)}' f on f.permaticker = d.permaticker and f.day = d.day
                join (select permaticker, date, lead(c) over w as c_next,
                             lead(open / close) over w as next_oc, lead(date) over w as d1,
                             last_value(c) over (partition by permaticker order by date
                                                 rows between current row and 40 following) as c40,
                             last_value(date) over (partition by permaticker order by date
                                                    rows between current row and 15 following) as d15,
                             last_value(date) over (partition by permaticker order by date
                                                    rows between current row and 40 following) as d40
                      from (select permaticker, date, open, close,
                                   sum(ln(close / prev_close)) over (partition by permaticker order by date) as c
                            from read_parquet('{store.root}/panel/*.parquet')
                            where prev_close > 0 and close > 0 and low > 0 and open > 0
                              and category like '%Common Stock%')
                      window w as (partition by permaticker order by date)) p
                  on p.permaticker = d.permaticker and p.date = d.day
                where d.day between DATE '2005-01-03' and DATE '2023-10-13' and d.next_open is not null
                  and coalesce(d.sector, '') <> 'Financial Services'"""
        )
    table = con.sql(" union all ".join(parts)).to_arrow_table()
    d = {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}
    # The index fund from the open of R+1 to the close of the exit day.
    fund = so.index()
    days = sorted(fund)
    place = {day: i for i, day in enumerate(days)}
    growth = np.cumsum([np.log1p(fund[day]["day"]) for day in days])
    for hold in HOLDS:
        over = np.full(len(d["day"]), np.nan)
        pairs = zip(d["d1"].astype(object), d[f"d{hold}"].astype(object), strict=True)
        for i, (first, last) in enumerate(pairs):
            if first in place and last in place and place[last] >= place[first]:
                a, b = place[first], place[last]
                over[i] = (1 + fund[first]["first"]) * np.exp(growth[b] - growth[a]) - 1
        d[f"iwm{hold}"] = over
    return d


def pick(d, form, size, reaction, period):
    small, big = SIZES[size]
    first, last = PERIODS[period]
    return ((d["form"] == form) & (d["mcap"] >= small) & (d["mcap"] < big) & REACTIONS[reaction](d)
            & (d["yr"] >= first) & (d["yr"] <= last))  # fmt: skip


def measure(d, keep, hold) -> dict:
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    gross = d[f"g{hold}"][keep].astype(float)
    net = gross - d["cost"][keep]
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    positive = sum(net[years == y].mean() > 0 for y in set(years))
    return {"n": n, "gross": gross.mean(), "net": net.mean(), "t": t, "pos": positive,
            "years": len(set(years)), "over": np.nanmean(gross - d[f"iwm{hold}"][keep]),
            "wins": (net > 0).mean()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:34} {m['n']:>6}"
    return (f"{label:34} {m['n']:>6}  gross {100 * m['gross']:>6.2f}%  net {100 * m['net']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  over IWM {100 * m['over']:>6.2f}%  "
            f"wins {100 * m['wins']:>3.0f}%")  # fmt: skip


def cells():
    for size in SIZES:
        for reaction in REACTIONS:
            for hold in HOLDS:
                yield "SC 13D", size, reaction, hold
    for size in SIZES:
        for hold in HOLDS:
            yield "SC 13G", size, "any", hold


def search(name: str = "stakes") -> None:
    d = load(name)
    print(f"{len(d['day'])} filings in the universe. Search years 2010 to 2017; buy at the open after R.")
    passed = []
    for form, size, reaction, hold in cells():
        m = measure(d, pick(d, form, size, reaction, "search"), hold)
        label = f"{form} {size} {reaction} {hold}"
        print(show(label, m))
        if (m["n"] >= 150 and m["net"] >= HOLDS[hold] and m["t"] >= 3 and m["pos"] >= 6
                and m["over"] >= 0.01):  # fmt: skip
            passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(form, size, reaction, hold, name: str = "stakes") -> None:
    d = load(name)
    for period in ("early", "late"):
        keep = pick(d, form, size, reaction, period)
        print(show(f"{form} {size} {reaction} {hold} {period}", measure(d, keep, int(hold))))
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
        test(*sys.argv[2:6])
