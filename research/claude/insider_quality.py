"""Which insider-buying signals fail (strategies/insider_buying/HYPOTHESIS.md, addendum of
2026-11-17 00:01 ET): rule I's trades split on ten facts known at the signal.

    cd research/claude && uv run python insider_quality.py
"""

from __future__ import annotations

import itertools
import tempfile

import duckdb
import numpy as np

import insider_study as study
from kinn.core.settings import load_settings

RULE_I = ("$50M-$300M", 1e5, 1, False, False)
SPANS = (("2010-17", lambda y: (y >= 2010) & (y <= 2017)), ("2006-09", lambda y: y <= 2009),
         ("2018-23", lambda y: y >= 2018), ("no 2020", lambda y: (y >= 2018) & (y != 2020)))  # fmt: skip


def load() -> dict[str, np.ndarray]:
    """Rule I's trades of every period with the facts joined from the daily tables."""
    parts = []
    for period in ("early", "choose", "late", "check"):
        d = study.rows(period)
        keep = study.pick(d, *RULE_I)
        parts.append({k: v[keep] for k, v in d.items()})
    d = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    base = load_settings().data_dir / "research" / "swing"
    con = duckdb.connect()
    con.execute(
        f"set threads=3; set memory_limit='1500MB'; set temp_directory='{tempfile.mkdtemp()}'"
    )
    con.execute("create table s (permaticker bigint, day date)")
    con.executemany("insert into s values (?, ?)",
                    [(int(p), str(day)[:10]) for p, day in zip(d["permaticker"], d["day"], strict=True)])  # fmt: skip
    facts = {}
    for name in ("early", "wide"):
        rows = con.sql(
            f"""select w.permaticker, w.day::varchar, w.ret250, w.netcash_price, w.ni_pos,
                       w.fcf_price, w.issue, w.high250
                from read_parquet('{base}/{name}_*.parquet') w join s
                  on s.permaticker = w.permaticker and s.day = w.day"""
        ).fetchall()
        facts.update({(p, day): rest for p, day, *rest in rows})
    cols = list(zip(*[facts.get((int(p), str(day)[:10]), (None,) * 6)
                      for p, day in zip(d["permaticker"], d["day"], strict=True)], strict=True))  # fmt: skip
    for name, col in zip(("ret250", "netcash", "ni_pos", "fcf", "issue", "high250"), cols, strict=True):
        d[name] = np.array([np.nan if v is None else float(v) for v in col])
    d["net"] = (d["g15"] - d["cost"]).astype(float)
    d["crossed"] = (d["g15"] - d["cost1"]).astype(float)
    d["year"] = d["yr"].astype(int)
    return d


def facts_of(d) -> dict[str, np.ndarray]:
    """Each fact as 1 (true), 0 (false) or -1 (unknown)."""

    def flag(values, test):
        out = np.where(test(values), 1, 0)
        return np.where(np.isnan(values), -1, out)

    return {
        "down over the year": flag(d["ret250"], lambda v: v <= 0),
        "net cash": flag(d["netcash"], lambda v: v >= 0),
        "lost money last quarter": flag(d["ni_pos"], lambda v: v == 0),
        "free cash flow negative": flag(d["fcf"], lambda v: v < 0),
        "issued over 10%": flag(d["issue"], lambda v: v > 0.10),
        "under $5": (d["close"].astype(float) < 5).astype(int),
        "not at a 250-day high": flag(d["high250"], lambda v: v <= 0),
        "an officer bought": d["officer"].astype(bool).astype(int),
        "0.2% of the company or more": (d["dollars"] / d["mcap"] >= 0.002).astype(int),
        "only a ten-percent owner": d["only_ten"].astype(bool).astype(int),
    }


def cells(d, mask) -> str:
    out = []
    for name, test in SPANS:
        m = mask & test(d["year"])
        out.append(f"{name} {100 * d['net'][m].mean() if m.any() else float('nan'):5.2f}% ({m.sum():4d})")
    return "  ".join(out)


def by_year(d, mask) -> dict[int, float]:
    return {int(y): float(d["net"][mask & (d["year"] == y)].mean())
            for y in sorted(set(d["year"][mask]))}  # fmt: skip


def main() -> None:
    d = load()
    f = facts_of(d)
    everyone = np.ones(len(d["net"]), bool)
    base = {name: d["net"][test(d["year"])].mean() for name, test in SPANS}
    print(f"rule I: {len(d['net'])} trades   {cells(d, everyone)}")
    print("   by year: " + " ".join(f"{y % 100:02d}:{100 * v:4.1f}" for y, v in by_year(d, everyone).items()))
    print("\nsingle splits (a side counts if it beats all trades in every span)")
    for name, values in f.items():
        for side, label in ((1, name), (0, "not: " + name)):
            mask = values == side
            better = all(d["net"][mask & test(d["year"])].mean() > base[n] for n, test in SPANS)
            print(f"  {label:36} {cells(d, mask)}" + ("   <- better in every span" if better else ""))
    first, rest = SPANS[0][1](d["year"]), ~SPANS[0][1](d["year"]) & (d["year"] != 2020)
    found = []
    for a, b in itertools.combinations(f, 2):
        for va, vb in itertools.product((1, 0), repeat=2):
            mask = (f[a] == va) & (f[b] == vb)
            if (mask & first).sum() < 150 or (mask & rest).sum() < 150:
                continue
            label = f"{a if va else 'not ' + a} & {b if vb else 'not ' + b}"
            found.append((d["net"][mask & first].mean(), d["net"][mask & rest].mean(), label, mask))
    found.sort(key=lambda x: x[0])
    x, y = np.array([g[0] for g in found]), np.array([g[1] for g in found])
    rank = lambda v: np.argsort(np.argsort(v))  # noqa: E731
    tenth = max(1, len(found) // 10)
    print(f"\n{len(found)} pair groups; rank correlation between 2010-17 and the other years "
          f"(no 2020): {np.corrcoef(rank(x), rank(y))[0, 1]:.2f}")  # fmt: skip
    print(f"worst tenth in 2010-17: {100 * x[:tenth].mean():.2f}% then, {100 * y[:tenth].mean():.2f}% "
          f"elsewhere; best tenth: {100 * x[-tenth:].mean():.2f}% then, {100 * y[-tenth:].mean():.2f}% "
          f"elsewhere; all trades {100 * d['net'][first].mean():.2f}% and {100 * d['net'][rest].mean():.2f}%")  # fmt: skip
    print("the eight best groups of 2010-17, and the eight worst:")
    for g in found[-8:][::-1] + found[:8]:
        years = by_year(d, g[3])
        print(f"  {g[2][:62]:62} {cells(d, g[3])}  yrs+ {sum(v > 0 for v in years.values())}/{len(years)} "
              f"21:{100 * years.get(2021, float('nan')):4.1f} 22:{100 * years.get(2022, float('nan')):4.1f}")  # fmt: skip


if __name__ == "__main__":
    main()
