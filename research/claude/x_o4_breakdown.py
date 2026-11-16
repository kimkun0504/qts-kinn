"""Break the x_o4 trades of existing runs down by market cap and by price. Reads the run store
and the panel only; starts no run. Usage: uv run python research/claude/x_o4_breakdown.py"""

from __future__ import annotations

import duckdb

from kinn.core.settings import load_settings

RUNS = {
    "development 2003-2016": "20261115T232205Z_claude_rebound_limit_84ff9c3d",
    "validation 2017-2023": "20261115T233007Z_claude_rebound_limit_eec4a69e",
}
CAP = """case when marketcap_prev is null then '4 unknown'
              when marketcap_prev < 3e8 then '1 under $300M'
              when marketcap_prev < 2e9 then '2 $300M-$2B' else '3 over $2B' end"""
PRICE = """case when prev_close < 2 then '1 $1-2' when prev_close < 5 then '2 $2-5'
                when prev_close < 10 then '3 $5-10' when prev_close < 20 then '4 $10-20'
                else '5 $20 and over' end"""
FINE = """case when marketcap_prev is null then '9 unknown'
               when marketcap_prev < 5e7 then '1 under $50M'
               when marketcap_prev < 1.5e8 then '2 $50-150M'
               when marketcap_prev < 3e8 then '3 $150-300M'
               when marketcap_prev < 1e9 then '4 $300M-1B'
               when marketcap_prev < 2e9 then '5 $1-2B' else '6 over $2B' end"""


def main() -> None:
    s = load_settings()
    build = (s.data_dir / "builds" / "CURRENT").read_text().strip()
    con = duckdb.connect()
    for label, run in RUNS.items():
        con.execute(
            f"""create or replace table t as
                select t.*, p.marketcap_prev, p.prev_close, p.adv20_prev
                from '{s.runs_dir}/{run}/trades.parquet' t
                left join read_parquet('{s.data_dir}/builds/{build}/panel/*.parquet') p
                  on p.date = t.day and p.permaticker = t.permaticker"""
        )
        n, matched = con.execute("select count(*), count(prev_close) from t").fetchone()
        print(f"\n## {label}  ({run}; {n} trades, {matched} matched to the panel)")
        for title, expr in (("market cap", CAP), ("market cap, finer", FINE), ("price", PRICE)):
            print(f"\nby {title} (previous session)")
            print(
                "group | trades | share | net/trade 1x | net/trade 2x | win | total net 1x"
                " | total net 2x | mean notional | cost bps"
            )
            rows = con.execute(
                f"""select {expr} g, count(*), avg(net / notional), avg(net_2x / notional),
                           avg((net > 0)::int), sum(net), sum(net_2x), avg(notional),
                           1e4 * sum(commission + fees + slippage) / sum(notional)
                    from t group by rollup(g) order by g nulls last"""
            ).fetchall()
            for g, k, r1, r2, win, net, net2, notional, cost in rows:
                print(
                    f"{g or 'all'} | {k} | {100 * k / n:.0f}% | {100 * r1:+.2f}% | "
                    f"{100 * r2:+.2f}% | {100 * win:.0f}% | {net:+,.0f} | {net2:+,.0f} | "
                    f"{notional:,.0f} | {cost:.0f}"
                )
        print("\nby market cap and year: trades, net/trade 2x, total net 1x")
        rows = con.execute(
            f"""select year(day) y, {CAP} g, count(*), avg(net_2x / notional), sum(net)
                from t group by 1, 2 order by 1, 2"""
        ).fetchall()
        years: dict[int, dict[str, str]] = {}
        for y, g, k, r2, net in rows:
            years.setdefault(y, {})[g] = f"{k}, {100 * r2:+.2f}%, {net:+,.0f}"
        groups = ["1 under $300M", "2 $300M-$2B", "3 over $2B", "4 unknown"]
        print("year | " + " | ".join(groups))
        for y, cells in years.items():
            print(f"{y} | " + " | ".join(cells.get(g, "0") for g in groups))


if __name__ == "__main__":
    main()
