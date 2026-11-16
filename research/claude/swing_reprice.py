"""Re-price a rule's swing trades from minute bars (addendum of 2026-11-16 in
strategies/swing_search/HYPOTHESIS.md): buy at the volume-weighted price of 09:30 to 10:00 on
the entry day and sell at that of the last 30 minutes on the exit day, instead of the single
opening and closing prints of the daily bar. Also records how much traded in those windows.

    uv run python research/claude/swing_reprice.py A early    # builds, then reports
"""

from __future__ import annotations

import sys
import tempfile
from collections import defaultdict

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from swing_early import PERIODS, RULES
from swing_earnings import AUCTION, weekly

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

HOLD = 15


def trades(con, store, base, rule: str, period: str) -> list[dict]:
    name, dates = PERIODS[period]
    rows = con.sql(
        f"""with p as (
                select permaticker, date as day, lead(date) over w as day_in,
                       lead(symbol) over w as symbol_in, lead(open) over w as open_in,
                       last_value(date) over x as day_out, last_value(symbol) over x as symbol_out,
                       last_value(close) over x as close_out
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'
                window w as (partition by permaticker order by date),
                       x as (partition by permaticker order by date
                             rows between 1 following and {HOLD} following))
            select d.day, d.symbol, d.permaticker, d.yr, d.adv, d.mcap, d.close,
                   (date_diff('day', DATE '2003-12-29', d.day) // 7) as week,
                   exp(first_day + c_exit{HOLD} - c_next) - 1 as g, {AUCTION} as cost,
                   2 * (half_spread + commission) as cost1,
                   p.day_in, p.symbol_in, p.open_in, p.day_out, p.symbol_out, p.close_out
            from read_parquet('{base}/{name}_*.parquet') d join p using (permaticker, day)
            where {dates} and next_open is not null and ({RULES.get(rule, rule)})
            order by d.day, d.symbol"""
    )
    names = rows.columns
    return [dict(zip(names, r, strict=True)) for r in rows.fetchall()]


def windows(con, store, day, symbols: set[str]) -> dict[str, dict]:
    """Per symbol: volume-weighted price and dollars traded, first and last 30 minutes."""
    path = store.bars_root / "minute" / f"year={day.year}" / f"{day.isoformat()}.parquet"
    if not path.exists():
        return {}
    listed = ", ".join("'" + s.replace("'", "''") + "'" for s in symbols)
    rows = con.sql(
        f"""with b as (select symbol, minute_et as m, (high + low + close) / 3 * volume as dv,
                              volume, open, transactions,
                              (select case when max(minute_et) filter (minute_et < 960) <= 780
                                           then 780 else 960 end from read_parquet('{path}')) as shut
                       from read_parquet('{path}') where symbol in ({listed}))
            select symbol,
                   sum(dv) filter (m >= 570 and m < 600)
                       / nullif(sum(volume) filter (m >= 570 and m < 600), 0) as vwap_in,
                   sum(dv) filter (m >= 570 and m < 600) as dollars_in,
                   sum(dv) filter (m = 570) as dollars_first,
                   sum(transactions) filter (m = 570) as trades_first,
                   sum(dv) filter (m >= shut - 30 and m < shut)
                       / nullif(sum(volume) filter (m >= shut - 30 and m < shut), 0) as vwap_out,
                   sum(dv) filter (m >= shut - 30 and m < shut) as dollars_out,
                   sum(dv) filter (m = shut - 1) as dollars_last
            from b group by 1"""
    )
    names = rows.columns
    return {r[0]: dict(zip(names, r, strict=True)) for r in rows.fetchall()}


def build(rule: str, period: str, target) -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    found = trades(con, store, base, rule, period)
    need: dict = defaultdict(set)
    for t in found:
        need[t["day_in"]].add(t["symbol_in"])
        need[t["day_out"]].add(t["symbol_out"])
    seen = {day: windows(con, store, day, symbols) for day, symbols in sorted(need.items())}
    for t in found:
        first = seen[t["day_in"]].get(t["symbol_in"], {})
        last = seen[t["day_out"]].get(t["symbol_out"], {})
        for key in ("vwap_in", "dollars_in", "dollars_first", "trades_first"):
            t[key] = first.get(key)
        for key in ("vwap_out", "dollars_out", "dollars_last"):
            t[key] = last.get(key)
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(found), target)


def report(target, label: str) -> None:
    t = pq.read_table(target).to_pydict()
    col = {k: np.array([np.nan if x is None else x for x in v], dtype=float)
           for k, v in t.items() if k not in ("day", "symbol", "day_in", "symbol_in", "day_out",
                                              "symbol_out")}  # fmt: skip
    g, cost = col["g"], col["cost"]
    has = ~np.isnan(col["vwap_in"]) & ~np.isnan(col["vwap_out"])
    ratio_in = np.where(np.isnan(col["vwap_in"]), 1.0, col["vwap_in"] / col["open_in"])
    ratio_out = np.where(np.isnan(col["vwap_out"]), 1.0, col["vwap_out"] / col["close_out"])
    v = (1 + g) / ratio_in * ratio_out - 1
    print(f"{label}: {len(g)} trades; both windows traded in {100 * has.mean():.1f}%")
    print(f"  entry: 30-minute price over the opening print, mean {100 * (ratio_in - 1).mean():+.2f}%"
          f", median {100 * np.median(ratio_in - 1):+.2f}%; exit: 30-minute price over the closing "
          f"print, mean {100 * (ratio_out - 1).mean():+.2f}%, median "
          f"{100 * np.median(ratio_out - 1):+.2f}%")  # fmt: skip
    for name, values in (("opening and closing prints", g), ("30-minute prices", v)):
        net = values - cost
        mean, tstat, weeks = weekly(net, col["week"])
        print(f"  {name:27}: gross {100 * values.mean():5.2f}%  after auction-basis costs "
              f"{100 * net.mean():5.2f}%  after the spread crossed {100 * (values - col['cost1']).mean():5.2f}%"
              f"  weekly t {tstat:5.2f} ({weeks} weeks)  winners {100 * (net > 0).mean():.0f}%"
              f"  median {100 * np.median(net):5.2f}%")  # fmt: skip
    q = lambda x, p: np.nanquantile(x, p)  # noqa: E731
    print(f"  traded 09:30-10:00 on the entry day: median ${q(col['dollars_in'], 0.5):,.0f}, "
          f"10th percentile ${q(col['dollars_in'], 0.1):,.0f}; in the 09:30 minute: median "
          f"${q(col['dollars_first'], 0.5):,.0f}, 10th ${q(np.nan_to_num(col['dollars_first']), 0.1):,.0f}"
          f"; last 30 minutes of the exit day: median ${q(col['dollars_out'], 0.5):,.0f}, 10th "
          f"${q(np.nan_to_num(col['dollars_out']), 0.1):,.0f}")  # fmt: skip
    years = col["yr"]
    for y in sorted(set(years)):
        m = years == y
        print(f"  {int(y)}: {m.sum():4d} trades  prints {100 * (g[m] - cost[m]).mean():6.2f}%  "
              f"30-minute prices {100 * (v[m] - cost[m]).mean():6.2f}%")  # fmt: skip


if __name__ == "__main__":
    rule, period = sys.argv[1], sys.argv[2]
    out = load_settings().data_dir / "research" / "swing" / "reprice" / f"{rule}_{period}.parquet"
    if not out.exists():
        build(rule, period, out)
    report(out, f"rule {rule}, {period}")
