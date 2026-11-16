"""Three selectors for the opening range breakout (strategies/intraday_momentum/HYPOTHESIS.md,
addendum of 2026-11-16 02:00 ET): news, gap and range height. Development trades only."""

from __future__ import annotations

import glob
import math
from datetime import date

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from kinn.validation.targets import DEVELOPMENT_END

POSITION = 4_000.0


def main() -> None:
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "momentum"
    files = [pq.read_table(f) for f in sorted(glob.glob(str(base / "trades" / "*.parquet")))]
    trades = pa.concat_tables([f for f in files if f.num_columns], promote_options="default")
    con = duckdb.connect()
    con.register("trades", trades)
    root = store.root
    joined = con.sql(
        f"""with t as (
                select t.*, c.range_high, c.range_low, c.or_open, c.atr14,
                       p.prev_close, p.prev_date, p.permaticker, p.filings_prev
                from trades t
                join '{base}/candidates.parquet' c
                  on c.day = t.day and c.symbol = t.symbol and c.range = t.range
                join read_parquet('{root}/panel/*.parquet') p
                  on p.date = t.day and p.symbol = t.symbol
                where t.range = 'or5' and p.date <= DATE '{DEVELOPMENT_END.isoformat()}'),
            earnings as (
                select distinct t.day, t.symbol
                from t join '{root}/master/security_master.parquet' s using (permaticker)
                join '{root}/sharadar/events.parquet' e
                  on e.ticker = s.ticker and e.date >= t.prev_date and e.date < t.day
                where regexp_matches('|' || e.eventcodes || '|', '[|]22[|]'))
            select t.*, e.day is not null as earnings from t
            left join earnings e on e.day = t.day and e.symbol = t.symbol"""
    ).to_arrow_table()
    d = {k: joined[k].to_numpy(zero_copy_only=False) for k in joined.column_names}
    calendar = store.calendar(date(2003, 9, 10), DEVELOPMENT_END).to_pylist()
    sessions = np.array([r["date"] for r in calendar]).astype("datetime64[D]")
    index = np.searchsorted(sessions, d["day"].astype("datetime64[D]"))
    year = d["day"].astype("datetime64[Y]").astype(int) + 1970
    side, entry = d["direction"].astype(float), d["entry"]
    gap = side * (d["or_open"] / d["prev_close"] - 1.0)
    height = (d["range_high"] - d["range_low"]) / d["atr14"]
    low_cut, high_cut = np.quantile(height, [1 / 3, 2 / 3])
    groups = {
        "all trades": np.ones(len(entry), dtype=bool),
        "1a 8-K since the prior session": d["filings_prev"] > 0,
        "1a no 8-K": d["filings_prev"] == 0,
        "1b earnings 8-K": d["earnings"].astype(bool),
        "1b no earnings 8-K": ~d["earnings"].astype(bool),
        "2 gap with, 3% or more": gap >= 0.03,
        "2 gap with, 1% or more": gap >= 0.01,
        "2 flat (under 1%)": np.abs(gap) < 0.01,
        "2 gap against, 1% or more": gap <= -0.01,
        f"3 narrow range (under {low_cut:.2f} ATR)": height < low_cut,
        "3 middle range": (height >= low_cut) & (height < high_cut),
        f"3 wide range (over {high_cut:.2f} ATR)": height >= high_cut,
    }
    for exit_rule in ("vwap", "stop"):
        print(f"\nexit: {exit_rule}")
        print(f"{'group':34}{'trades':>8}{'gross%':>8}{'se':>7}{'03-09':>8}{'10-16':>8}"
              f"{'even c':>8}{'S 1c':>7}{'S 2c':>7}{'$/yr 2c':>9}{'yrs 2c':>8}")  # fmt: skip
        for name, pick in groups.items():
            n = np.floor(POSITION / entry[pick])
            out_price, e, s = d[exit_rule][pick], entry[pick], side[pick]
            gross = s * (out_price - e) / e
            dollars = s * (out_price - e) * n - 2 * np.maximum(0.35, 0.0035 * n)
            even = 100 * dollars.sum() / (2 * n.sum())
            cells = []
            for cents in (0.01, 0.02):
                daily = np.bincount(index[pick], weights=dollars - 2 * cents * n,
                                    minlength=len(sessions))  # fmt: skip
                cells.append((daily.mean() / daily.std(ddof=1) * math.sqrt(252), daily))
            daily = cells[1][1]
            years = sessions.astype("datetime64[Y]").astype(int) + 1970
            good = sum(daily[years == y].sum() > 0 for y in np.unique(years))
            early, late = gross[year[pick] <= 2009], gross[year[pick] >= 2010]
            print(f"{name:34}{int(pick.sum()):>8}{100 * gross.mean():>8.3f}"
                  f"{100 * gross.std(ddof=1) / math.sqrt(len(gross)):>7.3f}"
                  f"{100 * early.mean():>8.3f}{100 * late.mean():>8.3f}{even:>8.1f}"
                  f"{cells[0][0]:>7.2f}{cells[1][0]:>7.2f}{daily.sum() / 13.3:>9,.0f}"
                  f"{good:>5}/14")  # fmt: skip


if __name__ == "__main__":
    main()
