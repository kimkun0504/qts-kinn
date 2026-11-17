"""The overnight programme (addendum of 2026-11-16 in strategies/swing_search/HYPOTHESIS.md):
which earnings jumps fail, a purchased hedge, standing aside, exits, and the book that results.
Signals of 2005 to October 2023 only. 2020 is always shown apart.

    uv run python research/claude/swing_overnight.py quality
    uv run python research/claude/swing_overnight.py books
"""

from __future__ import annotations

import math
import pickle
import sys
import tempfile
from collections import defaultdict
from datetime import date
from pathlib import Path

import duckdb
import numpy as np

import swing_exits as exits
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from swing_early import PERIODS, RULES

EXTRA = ("issue, ni_pos, fcf_price, netcash_price, earn_price, book_price, rev_yoy, fage, vol60, "
         "ret60, ret250, high250, mcap, close, ret2, loc, short_share, days_to_cover, sector, "
         "half_spread")  # fmt: skip
ACCOUNT, SLOTS, DRAG, FUND_COST = 20000.0, 10, 0.02 / 252, 0.0005
CACHE = Path(tempfile.gettempdir()) / "swing_overnight_signals.pkl"


def load(rule: str = "A50") -> list[dict]:
    """A50's signals with their bars (as in swing_exits.load) and the facts known at the close."""
    if CACHE.exists() and rule == "A50":
        return pickle.loads(CACHE.read_bytes())
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    names = [n.strip() for n in EXTRA.split(",")]
    out = []
    for period in ("early", "search", "check"):
        name, dates = PERIODS[period]
        market = "market_early" if name == "early" else "market"
        extra = ", ".join(f"d.{n}" if not (n in ("short_share", "days_to_cover") and name == "early")
                          else f"null as {n}" for n in names)  # fmt: skip
        rows = con.sql(
            f"""with p as (
                    select permaticker, date, open / close as o, high / close as h, low / close as l,
                           sum(ln(close / prev_close)) over (partition by permaticker order by date) as c,
                           row_number() over (partition by permaticker order by date) as rn
                    from read_parquet('{store.root}/panel/*.parquet')
                    where prev_close > 0 and close > 0 and low > 0 and open > 0
                      and category like '%Common Stock%'),
                s as (select d.permaticker, d.day, d.symbol, d.adv, d.dvr2, d.commission, {extra},
                             p.rn, p.c
                      from read_parquet('{base}/{name}_*.parquet') d
                      left join '{base}/{market}.parquet' m using (day)
                      join p on p.permaticker = d.permaticker and p.date = d.day
                      where {dates} and next_open is not null and ({RULES[rule]}))
                select s.day, s.symbol, s.adv, s.dvr2, s.commission, {", ".join("s." + n for n in names)},
                       p.rn - s.rn as k, p.date, exp(p.c - s.c) as close_, p.o, p.h, p.l
                from s join p on p.permaticker = s.permaticker
                             and p.rn between s.rn - {exits.BEFORE} and s.rn + {exits.AFTER}
                order by s.day, s.symbol, p.date"""
        ).fetchall()
        trades: dict = {}
        for row in rows:
            day, symbol, adv, volume, commission = row[:5]
            facts = dict(zip(names, row[5 : 5 + len(names)], strict=True))
            k, d, close, o, h, low = row[5 + len(names) :]
            t = trades.setdefault((day, symbol), {"day": day, "symbol": symbol, "adv": adv,
                                                  "volume": volume, "commission": commission,
                                                  **facts, "bars": {}})  # fmt: skip
            t["bars"][k] = (d, close * o, close * h, close * low, close)
        out += list(trades.values())
    if rule == "A50":
        CACHE.write_bytes(pickle.dumps(out))
    return out


def index() -> dict:
    """The small-stock index fund by session: its return from the open and from the prior
    close, whether it closed under its 200-day average, and its five-session return."""
    store = DataStore(load_settings())
    bars = store.daily(date(2004, 1, 2), date(2023, 11, 8), symbols=["IWM"])
    con = duckdb.connect()
    con.register("bars", bars)
    rows = con.execute(
        """select date, close / open - 1, close / lag(close) over w - 1,
                  close < avg(close) over (order by date rows between 199 preceding and current row),
                  close / lag(close, 5) over w - 1
           from bars window w as (order by date) order by date"""
    ).fetchall()
    return {d: {"first": a, "day": b, "below": bool(c), "five": e} for d, a, b, c, e in rows
            if b is not None}  # fmt: skip


def side_costs(t: dict, basis: str) -> float:
    spread = float(t["half_spread"]) if basis == "crossed" else exits.allow(t["adv"])
    return float(t["commission"]) + spread


def build(signals, fund, *, hedge=0.0, when="always", skip=None, keep=None, **exit_options):
    """Trades under one configuration: for each, the sessions held, the stock leg's value and
    the fund leg's value day by day (multiples of each leg's entry price), and its hedge."""
    out = []
    for t in signals:
        state = fund.get(t["day"])
        if state is None or (keep and not keep(t)):
            continue
        if (skip == "below" and state["below"]) or (
            skip == "five" and (state["five"] or 0) <= -0.05
        ):
            continue
        result = exits.trade(t, **exit_options)
        if result is None or not result[2]:
            continue
        _, _, marks, extra = result
        if any(d not in fund for d, _ in marks):
            continue
        ratio = hedge if (when == "always" or state["below"]) else 0.0
        value, leg = 1.0, []
        for i, (d, _) in enumerate(marks):
            value *= 1 - (fund[d]["first"] if i == 0 else fund[d]["day"]) - DRAG
            leg.append(value)
        out.append({"t": t, "dates": [d for d, _ in marks], "stock": [v for _, v in marks],
                    "fund": leg, "hedge": ratio, "extra": extra})  # fmt: skip
    return out


def per_trade(trades, basis="auction"):
    """Each trade's net return on the dollars put into it (stock and fund together)."""
    rows = []
    for x in trades:
        c, h = side_costs(x["t"], basis), x["hedge"]
        stock = x["stock"][-1] * (1 - c - x["extra"]) - (1 + c)
        fund = h * (x["fund"][-1] * (1 - FUND_COST) - (1 + FUND_COST))
        rows.append((x["t"]["day"].year, (stock + fund) / (1 + h)))
    return rows


def run_book(trades, basis="auction", slots=SLOTS):
    budget = ACCOUNT / slots
    by_entry = defaultdict(list)
    for x in trades:
        by_entry[x["dates"][0]].append(x)
    open_until: list = []
    daily: dict = defaultdict(float)
    taken = 0
    for day in sorted(by_entry):
        open_until = [last for last in open_until if last >= day]
        for x in sorted(by_entry[day], key=lambda x: (-x["t"]["volume"], x["t"]["symbol"])):
            if len(open_until) >= slots:
                continue
            open_until.append(x["dates"][-1])
            taken += 1
            c, h = side_costs(x["t"], basis), x["hedge"]
            stock_dollars, fund_dollars = budget / (1 + h), budget * h / (1 + h)
            daily[x["dates"][0]] -= stock_dollars * c + fund_dollars * FUND_COST
            before_s, before_f = 1.0, 1.0
            for d, s, f in zip(x["dates"], x["stock"], x["fund"], strict=True):
                daily[d] += stock_dollars * (s - before_s) + fund_dollars * (f - before_f)
                before_s, before_f = s, f
            daily[x["dates"][-1]] -= (stock_dollars * x["stock"][-1] * (c + x["extra"])
                                      + fund_dollars * x["fund"][-1] * FUND_COST)  # fmt: skip
    return daily, taken


def describe(label, trades):
    rows = per_trade(trades)
    years = sorted({y for y, _ in rows})
    by = {y: np.mean([r for yy, r in rows if yy == y]) for y in years}
    everything = np.array([r for _, r in rows])
    without = np.array([r for y, r in rows if y != 2020])
    line = (f"{label:44} n={len(rows):4d} trade {100 * everything.mean():5.2f}% (ex-2020 "
            f"{100 * without.mean():5.2f}%) yrs+ {sum(v > 0 for v in by.values()):2d}/{len(by)} "
            f"worst {min(by, key=by.get)} {100 * min(by.values()):5.1f}%")  # fmt: skip
    for basis in ("auction", "crossed"):
        daily, taken = run_book(trades, basis)
        days = sorted(d for d in daily if d.year >= 2006)
        pnl = np.array([daily[d] for d in days])
        equity = np.cumsum(pnl)
        drawdown = (np.maximum.accumulate(equity) - equity).max()
        span = (days[-1] - days[0]).days / 365.25
        totals = defaultdict(float)
        for d, x in zip(days, pnl, strict=True):
            totals[d.year] += x
        ex = [v for y, v in totals.items() if y != 2020]
        line += (f" | {basis[:4]} ${equity[-1] / span:5,.0f}/yr (ex-20 ${np.mean(ex):5,.0f}) Sh "
                 f"{pnl.mean() / pnl.std(ddof=1) * math.sqrt(252):4.2f} DD ${drawdown:6,.0f} worst "
                 f"{min(totals, key=totals.get)} ${min(totals.values()):6,.0f} lose "
                 f"{sum(v < 0 for v in totals.values())}")  # fmt: skip
    print(line)
    return by


FILTERS = {
    "issued 10% or less": lambda t: t["issue"] is not None and t["issue"] <= 0.10,
    "issued over 10%": lambda t: t["issue"] is not None and t["issue"] > 0.10,
    "profitable quarter": lambda t: t["ni_pos"] is True,
    "loss-making quarter": lambda t: t["ni_pos"] is False,
    "free cash flow positive": lambda t: t["fcf_price"] is not None and t["fcf_price"] >= 0,
    "free cash flow negative": lambda t: t["fcf_price"] is not None and t["fcf_price"] < 0,
    "net cash": lambda t: t["netcash_price"] is not None and t["netcash_price"] >= 0,
    "net debt": lambda t: t["netcash_price"] is not None and t["netcash_price"] < 0,
    "price $3 or more": lambda t: t["close"] >= 3,
    "price $5 or more": lambda t: t["close"] >= 5,
    "at a 250-day high": lambda t: t["high250"] is not None and t["high250"] > 0,
    "not at a 250-day high": lambda t: t["high250"] is not None and t["high250"] <= 0,
    "up over the year": lambda t: t["ret250"] is not None and t["ret250"] > 0,
    "down over the year": lambda t: t["ret250"] is not None and t["ret250"] <= 0,
    "short interest 5% or more": lambda t: t["short_share"] is not None and t["short_share"] >= 0.05,
    "short interest under 5%": lambda t: t["short_share"] is not None and t["short_share"] < 0.05,
}  # fmt: skip
SPANS = (("2010-17", lambda y: 2010 <= y <= 2017), ("2005-09", lambda y: y <= 2009),
         ("2018-23", lambda y: y >= 2018), ("2018-23 ex-2020", lambda y: y >= 2018 and y != 2020))  # fmt: skip


def quality(signals, fund) -> None:
    base = build(signals, fund)
    everything = {name: np.mean([r for y, r in per_trade(base) if ok(y)]) for name, ok in SPANS}
    print(
        f"{'all A50 trades':28} " + "  ".join(f"{n} {100 * v:5.2f}%" for n, v in everything.items())
    )
    for label, keep in FILTERS.items():
        rows = per_trade(build(signals, fund, keep=keep))
        cells, better = [], True
        for name, ok in SPANS:
            r = [x for y, x in rows if ok(y)]
            mean = np.mean(r) if r else float("nan")
            better &= bool(r) and mean > everything[name]
            cells.append(f"{name} {100 * mean:5.2f}% ({len(r):3d})")
        print(f"{label:28} " + "  ".join(cells) + ("   <- better in every span" if better else ""))


def books(signals, fund) -> None:
    configs = {
        "plain": {},
        "fund bought, all, always": {"hedge": 1.0},
        "fund bought, half, always": {"hedge": 0.5},
        "fund bought, all, in downtrend": {"hedge": 1.0, "when": "below"},
        "fund bought, half, in downtrend": {"hedge": 0.5, "when": "below"},
        "stand aside in downtrend": {"skip": "below"},
        "stand aside after a 5% drop": {"skip": "five"},
        "20-day-average exit": {"ema": 20},
        "20-day exit, fund all always": {"ema": 20, "hedge": 1.0},
        "20-day exit, fund in downtrend": {"ema": 20, "hedge": 1.0, "when": "below"},
        "40% target": {"target": 0.40},
        "40% target, fund all always": {"target": 0.40, "hedge": 1.0},
        "40% target, fund in downtrend": {"target": 0.40, "hedge": 1.0, "when": "below"},
    }
    for label, options in configs.items():
        describe(label, build(signals, fund, **options))


def up(t) -> bool:
    return t["ret250"] is not None and t["ret250"] > 0


def debt(t) -> bool:
    return t["netcash_price"] is not None and t["netcash_price"] < 0


def high(t) -> bool:
    return t["high250"] is not None and t["high250"] > 0


GROUPS = {
    "up and net debt": lambda t: up(t) and debt(t),
    "up and net cash": lambda t: up(t) and not debt(t) and t["netcash_price"] is not None,
    "down and net debt": lambda t: not up(t) and debt(t) and t["ret250"] is not None,
    "down and net cash": lambda t: (not up(t) and not debt(t) and t["ret250"] is not None
                                    and t["netcash_price"] is not None),
    "up or net debt": lambda t: up(t) or debt(t),
    "up over the year": up,
    "net debt": debt,
    "at a 250-day high": high,
    "high or net debt": lambda t: high(t) or debt(t),
}  # fmt: skip


def cross(signals, fund) -> None:
    for label, keep in GROUPS.items():
        rows = per_trade(build(signals, fund, keep=keep))
        cells = []
        for name, ok in SPANS:
            r = [x for y, x in rows if ok(y)]
            cells.append(f"{name} {100 * np.mean(r):5.2f}% ({len(r):3d})")
        years = sorted({y for y, _ in rows})
        by = {y: np.mean([x for yy, x in rows if yy == y]) for y in years}
        print(f"{label:20} " + "  ".join(cells))
        print("      " + " ".join(f"{y % 100:02d}:{100 * v:5.1f}" for y, v in by.items()))


def filtered(signals, fund) -> None:
    for name in ("up or net debt", "up over the year", "net debt", "high or net debt"):
        keep = GROUPS[name]
        for label, options in (("plain", {}), ("fund all in downtrend", {"hedge": 1.0, "when": "below"}),
                               ("fund all always", {"hedge": 1.0}),
                               ("20-day exit", {"ema": 20}),
                               ("20-day exit, fund in downtrend", {"ema": 20, "hedge": 1.0, "when": "below"}),
                               ("40% target, fund in downtrend", {"target": 0.4, "hedge": 1.0, "when": "below"})):  # fmt: skip
            describe(f"{name}: {label}"[:44], build(signals, fund, keep=keep, **options))


if __name__ == "__main__":
    what = sys.argv[1]
    data, market = load(), index()
    print(len(data), "signals;", len(market), "sessions of the index")
    {"quality": quality, "books": books, "cross": cross, "filtered": filtered}[what](data, market)
