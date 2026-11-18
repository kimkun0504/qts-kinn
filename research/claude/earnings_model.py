"""strategies/earnings_model/HYPOTHESIS.md: one fixed model of the drift after results.

    cd research/claude
    uv run python earnings_model.py table
    uv run --with lightgbm python earnings_model.py fit
"""

from __future__ import annotations

import sys
import tempfile

import duckdb
import numpy as np
from swing_earnings import AUCTION, weekly

from intraday_shape import folder as shape
from kinn.core.settings import load_settings
from kinn.data.store import DataStore

DAILY = ["ret1", "ret2", "ret5", "ret20", "ret60", "ret250", "dvr", "dvr2", "gap", "loc", "vol20", "rsi2",
         "high250", "netcash_price", "ni_pos", "rev_yoy", "earn_price", "issue"]  # fmt: skip
FEATURES = DAILY + ["lmcap", "lprice", "ladv", "first0", "last0", "first1", "last1"]
SPANS = {"2005-2009": (2005, 2009), "2010-2017": (2010, 2017), "2018-2022": (2018, 2022), "2023": (2023, 2023)}
FOLDS = [(2010, 2011), (2012, 2013), (2014, 2015), (2016, 2016), (2017, 2017)]


def path():
    return load_settings().data_dir / "research" / "swing" / "earnings_model.parquet"


def table() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(f"set threads=3; set memory_limit='2000MB'; set temp_directory='{tempfile.mkdtemp()}'")
    where = "earn and mcap >= 5e7 and mcap < 2e9 and adv >= 250000 and close >= 1 and next_open is not null"
    con.execute(
        f"""copy (
            with e as (
                select day, symbol, permaticker, prev_date, {", ".join(DAILY)}, ln(mcap) as lmcap, ln(close) as lprice,
                       ln(adv) as ladv, exp(first_day + c_exit15 - c_next) - 1 as g, {AUCTION} as cost,
                       (ret2 >= 0.15 and dvr2 >= 5 and mcap < 3e8) as a50
                from read_parquet('{base}/early_*.parquet') where {where} and day >= DATE '2005-01-03'
                union all
                select day, symbol, permaticker, prev_date, {", ".join(DAILY)}, ln(mcap), ln(close), ln(adv),
                       exp(first_day + c_exit15 - c_next) - 1, {AUCTION}, (ret2 >= 0.15 and dvr2 >= 5 and mcap < 3e8)
                from read_parquet('{base}/wide_*.parquet') where {where} and day <= DATE '2023-10-13'),
            p as (select symbol, date, open, close from read_parquet('{store.root}/panel/*.parquet')
                  where date <= DATE '2023-11-08'),
            s as (select p.symbol, p.date, ln(g.p1000 / p.open) as first30, ln(p.close / g.p1530) as last30
                  from p join read_parquet('{shape()}/segments_*.parquet') g on g.symbol = p.symbol and g.day = p.date)
            select e.*, s0.first30 as first0, s0.last30 as last0, s1.first30 as first1, s1.last30 as last1
            from e left join s s0 on s0.symbol = e.symbol and s0.date = e.day
            left join s s1 on s1.symbol = e.symbol and s1.date = e.prev_date
            where e.g is not null
        ) to '{path()}' (format parquet)"""
    )
    print(con.sql(f"select count(*), count(first0), sum(a50::int), min(day), max(day) from '{path()}'").fetchall())


def load() -> dict[str, np.ndarray]:
    t = duckdb.sql(
        f"""select *, year(day) as yr, (date_diff('day', DATE '2003-12-29', day) // 7) as week
            from '{path()}' order by day, symbol"""
    ).to_arrow_table()
    d = {n: t.column(n).to_numpy(zero_copy_only=False) for n in t.column_names}
    d["X"] = np.column_stack([np.asarray(d[f], dtype=float) for f in FEATURES])
    d["y"] = np.clip(d["g"].astype(float) - d["cost"].astype(float), -0.5, 1.0)
    d["net"] = d["g"].astype(float) - d["cost"].astype(float)
    return d


class model:
    """LightGBM's own training interface (scikit-learn is not installed), settings fixed in the plan."""

    PARAMS = {"objective": "regression", "learning_rate": 0.03, "num_leaves": 15, "min_data_in_leaf": 200,
              "feature_fraction": 0.8, "bagging_fraction": 0.8, "bagging_freq": 1, "seed": 7, "verbose": -1}  # fmt: skip

    def fit(self, x, y):
        import lightgbm as lgb

        self.booster_ = lgb.train(self.PARAMS, lgb.Dataset(x, y), num_boost_round=300)
        return self

    def predict(self, x):
        return self.booster_.predict(x)


def show(label, d, keep) -> str:
    net = d["net"][keep]
    if len(net) < 3:
        return f"{label:28} {len(net)}"
    _, t, _ = weekly(net, d["week"][keep])
    years = d["yr"][keep]
    pos = sum(net[years == y].mean() > 0 for y in set(years))
    other = keep & ~d["a50"].astype(bool)
    return (f"{label:28} {len(net):>5} trades  net {100 * net.mean():>6.2f}%  t {t:>5.2f}  yrs {pos} of {len(set(years))}  "
            f"A50 share {100 * d['a50'][keep].mean():>3.0f}%  not A50: {other.sum():>4} at {100 * d['net'][other].mean():>6.2f}%")  # fmt: skip


def fit() -> None:
    d = load()
    yr = d["yr"]
    train = (yr >= 2010) & (yr <= 2017)
    oof = np.full(len(yr), np.nan)
    for a, b in FOLDS:
        hold = (yr >= a) & (yr <= b)
        m = model().fit(d["X"][train & ~hold], d["y"][train & ~hold])
        oof[hold] = m.predict(d["X"][hold])
    full = model().fit(d["X"][train], d["y"][train])
    pred = np.where(train, oof, full.predict(d["X"]))
    cuts = {"top 10%": np.quantile(oof[train], 0.90), "top 5%": np.quantile(oof[train], 0.95)}
    print(f"{len(yr)} events; A50 signals {int(d['a50'].sum())}; cut-offs " + ", ".join(f"{k} {100 * v:.2f}%" for k, v in cuts.items()))
    for span, (a, b) in SPANS.items():
        inside = (yr >= a) & (yr <= b)
        print(show(f"every event {span}", d, inside))
        print(show(f"A50 {span}", d, inside & d["a50"].astype(bool)))
        for name, cut in cuts.items():
            print(show(f"{name} {span}", d, inside & (pred >= cut)))
            if span in ("2005-2009", "2018-2022"):
                keep = inside & (pred >= cut)
                print("      " + "  ".join(f"{y} {100 * d['net'][keep & (yr == y)].mean():.1f}% ({(keep & (yr == y)).sum()})"
                                           for y in sorted(set(yr[keep]))))  # fmt: skip
    gain = full.booster_.feature_importance(importance_type="gain")
    print("importance:", ", ".join(f"{FEATURES[i]} {100 * gain[i] / gain.sum():.0f}%" for i in np.argsort(-gain)[:10]))


if __name__ == "__main__":
    if sys.argv[1] == "table":
        table()
    else:
        fit()
