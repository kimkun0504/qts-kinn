"""Family swing_short (strategies/short_search/HYPOTHESIS.md): events to sell short at the
next open and buy back at the close 5 or 15 sessions later.

    cd research/claude
    uv run python short_search.py search            # the 24 cells on 2010 to 2017
    uv run python short_search.py test given_back small 15   # one cell on the test years
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import AUCTION, weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

BORROW = 0.10  # a year, on the position, for the sessions held
UNIVERSE = "mcap >= 5e7 and d.close >= 3 and adv >= 1e6"
EVENTS = {
    "earnings_fall": "earn and ret2 <= -0.15 and dvr2 >= 5",
    "given_back": "earn and (1 + ret2) * hc >= 1.15 and ret2 < 0.15 and dvr2 >= 5",
    "no_news_jump": "ret1 >= 0.30 and dvr >= 5 and filings_today = 0 and filings_prev = 0 and not earn",
    "run_up": "ret20 >= 1.0 and high250 > 0",
}
SIZES = {"small": "mcap < 3e8", "mid": "mcap >= 3e8 and mcap < 2e9", "large": "mcap >= 2e9"}
HOLDS = (5, 15)
PERIODS = {
    "search": ("wide", "d.day between DATE '2010-01-04' and DATE '2017-12-08'"),
    "early": ("early", "d.day between DATE '2005-01-03' and DATE '2009-12-08'"),
    "late": ("wide", "d.day between DATE '2018-01-02' and DATE '2022-11-30'"),
    "check": ("wide", "d.day between DATE '2023-01-03' and DATE '2023-10-13'"),
}


def trades(event: str, size: str, hold: int, period: str) -> dict[str, np.ndarray]:
    """Each signal's return to a short seller before costs (`s`), its costs, and the same
    against the average stock."""
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    name, dates = PERIODS[period]
    market = "market_early" if name == "early" else "market"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    table = con.sql(
        f"""select d.day::varchar as day, d.symbol, d.yr,
                   (date_diff('day', DATE '2003-12-29', d.day) // 7) as week,
                   1 - exp(first_day + c_exit{hold} - c_next) as s,
                   exp(first_day + c_exit{hold} - c_next) - 1 - m.mk{hold} as over,
                   {AUCTION} as cost
            from read_parquet('{base}/{name}_*.parquet') d
            left join '{base}/{market}.parquet' m using (day)
            join (select permaticker, date, high / close as hc
                  from read_parquet('{store.root}/panel/*.parquet')) p
              on p.permaticker = d.permaticker and p.date = d.day
            where {dates} and next_open is not null and {UNIVERSE}
              and ({SIZES[size]}) and ({EVENTS[event]})"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def measure(d: dict[str, np.ndarray], hold: int) -> dict:
    n = len(d["s"])
    if n < 3:
        return {"n": n}
    fee = BORROW * hold / 252
    before_fee = d["s"] - d["cost"]
    net = before_fee - fee
    mean, t, _ = weekly(net, d["week"])
    years = sorted(set(d["yr"]))
    positive = sum(net[d["yr"] == y].mean() > 0 for y in years)
    return {"n": n, "gross": d["s"].mean(), "net": net.mean(), "weekly": mean, "t": t,
            "years": f"{positive} of {len(years)}", "over": -d["over"].mean(),
            "breakeven": before_fee.mean() * 252 / hold, "worst": net.min(),
            "worst1": np.sort(net)[: max(1, n // 100)].mean(), "winners": (net > 0).mean()}  # fmt: skip


def show(label: str, m: dict) -> None:
    if m["n"] < 3:
        print(f"{label:<28} {m['n']:>5}  too few")
        return
    print(f"{label:<28} {m['n']:>5}  gross {100 * m['gross']:>6.2f}%  net {100 * m['net']:>6.2f}%  "
          f"t {m['t']:>5.2f}  yrs {m['years']:>7}  vs stocks {100 * m['over']:>6.2f}%  "
          f"fee to break even {100 * m['breakeven']:>5.0f}%  worst {100 * m['worst']:>6.0f}%  "
          f"worst 1% {100 * m['worst1']:>6.0f}%  wins {100 * m['winners']:>3.0f}%")  # fmt: skip


def search() -> None:
    print("Short at the next open, cover at the close after 5 or 15 sessions. 2010 to 2017.")
    print(
        f"Net is after the auction allowance, commission and a borrow fee of {BORROW:.0%} a year."
    )
    for event in EVENTS:
        for size in SIZES:
            for hold in HOLDS:
                m = measure(trades(event, size, hold, "search"), hold)
                show(f"{event} {size} {hold}", m)
                if (
                    m["n"] >= 150
                    and m["net"] >= 0.02
                    and m["t"] >= 3
                    and m["over"] > 0
                    and int(m["years"].split()[0]) >= 6
                ):
                    print("    ^ meets the search bar")


def test(event: str, size: str, hold: int, periods=("early", "late")) -> None:
    for period in periods:
        d = trades(event, size, hold, period)
        show(f"{event} {size} {hold} {period}", measure(d, hold))
        fee = BORROW * hold / 252
        for year in sorted(set(d["yr"])):
            pick = d["yr"] == year
            print(
                f"    {year}: {pick.sum():>4}  {100 * (d['s'][pick] - d['cost'][pick] - fee).mean():>6.2f}%"
            )


if __name__ == "__main__":
    if sys.argv[1] == "search":
        search()
    else:
        test(sys.argv[2], sys.argv[3], int(sys.argv[4]), tuple(sys.argv[5:]) or ("early", "late"))
