"""The combined model of the swing search (family 16; addendum of 2026-11-16 in
strategies/swing_search/HYPOTHESIS.md): gradient-boosted trees on every feature of the wide
table, fitted walk-forward, one model a year, each scoring only the year after its data ends.

LightGBM is a research-only tool here, not a dependency of the package:

    uv run --with lightgbm python research/claude/swing_model.py fit [--target 10] [--name base]
    uv run python research/claude/swing_model.py score --name base     # rank cells
"""

from __future__ import annotations

import argparse
import sys
import tempfile

import duckdb
import numpy as np

from kinn.core.settings import load_settings

FIRST, LAST = 2014, 2022
MARKET = ["m5", "m20", "m60", "m250", "breadth", "mvol", "highs", "lows"]
CALENDAR = ["tdleft", "tdom", "month(day) as month", "dayofweek(day) as weekday"]
PLAIN = [
    "dvr", "dvr2", "gap", "loc", "ret1", "ret2", "ret3", "ret5", "ret10", "ret20", "ret60",
    "ret120", "ret250", "down5", "down3", "vol20", "vol60", "high250", "low250", "high20",
    "ma20", "ma50", "ma200", "rsi2", "rsi14", "max20", "min20", "night20", "day20", "dv5",
    "range14", "season", "esince", "epred", "filings_prev", "filings_today", "fage", "rev_yoy",
    "earn_price", "fcf_price", "book_price", "netcash_price", "ni_chg", "gp_assets",
    "debt_assets", "accruals", "issue", "growth", "days_to_cover", "short_share", "short_chg",
    "ind5", "ind20", "ind60", "ind120",
]  # fmt: skip
DERIVED = [
    "ln(close) as lclose", "ln(mcap) as lmcap", "ln(adv) as ladv", "ln(age + 1) as lage",
    "earn::int as earn", "fnew::int as fnew", "ni_pos::int as ni_pos",
    "ret5 - ind5 as rel5", "ret20 - ind20 as rel20", "ret60 - ind60 as rel60",
    "ln(1 + ret5) / nullif(vol60 * sqrt(5), 0) as z5",
    "ln(1 + ret1) / nullif(vol60, 0) as z1",
    "dense_rank() over (order by sector) as sector",
]  # fmt: skip


def name_of(expr: str) -> str:
    return expr.split(" as ")[-1]


def connect(settings) -> duckdb.DuckDBPyConnection:
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    con.execute(
        f"""create view t as select d.*, m.* exclude (day), i.* exclude (day, industry)
            from read_parquet('{base}/wide_*.parquet') d
            left join '{base}/market.parquet' m using (day)
            left join '{base}/industry.parquet' i using (day, industry)"""
    )
    return con


def columns(market: bool) -> list[str]:
    cols = PLAIN + DERIVED + CALENDAR
    return cols + MARKET if market else cols


def load(con, where: str, target: int, market: bool, every: int = 1):
    cols = columns(market)
    table = con.sql(
        f"""select permaticker, day,
                   greatest(-0.3, least(0.3,
                       exp(first_day + c_exit{target} - c_next) - 1 - mk{target})) as y,
                   {", ".join(cols)}
            from t where close >= 3 and adv >= 5e6 and next_open is not null and ({where})
              and (tdom + 3 * month(day)) % {every} = 0"""
    ).to_arrow_table()
    names = [name_of(c) for c in cols]
    x = np.empty((table.num_rows, len(names)), dtype=np.float32)
    for j, n in enumerate(names):
        x[:, j] = table.column(n).to_numpy(zero_copy_only=False).astype(np.float32)
    y = table.column("y").to_numpy(zero_copy_only=False).astype(np.float32)
    return table.select(["permaticker", "day"]), x, y, names


def fit(name: str, target: int, market: bool) -> None:
    import lightgbm as lgb
    import pyarrow as pa
    import pyarrow.parquet as pq

    settings = load_settings()
    out = settings.data_dir / "research" / "swing" / "scores"
    out.mkdir(parents=True, exist_ok=True)
    con = connect(settings)
    params = {
        "objective": "regression", "learning_rate": 0.03, "num_leaves": 31,
        "min_data_in_leaf": 2000, "feature_fraction": 0.7, "bagging_fraction": 0.5,
        "bagging_freq": 1, "lambda_l2": 10.0, "num_threads": 3, "verbose": -1, "seed": 7,
        "max_bin": 63,
    }  # fmt: skip
    for year in range(FIRST, LAST + 1):
        target_file = out / f"{name}_{year}.parquet"
        if target_file.exists():
            continue
        _, x, y, names = load(
            con, f"day between DATE '2010-01-04' and DATE '{year - 1}-12-10'", target, market, 3
        )
        keep = ~np.isnan(y)
        data = lgb.Dataset(
            x[keep], y[keep], feature_name=names, categorical_feature=["sector"],
            free_raw_data=True,
        )  # fmt: skip
        model = lgb.train(params, data, num_boost_round=300)
        del x, y, data
        keys, x, _, _ = load(con, f"year(day) = {year}", target, market)
        score = model.predict(x)
        del x
        tmp = out / f"{name}_{year}.tmp"
        pq.write_table(keys.append_column("score", pa.array(score, type=pa.float32())), tmp)
        tmp.rename(target_file)
        gain = model.feature_importance("gain")
        top = sorted(zip(gain, names, strict=True), reverse=True)[:12]
        print(year, keep.sum(), "rows;", ", ".join(f"{n} {g / gain.sum():.0%}" for g, n in top),
              flush=True)  # fmt: skip


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=("fit",))
    parser.add_argument("--name", default="base")
    parser.add_argument("--target", type=int, default=10)
    parser.add_argument("--no-market", action="store_true")
    a = parser.parse_args()
    fit(a.name, a.target, not a.no_market)


if __name__ == "__main__":
    sys.exit(main())
