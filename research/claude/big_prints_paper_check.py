"""Does the paper ledger's code (src/kinn/big_prints_paper.py) find the research's signals?

Runs its measures and candidates on the processed daily bars for sampled sessions of 2022,
with the panel's market value and the research's 8-K filter standing in for the vendor's
details and the SEC's submissions, and compares the signals with research/claude/big_prints.py
(events_v5, "small 20 fp>=3").

    cd research/claude
    uv run python big_prints_paper_check.py
"""

from __future__ import annotations

import random
from datetime import date

import duckdb

import sec_times
from kinn import big_prints_paper as bpp
from kinn.core.settings import load_settings
from kinn.data.store import DataStore


def main() -> None:
    settings = load_settings()
    store = DataStore(settings)
    bars = store.bars_roots[0] / "daily"
    con = duckdb.connect()
    con.execute("set threads=3; set memory_limit='1500MB'")
    small = con.sql(
        f"""select distinct symbol from read_parquet('{store.root}/panel/*.parquet')
            where date between DATE '2022-01-01' and DATE '2022-12-31' and marketcap_prev < 3e8
              and marketcap_prev >= 5e7 and category like '%Common Stock%'"""
    ).fetchall()
    symbols = [s[0] for s in small]
    rows = con.execute(
        f"""select date, symbol, open, close, volume, transactions from read_parquet('{bars}/*.parquet')
            where date between DATE '2021-08-01' and DATE '2022-12-31' and transactions > 0 and volume > 0
              and symbol in (select unnest(?))""",
        [symbols],
    ).fetchall()
    window: bpp.Window = {}
    for d, s, o, c, v, n in rows:
        window.setdefault(d, {})[s] = bpp.DayBar(o, c, float(v), float(n))
    sessions = sorted(window)
    caps = {(r[0], r[1]): r[2] for r in con.sql(
        f"""select date, symbol, marketcap_prev from read_parquet('{store.root}/panel/*.parquet')
            where date between DATE '2022-01-01' and DATE '2022-12-31'""").fetchall()}  # fmt: skip
    stocks = sec_times.numbers()
    news = {}
    for row in sec_times.filings("8k.jsonl.gz"):
        if row["cik"] in stocks and "2021-12" <= row["filed"][:7] <= "2022-12":
            when = sec_times.accepted(row)
            day = sec_times.reaction_session(sessions, when) if when else None
            if day:
                news.setdefault(row["cik"], []).append(day)
    perma = {r[0]: r[1] for r in con.sql(
        f"""select symbol || '|' || date, permaticker from read_parquet('{store.root}/panel/*.parquet')
            where date between DATE '2022-01-01' and DATE '2022-12-31'""").fetchall()}  # fmt: skip
    by_perma = {}
    for cik, ps in stocks.items():
        for p in ps:
            by_perma.setdefault(p, []).extend(news.get(cik, []))
    research = con.sql(
        f"""select signal_day, permaticker from '{settings.data_dir}/research/big_prints/events_v5.parquet'
            where size = 'small' and fp >= 3 and year(signal_day) = 2022"""
    ).fetchall()
    days = sorted(random.Random(18).sample([d for d in sessions if d.year == 2022], 25))
    want = {(d, p) for d, p in research if d in set(days)}
    got = set()
    skipped = []
    for day in days:
        found = bpp.measures(window, day)
        if bpp.market_share(found) >= bpp.SHARE_MAX:
            skipped.append(day)
            continue
        for c in bpp.candidates(found):
            cap = caps.get((day, c["symbol"]))
            p = perma.get(f"{c['symbol']}|{day}")
            if p is None or not cap or not bpp.CAP_MIN <= cap < bpp.CAP_MAX:
                continue
            if any(day.toordinal() - 4 <= r.toordinal() <= day.toordinal() for r in by_perma.get(p, [])):
                continue
            got.add((day, p))
    both = want & got
    print(f"{len(days)} sessions of 2022: research {len(want)} signals, paper code {len(got)}, both {len(both)}")
    print("skipped as index days:", skipped)
    print("research only:", sorted(want - got)[:10])
    print("paper only:", sorted(got - want)[:10])
    _ = date


if __name__ == "__main__":
    main()
