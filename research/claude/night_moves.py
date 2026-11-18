"""strategies/night_bids/HYPOTHESIS.md, addendum "trading with the move": after a rise or a
fall after hours with real trading and no results due, trade in the next minute.

    cd research/claude
    uv run python night_moves.py collect 2005 2023
    uv run python night_moves.py search
    uv run python night_moves.py test up 5 mid open
"""

from __future__ import annotations

import sys

import duckdb
import numpy as np
from swing_earnings import weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from night_bids import DEPTHS, FIRST, LAST, MIN_DOLLARS, MIN_TRADES, PERIODS, SIZES, connect, folder, pick

SIDES = {"up": ("low", ">", 1), "dn": ("high", "<", -1)}
EXITS = {"up": ("open", "close"), "dn": ("open",)}
BORROW_NIGHT = 0.10 / 252


def keys():
    return [(side, x) for side in SIDES for x in DEPTHS]


def beyond(side: str, x: int) -> str:
    column, op, sign = SIDES[side]
    return f"{column} {op} ref * {1 + sign * x / 100}"


def collect(first: int, last: int) -> None:
    store = DataStore(load_settings())
    out = folder()
    con = connect()
    running = ", ".join(
        f"""sum(case when {beyond(s, x)} then transactions else 0 end) over w as t_{s}{x},
            sum(case when {beyond(s, x)} then close * volume else 0 end) over w as d_{s}{x}"""
        for s, x in keys()
    )
    signal = ", ".join(
        f"min(minute_et) filter (where t_{s}{x} >= {MIN_TRADES} and d_{s}{x} >= {MIN_DOLLARS}) as at_{s}{x}"
        for s, x in keys()
    )
    entry = ", ".join(
        f"""min(r.minute_et) filter (where r.minute_et > at_{s}{x}) as m_{s}{x},
            arg_min(r.{'high' if s == 'up' else 'low'}, r.minute_et) filter (where r.minute_et > at_{s}{x}) as p_{s}{x},
            arg_min(r.close * r.volume, r.minute_et) filter (where r.minute_et > at_{s}{x}) as b_{s}{x}"""
        for s, x in keys()
    )
    for year in range(first, last + 1):
        target = out / f"moves_{year}.parquet"
        if target.exists():
            continue
        files = str(store.bars_roots[0] / "minute" / f"year={year}" / "*.parquet")
        con.execute(
            f"""create or replace temp table bars as
                select b.symbol, b.day, minute_et, high, low, b.close, volume, transactions, d.ref
                from (select symbol, cast(regexp_extract(filename, '(\\d{{4}}-\\d{{2}}-\\d{{2}})\\.parquet', 1) as date) as day,
                             minute_et, high, low, close, volume, transactions
                      from read_parquet('{files}', filename = true)
                      where minute_et between 955 and {LAST}) b
                join '{out}/daily.parquet' d on d.day = b.day and d.symbol = b.symbol"""
        )
        con.execute(
            f"""create or replace temp table moved as
                select day, symbol, min(abs(close / ref - 1)) filter (where minute_et <= 960) as close_gap
                from bars group by 1, 2
                having count(*) filter (where minute_et >= {FIRST} and (low > ref * 1.03 or high < ref * 0.97)) > 0"""
        )
        con.execute(
            f"""copy (
                with r as (
                    select b.*, {running} from bars b join moved using (day, symbol)
                    where minute_et >= {FIRST}
                    window w as (partition by b.day, b.symbol order by minute_et)),
                s as (select day, symbol, {signal} from r group by 1, 2),
                e as (select r.day, r.symbol, {", ".join(f"any_value(at_{s}{x}) as at_{s}{x}" for s, x in keys())},
                             {entry}
                      from r join s on s.day = r.day and s.symbol = r.symbol group by 1, 2)
                select e.*, m.close_gap, d.permaticker, d.ref, d.mcap, d.adv, d.to_open, d.to_close
                from e join moved m using (day, symbol) join '{out}/daily.parquet' d using (day, symbol)
                where coalesce({", ".join(f"m_{s}{x}" for s, x in keys())}) is not null
            ) to '{target}' (format parquet)"""
        )
        print(year, con.sql(f"select count(*) from '{target}'").fetchall()[0][0], flush=True)


def load(side: str, x: int) -> dict[str, np.ndarray]:
    out = folder()
    k = f"{side}{x}"
    gain = ("d.to_{e} / (f.p_" + k + " / f.ref) - 1") if side == "up" else ("1 - d.to_{e} / (f.p_" + k + " / f.ref)")
    borrow = BORROW_NIGHT if side == "dn" else 0.0
    table = duckdb.sql(
        f"""with f as (select * from read_parquet('{out}/moves_*.parquet')
                       where m_{k} is not null and m_{k} <= at_{k} + 20 and close_gap <= 0.02 and p_{k} >= 1),
            e as (select permaticker, day, min("at") as filed_at from '{out}/evening_filings.parquet' group by 1, 2)
            select f.day, f.symbol, year(f.day) as yr, (date_diff('day', DATE '2003-12-29', f.day) // 7) as week,
                   f.mcap, f.at_{k} as signal_at, f.b_{k} as bar_dollars, f.p_{k} / f.ref - 1 as moved,
                   {gain.format(e="open")} as g_open, {gain.format(e="close")} as g_close,
                   case when f.adv < 1e6 then 0.0025 when f.adv < 1e7 then 0.0010
                        when f.adv < 1e8 then 0.0005 else 0.0002 end
                   + 2 * least(0.01, greatest(0.000175, 0.0035 / f.p_{k})) + {borrow} as cost
            from f join '{out}/daily.parquet' d on d.day = f.day and d.symbol = f.symbol
            left join e on e.permaticker = f.permaticker and e.day = f.day
            where not exists (select 1 from '{out}/results_due.parquet' r
                              where r.permaticker = f.permaticker and r.day = f.day)
              and (e.filed_at is null or e.filed_at > f.at_{k})
            order by f.day, f.symbol"""
    ).to_arrow_table()
    return {n: table.column(n).to_numpy(zero_copy_only=False) for n in table.column_names}


def measure(d, keep, exit_) -> dict:
    n = int(keep.sum())
    if n < 3:
        return {"n": n}
    net = d[f"g_{exit_}"][keep].astype(float) - d["cost"][keep]
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    ordered = np.sort(net)
    return {"n": n, "net": net.mean(), "median": np.median(net), "t": t, "wins": (net > 0).mean(),
            "pos": sum(net[years == y].mean() > 0 for y in set(years)), "years": len(set(years)),
            "worst": ordered[0], "worst1": ordered[: max(1, n // 100)].mean(),
            "moved": np.median(d["moved"][keep]), "thin": (d["bar_dollars"][keep] < 5000).mean()}  # fmt: skip


def show(label, m) -> str:
    if m["n"] < 3:
        return f"{label:22} {m['n']:>6}"
    return (f"{label:22} {m['n']:>6}  net {100 * m['net']:>6.2f}%  median {100 * m['median']:>6.2f}%  "
            f"t {m['t']:>5.2f}  yrs {m['pos']} of {m['years']}  wins {100 * m['wins']:>3.0f}%  "
            f"worst {100 * m['worst']:>5.0f}%  worst 1% {100 * m['worst1']:>4.0f}%  "
            f"at {100 * m['moved']:>5.1f}%  thin minute {100 * m['thin']:>3.0f}%")  # fmt: skip


def search() -> None:
    passed = []
    for side, x in keys():
        d = load(side, x)
        for size in SIZES:
            keep = pick(d, size, "search")
            for exit_ in EXITS[side]:
                m = measure(d, keep, exit_)
                label = f"{side} {x}% {size} {exit_}"
                print(show(label, m))
                if m["n"] >= 150 and m["net"] >= 0.01 and m["t"] >= 3 and m["pos"] >= 6:
                    passed.append(label)
    print("\nMeet the search bar:", passed or "none")


def test(side, x, size, exit_) -> None:
    d = load(side, int(x))
    net = d[f"g_{exit_}"].astype(float) - d["cost"]
    for period in ("early", "late"):
        keep = pick(d, size, period)
        print(show(f"{side} {x}% {size} {exit_} {period}", measure(d, keep, exit_)))
        for year in sorted(set(d["yr"][keep])):
            mine = keep & (d["yr"] == year)
            print(f"    {year}: {mine.sum():>5}  {100 * net[mine].mean():>6.2f}%")


if __name__ == "__main__":
    if sys.argv[1] == "collect":
        collect(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "search":
        search()
    else:
        test(*sys.argv[2:6])
