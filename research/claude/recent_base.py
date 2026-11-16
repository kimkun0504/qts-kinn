"""The search table (strategies/recent_search/HYPOTHESIS.md): one row per stock-day with the
features and forward returns the idea families use. Built in four parts by company.

    uv run python research/claude/recent_base.py            # all four parts, skips finished
"""

from __future__ import annotations

import tempfile

import duckdb

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

TIMES = (575, 585, 600, 630, 660, 720, 780, 840, 900, 930)
NORMED = (575, 600, 660, 780, 900)  # times with volume and trade size against their norm
PARTS = 4


def select() -> str:
    cols = [
        "f.day",
        "year(f.day) as yr",
        "f.symbol",
        "f.permaticker",
        "f.category",
        "f.exchange",
        "s.sector",
        "s.industry",
        "f.prev_close",
        "f.marketcap_prev as mcap",
        "f.adv20_prev as adv",
        "f.sessions_prior as age",
        "f.ret60_prev as ret60",
        "f.filings_prev",
        "f.official_close",
        "f.open_px",
        "f.open_px / f.prev_close - 1 as gap",
        "coalesce(f.pm_dollar, 0) / f.adv20_prev as pm_part",
        "f.pm_last / f.prev_close - 1 as pm_ret",
        "f.adv20_prev / nullif(f.marketcap_prev, 0) as turnover",
        "lag(f.official_close / f.prev_close - 1) over w as ret1",
        "lag((f.official_close - f.d_low) / nullif(f.d_high - f.d_low, 0)) over w as loc1",
        "lag(f.d_volume * f.official_close / f.adv20_prev) over w as rvol1",
        "exp(sum(ln(f.official_close / f.prev_close)) over w5) - 1 as ret5",
        "avg((f.d_high - f.d_low) / f.official_close) over w14 as range14",
        "lag(f.day) over w as prev_row_day",
        "f.prev_date",
        """case when f.adv20_prev < 1e6 then 0.0100 when f.adv20_prev < 1e7 then 0.0043
                when f.adv20_prev < 1e8 then 0.0018 else 0.0005 end as half_spread""",
        "least(0.01, greatest(0.000175, 0.0035 / f.prev_close)) as commission",
    ]
    for t in TIMES:
        cols += [
            f"f.official_close / f.e{t} - 1 as r{t}",
            f"(f.em{t} <= {t + 5}) as ok{t}",
            f"f.c{t} / f.prev_close - 1 as mov{t}",
            f"f.c{t} / f.open_px - 1 as drv{t}",
            f"f.c{t} / nullif(f.pv{t} / nullif(f.v{t}, 0), 0) - 1 as vw{t}",
            f"(f.c{t} - f.lo{t}) / nullif(f.hi{t} - f.lo{t}, 0) as pos{t}",
            f"f.loa{t} / f.e{t} - 1 as mae{t}",
            f"f.hia{t} / f.e{t} - 1 as mfe{t}",
            f"f.c{t} * f.v{t} as dv{t}",
        ]
    for t in NORMED:
        cols += [
            f"f.v{t} / nullif(avg(coalesce(f.v{t}, 0)) over w20, 0) as rvol{t}",
            f"(f.v{t} / nullif(f.n{t}, 0)) / nullif(avg(f.v{t} / nullif(f.n{t}, 0)) over w20, 0)"
            f" as size{t}",
        ]
    return ",\n".join(cols)


def main() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "recent"
    scratch = tempfile.mkdtemp()
    for part in range(PARTS):
        target = base / f"base_{part}.parquet"
        if target.exists():
            continue
        con = duckdb.connect()
        con.execute(f"set threads=2; set memory_limit='2200MB'; set temp_directory='{scratch}'")
        con.execute("set preserve_insertion_order=false")
        tmp = base / f"base_{part}.tmp"
        con.execute(
            f"""copy (
                select {select()}
                from read_parquet('{base}/features/*.parquet') f
                left join '{store.root}/master/security_master.parquet' s using (permaticker)
                where f.permaticker % {PARTS} = {part} and abs(ln(f.split_ratio)) < 1e-9
                window w as (partition by f.permaticker order by f.day),
                       w5 as (partition by f.permaticker order by f.day
                              rows between 5 preceding and 1 preceding),
                       w14 as (partition by f.permaticker order by f.day
                               rows between 14 preceding and 1 preceding),
                       w20 as (partition by f.permaticker order by f.day
                               rows between 20 preceding and 1 preceding)
            ) to '{tmp}' (format parquet, compression zstd)"""
        )
        tmp.replace(target)
        con.close()
        print("part", part, "done", flush=True)


if __name__ == "__main__":
    main()
