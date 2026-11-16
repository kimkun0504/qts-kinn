"""The overnight search (strategies/recent_search/HYPOTHESIS.md). Each family is a grid of
conditions; every cell is measured on 2018-2022 only, net of costs at twice the modelled
spread, long (and short for information). The check on 2023 is a separate, explicit call.

    uv run python research/claude/recent_search.py news          # once: the 8-K table
    uv run python research/claude/recent_search.py family 1      # one family (1-8)
    uv run python research/claude/recent_search.py cell <t> "<sql condition>" [--check]
"""

from __future__ import annotations

import argparse
import sys

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

YEARS = (2018, 2019, 2020, 2021, 2022)
CAP = """case when mcap is null then 'cap?' when mcap < 3e8 then 'micro'
              when mcap < 2e9 then 'small' else 'large' end"""
NEWS = "case when earn then 'earnings' when any8k then 'other8k' else 'none' end"


def cut(column: str, edges: list[float], unit: float = 100.0) -> str:
    """A bucket label for `column` from ascending edges, e.g. '<-10', '-10..-5', '>=20'."""
    parts = [
        f"when {column} is null then null",
        f"when {column} < {edges[0]} then '<{edges[0] * unit:g}'",
    ]
    for a, b in zip(edges, edges[1:], strict=False):
        parts.append(f"when {column} < {b} then '{a * unit:g}..{b * unit:g}'")
    return "case " + " ".join(parts) + f" else '>={edges[-1] * unit:g}' end"


FAMILIES = {
    1: (575, "abs(gap) >= 0.05", {
        "gap": cut("gap", [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20, 0.50]), "news": NEWS,
        "premarket": cut("pm_part", [0.02, 0.20]), "cap": CAP}),
    2: (600, "abs(drv600) >= 0.02", {
        "drive": cut("drv600", [-0.10, -0.05, -0.02, 0.02, 0.05, 0.10]),
        "rvol": cut("rvol600", [2, 5], 1), "tradesize": cut("size600", [0.7, 1.5], 1),
        "cap": CAP}),
    3: (None, "abs(mov{t}) >= 0.05", {
        "move": cut("mov{t}", [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]),
        "rvol": cut("rvol{t}", [2, 5], 1), "cap": CAP}),
    4: (575, "abs(ret1) >= 0.10", {
        "yesterday": cut("ret1", [-0.20, -0.10, 0.10, 0.20]),
        "closed": cut("loc1", [0.25, 0.75], 1), "gap": cut("gap", [-0.01, 0.01]), "cap": CAP}),
    5: (575, "codes is not null", {
        "item": "unnest(codes)", "gap": cut("gap", [-0.02, 0.02]), "cap": CAP}),
    6: (660, "rvol660 >= 2", {
        "vwap": cut("vw660", [-0.03, -0.01, 0.01, 0.03]), "range": cut("pos660", [0.25, 0.75], 1),
        "move": cut("mov660", [-0.02, 0.02])}),
    7: (None, "age <= 20", {
        "age": cut("age", [3, 10], 1), "move": cut("mov{t}", [-0.10, -0.03, 0.03, 0.10])}),
    8: (600, "size600 >= 2 or size600 <= 0.5", {
        "tradesize": cut("size600", [0.33, 0.5, 2, 3], 1), "drive": cut("drv600", [-0.02, 0.02]),
        "cap": CAP}),
}  # fmt: skip
TIMES = {3: (660, 780, 900), 7: (575, 600)}


def connect() -> duckdb.DuckDBPyConnection:
    settings = load_settings()
    base = settings.data_dir / "research" / "recent"
    con = duckdb.connect()
    con.execute("set threads=3; set memory_limit='2500MB'")
    con.execute(
        f"""create view b as
            select x.*, n.codes, coalesce(n.earn, false) as earn,
                   n.codes is not null as any8k
            from read_parquet('{base}/base_*.parquet') x
            left join '{base}/news.parquet' n using (day, permaticker)"""
    )
    return con


def news() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "recent"
    duckdb.sql(
        f"""copy (
            select f.day, f.permaticker,
                   list_distinct(flatten(list(string_split(e.eventcodes, '|')))) as codes,
                   bool_or(regexp_matches('|' || e.eventcodes || '|', '[|]22[|]')) as earn
            from read_parquet('{base}/base_*.parquet') f
            join '{store.root}/master/security_master.parquet' s using (permaticker)
            join '{store.root}/sharadar/events.parquet' e
              on e.ticker = s.ticker and e.date >= f.prev_date and e.date < f.day
            group by 1, 2) to '{base}/news.parquet' (format parquet)"""
    )
    print(duckdb.sql(f"select count(*), sum(earn::int) from '{base}/news.parquet'").fetchall())


def measure(con, t: int, where: str, keys: dict[str, str], years: str) -> list[tuple]:
    names = list(keys)
    exprs = ", ".join(f"{expr.format(t=t)} as {name}" for name, expr in keys.items())
    group = ", ".join(names) if names else "1"
    per_year = ", ".join(
        f"sum(net * n) filter (yr = {y}) / nullif(sum(n) filter (yr = {y}), 0) as y{y}"
        for y in (*YEARS, 2023)
    )
    lead = f"{exprs}," if names else ""
    sql = f"""
        with x as (
            select {lead} day, yr, r{t} as r, 2 * (2 * half_spread + commission) as cost
            from b where ok{t} and r{t} is not null and {years} and ({where.format(t=t)})),
        d as (select {group + "," if names else ""} day, any_value(yr) as yr, count(*) as n,
                     avg(r - cost) as net, avg(-r - cost) as short, avg(r) as gross,
                     avg(case when r - cost > 0 then r - cost end) as win,
                     sum((r - cost > 0)::int) as wins
              from x group by {group + "," if names else ""} day)
        select {group + "," if names else ""} sum(n) as trades, count(*) as days,
               sum(gross * n) / sum(n) as gross, sum(net * n) / sum(n) as net,
               avg(net) / nullif(stddev_samp(net) / sqrt(count(*)), 0) as t,
               sum(short * n) / sum(n) as short,
               avg(short) / nullif(stddev_samp(short) / sqrt(count(*)), 0) as t_short,
               sum(wins) / sum(n) as win_rate, {per_year}
        from d group by {group if names else "()"}"""
    return con.execute(sql).fetchall(), names


def show(rows, names, title: str) -> None:
    k = len(names)
    head = "".join(f"{n:>11}" for n in names)
    print(f"\n{title}\n{head}{'trades':>8}{'gross%':>8}{'net%':>8}{'t':>7}{'short%':>8}"
          f"{'t':>6}{'win':>5}  2018  2019  2020  2021  2022")  # fmt: skip
    for r in rows:
        label = "".join(f"{str(v):>11}" for v in r[:k])
        trades, _, gross, net, t, short, t_short, win, *by_year = r[k:]
        years = " ".join(f"{100 * (v or 0):5.1f}" for v in by_year[:5])
        print(f"{label}{trades:>8.0f}{100 * gross:>8.2f}{100 * net:>8.2f}{t or 0:>7.1f}"
              f"{100 * short:>8.2f}{t_short or 0:>6.1f}{100 * win:>5.0f}  {years}")  # fmt: skip


def family(number: int) -> None:
    con = connect()
    t0, where, keys = FAMILIES[number]
    total = 0
    for t in TIMES.get(number, (t0,)):
        rows, names = measure(con, t, where, keys, "yr <= 2022")
        k = len(names)
        rows = [r for r in rows if all(v is not None for v in r[:k])]
        total += len(rows)
        big = [r for r in rows if r[k] >= 300]

        def years_ok(r, sign=1):
            return all(v is not None and sign * v > 0 for v in r[k + 8 : k + 13])

        short_listed = [r for r in big if r[k + 3] >= 0.03 and (r[k + 4] or 0) >= 4 and years_ok(r)]
        near = [r for r in big if 0.015 <= r[k + 3] < 0.03 and (r[k + 4] or 0) >= 4 and years_ok(r)]
        print(f"\n=== family {number} at {t // 60:02d}:{t % 60:02d}: {len(rows)} cells, "
              f"{len(big)} with 300+ trades; shortlisted {len(short_listed)}, near {len(near)}")  # fmt: skip
        show(sorted(short_listed, key=lambda r: -r[k + 3]), names, "SHORTLIST (long)")
        show(sorted(near, key=lambda r: -r[k + 3]), names, "near misses (long)")
        show(sorted(big, key=lambda r: -r[k + 3])[:5], names, "best long cells by net")
        show(sorted(big, key=lambda r: -r[k + 5])[:4], names, "best short cells (information)")
    print(f"\ncells measured in family {number}: {total}")


STATES = {
    "any": "true", "gap up 10%+": "gap >= 0.10", "gap down 10%+": "gap <= -0.10",
    "up 10%+ by then": "mov{t} >= 0.10", "yesterday up 20%+": "ret1 >= 0.20",
    "yesterday down 20%+": "ret1 <= -0.20", "volume 5x": "rvol{t} >= 5",
}  # fmt: skip


def limits(years: str = "yr <= 2022") -> None:
    """Family 10: a bid resting `depth` below the price from time t; sold at the close."""
    con = connect()
    found = []
    for t in (575, 600):
        for depth in (0.05, 0.10, 0.15, 0.20, 0.30):
            for state, where in STATES.items():
                per_year = ", ".join(
                    f"sum(net * n) filter (yr = {y}) / nullif(sum(n) filter (yr = {y}), 0)"
                    for y in (*YEARS, 2023)
                )
                rows = con.execute(
                    f"""with x as (
                            select {CAP} as cap, day, yr,
                                   (1 + r{t}) / {1 - depth} - 1 as r,
                                   2 * half_spread + 2 * commission as cost
                            from b where ok{t} and mae{t} <= {-depth} and {years}
                              and ({where.format(t=t)})),
                        d as (select cap, day, any_value(yr) as yr, count(*) as n,
                                     avg(r - cost) as net, avg(r) as gross,
                                     sum((r - cost > 0)::int) as wins from x group by 1, 2)
                        select cap, sum(n), count(*), sum(gross * n) / sum(n),
                               sum(net * n) / sum(n),
                               avg(net) / nullif(stddev_samp(net) / sqrt(count(*)), 0),
                               sum(wins) / sum(n), {per_year}
                        from d group by 1"""
                ).fetchall()
                found += [(t, depth, state, *r) for r in rows]
    print(f"cells: {len(found)}; with 300+ fills: {sum(r[4] >= 300 for r in found)}")
    print(f"{'time':>5}{'depth':>6} {'state':22}{'cap':>6}{'fills':>7}{'days':>6}{'gross%':>8}"
          f"{'net%':>7}{'t':>6}{'win':>5}   2018   2019   2020   2021   2022")  # fmt: skip
    keep = [r for r in found if r[4] >= 300]
    for r in sorted(keep, key=lambda r: -r[7])[:28]:
        t, depth, state, cap, n, days, gross, net, tstat, win, *by = r
        years_text = " ".join(f"{100 * (v or 0):6.1f}" for v in by[:5])
        print(f"{t:>5}{100 * depth:>5.0f}% {state:22}{cap:>6}{n:>7.0f}{days:>6}"
              f"{100 * gross:>8.2f}{100 * net:>7.2f}{tstat or 0:>6.1f}{100 * win:>5.0f}  "
              f"{years_text}")  # fmt: skip
    good = [r for r in keep if r[7] >= 0.03 and (r[8] or 0) >= 4
            and all(v is not None and v > 0 for v in r[10:15])]  # fmt: skip
    print(f"shortlisted: {len(good)}")
    for r in good:
        print("  ", r[:4], f"net {100 * r[7]:.2f}% t {r[8]:.1f} fills {r[4]:.0f}")


def cell(t: int, where: str, check: bool) -> None:
    con = connect()
    rows, names = measure(con, t, where, {}, "yr = 2023" if check else "yr <= 2022")
    show(rows, names, f"{'CHECK 2023' if check else 'search 2018-2022'}: {where} at {t}")
    if check:
        print("2023 net:", rows[0][-1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=("news", "family", "cell", "limits"))
    parser.add_argument("args", nargs="*")
    parser.add_argument("--check", action="store_true")
    a = parser.parse_args()
    if a.what == "news":
        news()
    elif a.what == "family":
        family(int(a.args[0]))
    elif a.what == "limits":
        limits()
    else:
        cell(int(a.args[0]), a.args[1], a.check)
    sys.stdout.flush()
