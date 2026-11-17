"""Family 23 (addendum of 2026-11-17 14:41 ET in strategies/swing_search/HYPOTHESIS.md):
buying during the first session after an earnings report instead of at the next open.

    uv run python research/claude/swing_intraday_entry.py candidates
    uv run python research/claude/swing_intraday_entry.py collect 2005 2009   # by year, resumable
    uv run python research/claude/swing_intraday_entry.py report
"""

from __future__ import annotations

import sys
import tempfile
from collections import defaultdict

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

FIRST, LAST = "2005-01-03", "2023-10-13"
JUMP, VOLUME, HOLD = 0.15, 5.0, 15
OPEN, CLOSE = 570, 960  # 09:30 and 16:00 as minutes of the day
CHECKPOINTS = {"09:35": 575, "10:00": 600, "11:00": 660, "13:00": 780, "15:30": 930}
CELLS = [*CHECKPOINTS, "first touch"]
SPANS = [("2005-2009", 2005, 2009, None), ("2010-2017", 2010, 2017, None),
         ("2018-2023", 2018, 2023, None), ("2018-2023 without 2020", 2018, 2023, 2020)]  # fmt: skip


def folder(settings):
    out = settings.data_dir / "research" / "swing" / "intraday_entry"
    out.mkdir(parents=True, exist_ok=True)
    return out


def candidates() -> None:
    """Every session after an earnings 8-K in the universe whose high reached the jump, with
    the daily figures the trigger and the returns need (prices as log levels, so splits do
    not matter)."""
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    con.execute(
        f"""copy (
            with p as (
                select permaticker, date, symbol, open, high, close, dollar_volume as dv,
                       adv20_prev as adv, marketcap_prev as mcap,
                       sum(ln(close / prev_close)) over w as c
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'
                window w as (partition by permaticker order by date)),
            q as (
                select *, lag(c, 2) over w as c2,
                       lag(dv) over w / nullif(lag(adv) over w, 0) as dvr_prev,
                       last_value(c) over (partition by permaticker order by date
                                           rows between current row and {HOLD} following) as c_exit,
                       lead(c) over w as c_next, lead(open) over w / lead(close) over w as next_open
                from p
                window w as (partition by permaticker order by date)),
            e as (select permaticker, day from '{base}/earn.parquet'
                  union select permaticker, day from '{base}/earn_early.parquet')
            select q.date as day, q.symbol, q.permaticker, q.close, q.adv, q.mcap, q.c, q.c2,
                   q.dvr_prev, q.dv / nullif(q.adv, 0) as dvr, q.c_exit, q.c_next, q.next_open
            from q join e on e.permaticker = q.permaticker and e.day = q.date
            where q.date between DATE '{FIRST}' and DATE '{LAST}'
              and q.mcap >= 5e7 and q.mcap < 3e8 and q.adv >= 250000 and q.c2 is not null
              and exp(q.c + ln(q.high / q.close) - q.c2) >= {1 + JUMP}
            order by day, symbol
        ) to '{folder(settings)}/candidates.parquet' (format parquet)"""
    )
    rows = con.sql(
        f"select count(*), count(distinct day) from '{folder(settings)}/candidates.parquet'"
    ).fetchall()[0]
    print(f"{rows[0]} candidate sessions on {rows[1]} days")


def fire(minute, price, volume, adv, level, dvr_prev, before):
    """Whether the trigger holds on the last bar before `before`, and that bar's index."""
    k = int(np.searchsorted(minute, before)) - 1
    if k < 0:
        return False
    dollars = float(np.dot(price[: k + 1], volume[: k + 1]))
    return price[k] >= 1 and level * price[k] >= 1 + JUMP and max(dvr_prev, dollars / adv) >= VOLUME


def entry(minute, opens, at):
    """The open of the first bar from `at`, if one prints within 10 minutes and before the close."""
    k = int(np.searchsorted(minute, at))
    if k >= len(minute) or minute[k] > at + 10 or minute[k] >= CLOSE:
        return None
    return float(opens[k]), int(minute[k])


def collect(first: int, last: int) -> None:
    settings = load_settings()
    store = DataStore(settings)
    out = folder(settings)
    table = pq.read_table(out / "candidates.parquet").to_pylist()
    by_day = defaultdict(list)
    for row in table:
        by_day[row["day"]].append(row)
    for year in range(first, last + 1):
        target = out / f"entries_{year}.parquet"
        if target.exists():
            continue
        found = []
        for day in sorted(d for d in by_day if d.year == year):
            rows = by_day[day]
            try:
                bars = store.minute(day, symbols=[r["symbol"] for r in rows],
                                    columns="symbol, minute_et, open, close, volume")  # fmt: skip
            except FileNotFoundError:
                continue
            symbol = bars.column("symbol").to_pylist()
            cols = {
                n: bars.column(n).to_numpy(zero_copy_only=False)
                for n in ("minute_et", "open", "close", "volume")
            }
            where = defaultdict(list)
            for i, s in enumerate(symbol):
                where[s].append(i)
            for r in rows:
                idx = where.get(r["symbol"])
                if not idx:
                    continue
                minute, opens, price, volume = (
                    cols[n][idx[0] : idx[-1] + 1].astype(float)
                    for n in ("minute_et", "open", "close", "volume")
                )
                regular = np.flatnonzero((minute >= OPEN) & (minute <= CLOSE))
                if not len(regular):
                    continue
                last_price = price[regular[-1]]
                # The stock's level against the close of S-2 for one dollar of the minute price.
                level = float(np.exp(r["c"] - r["c2"])) / last_price
                for cell in CELLS:
                    if cell == "first touch":
                        got = None
                        for k in np.flatnonzero(
                            (minute >= CHECKPOINTS["09:35"] - 1) & (minute < CHECKPOINTS["15:30"])
                        ):
                            if fire(
                                minute,
                                price,
                                volume,
                                r["adv"],
                                level,
                                r["dvr_prev"] or 0.0,
                                minute[k] + 1,
                            ):
                                got = entry(minute, opens, minute[k] + 1)
                                break
                    else:
                        at = CHECKPOINTS[cell]
                        got = (
                            entry(minute, opens, at)
                            if fire(
                                minute, price, volume, r["adv"], level, r["dvr_prev"] or 0.0, at
                            )
                            else None
                        )
                    if got:
                        found.append({"day": day, "symbol": r["symbol"], "cell": cell,
                                      "minute": got[1],
                                      "paid": got[0], "rel": got[0] / last_price})  # fmt: skip
        pq.write_table(
            pa.Table.from_pylist(found)
            if found
            else pa.table(
                {"day": [], "symbol": [], "cell": [], "minute": [], "paid": [], "rel": []}
            ),
            target,
        )
        print(f"{year}: {len(found)} entries", flush=True)


def allow(adv: float) -> float:
    return 0.0025 if adv < 1e6 else 0.0010 if adv < 1e7 else 0.0005 if adv < 1e8 else 0.0002


def spread(adv: float) -> float:
    return 0.0100 if adv < 1e6 else 0.0043 if adv < 1e7 else 0.0018 if adv < 1e8 else 0.0005


def commission(price: float) -> float:
    return min(0.01, max(0.000175, 0.0035 / price))


def line(label: str, values) -> str:
    values = np.asarray(values, float)
    if not len(values):
        return f"    {label:<34} none"
    t = (
        values.mean() / (values.std(ddof=1) / np.sqrt(len(values)))
        if len(values) > 2
        else float("nan")
    )
    mean, wins = 100 * values.mean(), 100 * (values > 0).mean()
    return (f"    {label:<34} {len(values):>5}  mean {mean:>6.2f}%  t {t:>5.2f}  "
            f"winners {wins:>3.0f}%")  # fmt: skip


def report() -> None:
    settings = load_settings()
    out = folder(settings)
    con = duckdb.connect()
    cand = {
        (r["day"], r["symbol"]): r for r in pq.read_table(out / "candidates.parquet").to_pylist()
    }
    entries = (
        con.sql(f"select * from read_parquet('{out}/entries_*.parquet')")
        .to_arrow_table()
        .to_pylist()
    )
    # A50 as it stands: its test at the close, bought at the next open, the auction allowance
    # both ways.
    a50 = {}
    for key, r in cand.items():
        heavy = max(r["dvr"] or 0, r["dvr_prev"] or 0) >= VOLUME
        if (np.exp(r["c"] - r["c2"]) - 1 >= JUMP and heavy
                and r["close"] >= 1 and r["next_open"] is not None):  # fmt: skip
            gross = float(np.exp(r["c_exit"] - r["c_next"]) / r["next_open"]) - 1
            a50[key] = (gross, gross - 2 * (allow(r["adv"]) + commission(r["close"])))
    print(f"A50 as it stands: {len(a50)} signals")
    for label, lo, hi, skip in SPANS:
        keys = [k for k in a50 if lo <= k[0].year <= hi and k[0].year != skip]
        print(line(f"{label}, after costs", [a50[k][1] for k in keys]))
    for cell in CELLS:
        rows = [e for e in entries if e["cell"] == cell]
        keys = {(e["day"], e["symbol"]) for e in rows}
        shared = len(keys & set(a50))
        also, caught = 100 * shared / max(len(keys), 1), 100 * shared / len(a50)
        print(f"\n{cell}: {len(rows)} entries, {also:.0f}% also A50 signals at the close; "
              f"A50 signals caught {caught:.0f}%")  # fmt: skip
        for label, lo, hi, skip in SPANS:
            both, early, late, failed, gross = [], [], [], [], []
            for e in rows:
                key = (e["day"], e["symbol"])
                if not (lo <= key[0].year <= hi) or key[0].year == skip:
                    continue
                r = cand[key]
                g = float(np.exp(r["c_exit"] - r["c"])) / e["rel"] - 1
                net = (
                    g
                    - spread(r["adv"])
                    - commission(e["paid"])
                    - allow(r["adv"])
                    - commission(e["paid"])
                )
                gross.append(g)
                early.append(net)
                if key in a50:
                    both.append(net)
                    late.append(a50[key][1])
                else:
                    failed.append(net)
            print(f"  {label}")
            print(line("before costs", gross))
            print(line("after costs", early))
            print(line("  where A50 also buys: early", both))
            print(line("  the same, bought at A50's time", late))
            print(line("  fails A50's test at the close", failed))


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "candidates":
        candidates()
    elif command == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    else:
        report()
