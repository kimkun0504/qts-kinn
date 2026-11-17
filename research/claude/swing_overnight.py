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
    cache = CACHE.with_name(f"swing_overnight_{rule}.pkl")
    if cache.exists():
        return pickle.loads(cache.read_bytes())
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
                      left join (select permaticker as p0, day as d0
                                 from '{base}/earn0{"_early" if name == "early" else ""}.parquet') e0
                        on e0.p0 = d.permaticker and e0.d0 = d.day
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
    cache.write_bytes(pickle.dumps(out))
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
    if "side" in t:
        return t["side"][basis]
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


# ---- Checks on the filter (HYPOTHESIS.md, addendum of 2026-11-16 23:08 ET) ----

FACTS = {
    "issued over 10%": lambda t: None if t["issue"] is None else t["issue"] > 0.10,
    "loss-making": lambda t: None if t["ni_pos"] is None else not t["ni_pos"],
    "free cash flow negative": lambda t: None if t["fcf_price"] is None else t["fcf_price"] < 0,
    "net cash": lambda t: None if t["netcash_price"] is None else t["netcash_price"] >= 0,
    "under $5": lambda t: t["close"] < 5,
    "not at a high": lambda t: None if t["high250"] is None else t["high250"] <= 0,
    "down over the year": lambda t: None if t["ret250"] is None else t["ret250"] <= 0,
}  # fmt: skip


def table(signals, fund):
    base = build(signals, fund)
    rows = per_trade(base)
    return base, np.array([y for y, _ in rows]), np.array([r for _, r in rows])


def chance(signals, fund) -> None:
    base, years, r = table(signals, fund)
    kept = np.array([GROUPS["up or net debt"](x["t"]) for x in base])
    labels = sorted(set(years))

    def measures(mask):
        by = [r[mask & (years == y)].mean() for y in labels if (mask & (years == y)).any()]
        return r[mask & (years != 2020)].mean(), sum(v > 0 for v in by), min(by)

    real = measures(kept)
    print(f"the filter drops {(~kept).sum()} of {len(kept)}: mean without 2020 {100 * real[0]:.2f}%, "
          f"winning years {real[1]} of {len(labels)}, worst year {100 * real[2]:.2f}%")  # fmt: skip
    rng = np.random.default_rng(20261116)
    for name in ("anywhere", "the same number in each year"):
        got = []
        for _ in range(5000):
            mask = np.ones(len(r), bool)
            if name == "anywhere":
                mask[rng.choice(len(r), (~kept).sum(), replace=False)] = False
            else:
                for y in labels:
                    index = np.flatnonzero(years == y)
                    drop = (~kept[index]).sum()
                    mask[rng.choice(index, drop, replace=False)] = False
            got.append(measures(mask))
        got = np.array(got)
        print(f"random drops, {name}: mean without 2020 averages {100 * got[:, 0].mean():.2f}% "
              f"(best of 5,000: {100 * got[:, 0].max():.2f}%); as good as the filter in "
              f"{(got[:, 0] >= real[0]).mean():.4f}; worst year as good in "
              f"{(got[:, 2] >= real[2]).mean():.4f}; all years winning in "
              f"{(got[:, 1] == len(labels)).mean():.4f}")  # fmt: skip


def pairs(signals, fund) -> None:
    import itertools

    base, years, r = table(signals, fund)
    values = {name: np.array([f(x["t"]) for x in base], dtype=object) for name, f in FACTS.items()}
    first = (years >= 2010) & (years <= 2017)
    rest = ~first & (years != 2020)
    found = []
    for a, b in itertools.combinations(FACTS, 2):
        for va, vb in itertools.product((True, False), repeat=2):
            mask = np.array([x is va and y is vb for x, y in zip(values[a], values[b], strict=True)])
            if (mask & first).sum() < 60 or (mask & rest).sum() < 30:
                continue
            label = f"{a if va else 'not ' + a} & {b if vb else 'not ' + b}"
            found.append((r[mask & first].mean(), r[mask & rest].mean(), r[mask & (years <= 2009)].mean(),
                          r[mask & (years >= 2018) & (years != 2020)].mean(),
                          int((mask & first).sum()), int((mask & rest).sum()), label))  # fmt: skip
    found.sort()
    print(f"{len(found)} groups; all trades 2010-17 {100 * r[first].mean():.2f}%, the other years "
          f"without 2020 {100 * r[rest].mean():.2f}%")  # fmt: skip
    a, b = np.array([f[0] for f in found]), np.array([f[1] for f in found])
    rank = lambda v: np.argsort(np.argsort(v))  # noqa: E731
    print(f"rank correlation between a group's mean in 2010-17 and in the other years: "
          f"{np.corrcoef(rank(a), rank(b))[0, 1]:.2f}")  # fmt: skip
    print("  2010-17  other  2005-09 2018-23x    n   n  group (worst of 2010-17 first)")
    for i, f in enumerate(found):
        if i < 8 or i >= len(found) - 5 or "net cash & down" in f[6]:
            print(f"{i + 1:3d} {100 * f[0]:6.2f} {100 * f[1]:6.2f} {100 * f[2]:7.2f} {100 * f[3]:7.2f} "
                  f"{f[4]:5d} {f[5]:4d}  {f[6]}")  # fmt: skip
    worst = found[: len(found) // 4]
    print(f"the worst quarter of groups in 2010-17 averaged {100 * np.mean([f[0] for f in worst]):.2f}% "
          f"then and {100 * np.mean([f[1] for f in worst]):.2f}% in the other years; the best quarter "
          f"{100 * np.mean([f[0] for f in found[-len(worst):]]):.2f}% and "
          f"{100 * np.mean([f[1] for f in found[-len(worst):]]):.2f}%")  # fmt: skip


def cutoffs(signals, fund) -> None:
    base, years, r = table(signals, fund)
    ret = np.array([np.nan if x["t"]["ret250"] is None else x["t"]["ret250"] for x in base], float)
    cash = np.array([np.nan if x["t"]["netcash_price"] is None else float(x["t"]["netcash_price"])
                     for x in base], float)  # fmt: skip
    labels = sorted(set(years))
    print("keep if the year's return is over A, or net cash is under B of market value")
    print("     A      B     n  2010-17 2005-09 2018-23 no-2020  yrs+  worst year")
    for a in (-0.30, -0.20, -0.10, 0.0, 0.10, 0.20):
        for b in (-0.10, 0.0, 0.10, 0.25):
            keep = (ret > a) | (cash < b)
            by = {y: r[keep & (years == y)].mean() for y in labels}
            print(f"{100 * a:5.0f}% {100 * b:5.0f}% {keep.sum():5d} "
                  f"{100 * r[keep & (years >= 2010) & (years <= 2017)].mean():7.2f} "
                  f"{100 * r[keep & (years <= 2009)].mean():7.2f} "
                  f"{100 * r[keep & (years >= 2018)].mean():7.2f} "
                  f"{100 * r[keep & (years != 2020)].mean():7.2f} "
                  f"{sum(v > 0 for v in by.values()):3d}/{len(by)} "
                  f"{min(by, key=by.get)} {100 * min(by.values()):5.1f}%")  # fmt: skip
    print("dropped group alone, by cut-off (mean of the trades skipped):")
    for a in (-0.30, -0.20, -0.10, 0.0, 0.10, 0.20):
        cells = []
        for b in (-0.10, 0.0, 0.10, 0.25):
            drop = ~((ret > a) | (cash < b)) & ~np.isnan(ret) & ~np.isnan(cash)
            cells.append(f"B {100 * b:4.0f}%: {100 * r[drop].mean():6.2f}% ({drop.sum():3d})")
        print(f"  A {100 * a:4.0f}%  " + "   ".join(cells))


def who(signals, fund) -> None:
    from collections import Counter

    base, years, r = table(signals, fund)
    bad = np.array([GROUPS["down and net cash"](x["t"]) for x in base])
    for name, mask in (("down and net cash", bad), ("everything else", ~bad)):
        ts = [x["t"] for x, m in zip(base, mask, strict=True) if m]
        sectors = Counter(t["sector"] for t in ts)
        share = lambda f: 100 * np.mean([bool(f(t)) for t in ts if f(t) is not None])  # noqa: E731
        med = lambda k: float(np.median([float(t[k]) for t in ts if t[k] is not None]))  # noqa: E731
        print(f"{name}: {len(ts)} trades, mean {100 * r[mask].mean():.2f}%, median "
              f"{100 * np.median(r[mask]):.2f}%, winners {100 * (r[mask] > 0).mean():.0f}%")  # fmt: skip
        print("   sectors: " + ", ".join(f"{s} {100 * n / len(ts):.0f}%" for s, n in sectors.most_common(6)))
        print(f"   loss-making {share(FACTS['loss-making']):.0f}%, free cash flow negative "
              f"{share(FACTS['free cash flow negative']):.0f}%, issued over 10% "
              f"{share(FACTS['issued over 10%']):.0f}%, under $5 {share(FACTS['under $5']):.0f}%; "
              f"median size ${med('mcap') / 1e6:.0f}M, price ${med('close'):.2f}, year's return "
              f"{100 * med('ret250'):.0f}%, net cash {100 * med('netcash_price'):.0f}% of value, "
              f"jump {100 * med('ret2'):.0f}%")  # fmt: skip
        paths = [x for x, m in zip(base, mask, strict=True) if m]
        marks = {k: 100 * np.mean([x["stock"][min(k, len(x["stock"])) - 1] - 1 for x in paths])
                 for k in (1, 3, 5, 10, 15)}  # fmt: skip
        print("   gross since the entry, by session: " + "  ".join(f"{k}: {v:5.2f}%" for k, v in marks.items()))
        by_sector = {s: (100 * np.mean([q for q, t in zip(r[mask], ts, strict=True) if t["sector"] == s]), n)
                     for s, n in sectors.most_common(5)}  # fmt: skip
        print("   mean by sector: " + ", ".join(f"{s} {v:.2f}% ({n})" for s, (v, n) in by_sector.items()))


def wider(signals, fund) -> None:
    more = [t for t in load("A2") if t["ret2"] < 0.15]
    print(len(more), "signals with a jump of 10% to 15%")
    for name in ("all", "up or net debt", "down and net cash", "high or net debt"):
        keep = None if name == "all" else GROUPS[name]
        rows = per_trade(build(more, fund, keep=keep))
        cells = [f"{n} {100 * np.mean([x for y, x in rows if ok(y)]):5.2f}% "
                 f"({sum(ok(y) for y, _ in rows):3d})" for n, ok in SPANS]  # fmt: skip
        by = {y: np.mean([x for yy, x in rows if yy == y]) for y in sorted({y for y, _ in rows})}
        print(f"{name:18} " + "  ".join(cells) + f"  yrs+ {sum(v > 0 for v in by.values())}/{len(by)}")
        print("      " + " ".join(f"{y % 100:02d}:{100 * v:5.1f}" for y, v in by.items()))


def insider_trades(cell=("$50M-$300M", 1e5, 1, False, False), hold=15) -> list[dict]:
    """An insider cell's trades in this script's form, with the two facts the filter needs."""
    import insider_study as study

    kept = []
    for period in ("early", "choose", "late", "check"):
        d = study.rows(period)
        keep = study.pick(d, *cell)
        kept += [(int(p), str(day)[:10], float(dollars), float(c) / 2, float(c1) / 2)
                 for p, day, dollars, c, c1 in zip(d["permaticker"][keep], d["day"][keep],
                                                   d["dollars"][keep], d["cost"][keep],
                                                   d["cost1"][keep], strict=True)]  # fmt: skip
    settings = load_settings()
    store = DataStore(settings)
    base = settings.data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    con.execute("create table s (permaticker bigint, day date, dollars double, c0 double, c1 double)")
    con.executemany("insert into s values (?, ?, ?, ?, ?)", kept)
    facts = {}
    for name in ("early", "wide"):
        for p, day, a, b, c in con.sql(
            f"""select w.permaticker, w.day, w.ret250, w.netcash_price, w.high250
                from read_parquet('{base}/{name}_*.parquet') w join s
                  on s.permaticker = w.permaticker and s.day = w.day"""
        ).fetchall():
            facts[(p, day)] = (a, b, c)
    rows = con.sql(
        f"""with p as (
                select permaticker, date, symbol, ln(close / prev_close) as lr,
                       ln(close / open) as first,
                       row_number() over (partition by permaticker order by date) as rn
                from read_parquet('{store.root}/panel/*.parquet')
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'),
            k as (select s.*, p.rn, p.symbol from s join p
                  on p.permaticker = s.permaticker and p.date = s.day)
            select k.permaticker, k.day, k.symbol, k.dollars, k.c0, k.c1, p.date,
                   case when p.rn = k.rn + 1 then p.first else p.lr end as r
            from k join p on p.permaticker = k.permaticker
                         and p.rn between k.rn + 1 and k.rn + {hold}
            order by k.day, k.symbol, p.date"""
    ).fetchall()
    found: dict = {}
    for p, day, symbol, dollars, c0, c1, session, lr in rows:
        ret, cash, top = facts.get((p, day), (None, None, None))
        x = found.setdefault((day, symbol), {
            "t": {"day": day, "symbol": symbol, "volume": dollars / 1e12, "ret250": ret,
                  "netcash_price": cash, "high250": top, "side": {"auction": c0, "crossed": c1}},
            "dates": [], "stock": [], "fund": [], "hedge": 0.0, "extra": 0.0})  # fmt: skip
        x["dates"].append(session)
        x["stock"].append((x["stock"][-1] if x["stock"] else 1.0) * math.exp(lr))
        x["fund"].append(1.0)
    return list(found.values())


def insider(signals, fund) -> None:
    for label, cell in (("rule I ($100k+, one insider)", ("$50M-$300M", 1e5, 1, False, False)),
                        ("$100k+, two or more insiders", ("$50M-$300M", 1e5, 2, False, False))):  # fmt: skip
        trades = insider_trades(cell)
        for name in ("all", "up or net debt", "down and net cash", "up over the year", "net debt"):
            keep = (lambda t: True) if name == "all" else GROUPS[name]
            rows = per_trade([x for x in trades if keep(x["t"])])
            spans = (("2010-17", lambda y: 2010 <= y <= 2017), ("2006-09", lambda y: y <= 2009),
                     ("2018-23", lambda y: y >= 2018), ("2018-23 ex-2020", lambda y: y >= 2018 and y != 2020))  # fmt: skip
            cells = [f"{n} {100 * np.mean([x for y, x in rows if ok(y)]):5.2f}% "
                     f"({sum(ok(y) for y, _ in rows):4d})" for n, ok in spans]  # fmt: skip
            print(f"{label[:28]:28} {name:18} " + "  ".join(cells))


def by_year(label, trades) -> None:
    print(label)
    for basis in ("auction", "crossed"):
        daily, taken = run_book(trades, basis)
        totals = defaultdict(float)
        for d, x in daily.items():
            if d.year >= 2006:
                totals[d.year] += x
        print(f"   {basis:8} taken {taken:5d}  " + " ".join(f"{y % 100:02d}:{v:6,.0f}" for y, v in sorted(totals.items())))


def final(signals, fund) -> None:
    keep = GROUPS["up or net debt"]
    plain = build(signals, fund)
    kept = build(signals, fund, keep=keep)
    kept20 = build(signals, fund, keep=keep, ema=20)
    rule_i = insider_trades()
    two = insider_trades(("$50M-$300M", 1e5, 2, False, False))
    print(len(plain), "earnings trades;", len(kept), "after the filter;", len(rule_i), "rule I;", len(two), "two insiders")
    books = {
        "A50 as it is": plain,
        "A50, filtered": kept,
        "A50, filtered, 20-day exit": kept20,
        "rule I alone": rule_i,
        "A50 + rule I": plain + rule_i,
        "A50 filtered + rule I": kept + rule_i,
        "A50 filtered + two insiders": kept + two,
        "A50 filtered, 20-day exit + rule I": kept20 + rule_i,
    }
    for label, trades in books.items():
        describe(label, trades)
    for label in ("A50 as it is", "A50, filtered", "A50 filtered + rule I"):
        by_year(label, books[label])
    for slots in (5, 20):
        for label in ("A50, filtered", "A50 filtered + rule I"):
            for basis in ("auction", "crossed"):
                daily, taken = run_book(books[label], basis, slots)
                totals = defaultdict(float)
                for d, x in daily.items():
                    if d.year >= 2006:
                        totals[d.year] += x
                v = list(totals.values())
                print(f"{slots:2d} positions, {label:24} {basis:8} taken {taken:5d} ${np.mean(v):6,.0f} a year, "
                      f"worst {min(totals, key=totals.get)} ${min(v):6,.0f}, losing {sum(x < 0 for x in v)}")  # fmt: skip


def same_day(signals, fund) -> None:
    """Family 19's passing cell: the earnings 8-K is dated the day of the jump, so the signal
    is read that day and bought a session earlier than A50 would."""
    early = load("S50")
    keep = GROUPS["up or net debt"]
    a50 = build(signals, fund, keep=keep)
    s50_all = build(early, fund)
    s50 = build(early, fund, keep=keep)
    print(len(early), "same-day signals;", len(s50), "pass the test; A50Q has", len(a50))
    for label, trades in (("same day, all", s50_all), ("same day, quality", s50)):
        rows = per_trade(trades)
        cells = [f"{n} {100 * np.mean([x for y, x in rows if ok(y)]):5.2f}% "
                 f"({sum(ok(y) for y, _ in rows):3d})" for n, ok in SPANS]  # fmt: skip
        by = {y: np.mean([x for yy, x in rows if yy == y]) for y in sorted({y for y, _ in rows})}
        print(f"{label:20} " + "  ".join(cells) + f"  yrs+ {sum(v > 0 for v in by.values())}/{len(by)}")
        print("      " + " ".join(f"{y % 100:02d}:{100 * v:5.1f}" for y, v in by.items()))
    # One position a company: of two signals within 15 sessions, the earlier is kept.
    union, last = [], {}
    for x in sorted(a50 + s50, key=lambda x: (x["dates"][0], x["t"]["symbol"])):
        symbol, entry = x["t"]["symbol"], x["dates"][0]
        if symbol in last and entry <= last[symbol]:
            continue
        last[symbol] = x["dates"][-1]
        union.append(x)
    firsts = {(x["t"]["symbol"], x["t"]["day"]) for x in s50}
    took_early = sum((x["t"]["symbol"], x["t"]["day"]) in firsts for x in union)
    print(f"together, one position a company: {len(union)} trades, {took_early} entered on the "
          f"same-day signal, {len(union) - took_early} on A50's")  # fmt: skip
    books = {"A50Q alone": a50, "same day (quality) alone": s50, "both, one a company": union,
             "both, one a company, 20-day exit": None}  # fmt: skip
    a50e, s50e = build(signals, fund, keep=keep, ema=20), build(early, fund, keep=keep, ema=20)
    union_e, last = [], {}
    for x in sorted(a50e + s50e, key=lambda x: (x["dates"][0], x["t"]["symbol"])):
        symbol, entry = x["t"]["symbol"], x["dates"][0]
        if symbol in last and entry <= last[symbol]:
            continue
        last[symbol] = x["dates"][-1]
        union_e.append(x)
    books["both, one a company, 20-day exit"] = union_e
    for label, trades in books.items():
        describe(label, trades)
    for label in ("A50Q alone", "both, one a company"):
        by_year(label, books[label])
    for slots in (15, 20):
        for basis in ("auction", "crossed"):
            daily, taken = run_book(union, basis, slots)
            totals = defaultdict(float)
            for d, v in daily.items():
                if d.year >= 2006:
                    totals[d.year] += v
            v = list(totals.values())
            print(f"{slots} positions, both: {basis:8} taken {taken:5d} ${np.mean(v):6,.0f} a year, "
                  f"worst {min(totals, key=totals.get)} ${min(v):6,.0f}, losing {sum(x < 0 for x in v)}")  # fmt: skip


if __name__ == "__main__":
    what = sys.argv[1]
    data, market = load(), index()
    print(len(data), "signals;", len(market), "sessions of the index")
    {"quality": quality, "books": books, "cross": cross, "filtered": filtered, "chance": chance,
     "pairs": pairs, "cutoffs": cutoffs, "who": who, "wider": wider, "insider": insider,
     "final": final, "same_day": same_day}[what](data, market)  # fmt: skip
