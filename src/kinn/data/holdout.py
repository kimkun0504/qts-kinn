"""The unsealed build: the owner's one look at the holdout (decision 0002).

It is the ordinary pipeline run over the open data and the sealed data together, written to its
own folder (``<data>/holdout/``). The research build and its seal are left exactly as they are.
Every entry point needs ``KINN_UNSEAL_TOKEN``, which only the owner sets, and is logged.

    <data>/holdout/bars/<sealed_bars_id>/     the sealed Massive days as Parquet
    <data>/holdout/builds/<build_id>/         master, panel and Sharadar tables, nothing censored
    <data>/holdout/builds/CURRENT             the build readers use with ``unseal=True``

Agents write and test this code; they never run it on the real sealed folder.
"""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path

import duckdb

from kinn.core.settings import HOLDOUT_START, Settings
from kinn.data import bars, build, raw, seal

FOLDER = "holdout"
UNSEALED_VERSION = "unsealed-2"  # bump when the unsealed tables must be rebuilt
TOLERANCE = 1e-9  # relative; see ``compare_panels``
CHECK_NAME = "check.json"
_REUSED = "^[A-Z.]+?[0-9]+$"  # Sharadar's name for a delisted company whose ticker was reused
AMBIGUOUS = "symbol also claimed by a company delisted after the seal; ambiguous, dropped"


def authorise(settings: Settings, source: str) -> None:
    """Raise ``HoldoutError`` unless the owner's token is set; log the unseal otherwise."""
    seal.check_range(
        HOLDOUT_START, HOLDOUT_START, source=source, unseal=True, log_dir=settings.data_dir
    )


def folder(settings: Settings) -> Path:
    return settings.data_dir / FOLDER


def identifiers(settings: Settings, sealed_dir: Path) -> dict:
    opened = build.paths(settings)
    sealed_bars = bars.bars_id(sealed_dir, holdout=True)
    zips = [raw.sharadar_zip(opened.snapshot, t) for t in build.SHARADAR_TABLES]
    build_id = raw.fingerprint(
        [(z.name, z.stat().st_size) for z in zips],
        opened.bars_id, sealed_bars, build.DATA_VERSION, UNSEALED_VERSION,
    )  # fmt: skip
    return {
        "build_id": build_id, "bars_id": opened.bars_id, "sealed_bars_id": sealed_bars,
        "research_build_id": opened.build_id, "snapshot": opened.snapshot,
    }  # fmt: skip


def build_unsealed(
    settings: Settings, sealed_dir: Path, *, budget_seconds: float = 3600.0, workers: int = 4
) -> tuple[str, list[str]]:
    """Convert the sealed bars and build the unsealed tables, in resumable steps. Returns
    (build id, what is still pending)."""
    authorise(settings, "unsealed build")
    ids = identifiers(settings, sealed_dir)
    if not raw.massive_files(sealed_dir, "minute", holdout=True):
        raise FileNotFoundError(f"no holdout-dated Massive files under {sealed_dir}")
    deadline = time.monotonic() + budget_seconds
    sealed_root = folder(settings) / "bars" / ids["sealed_bars_id"]
    while True:
        steps = bars.pending_steps(sealed_dir, sealed_root, holdout=True)
        if not steps:
            break
        done = bars.run_steps(steps, budget_seconds=deadline - time.monotonic(), workers=workers)
        if done < len(steps):
            return ids["build_id"], [f"{len(steps) - done} bar files"]
    open_root = settings.data_dir / "bars" / ids["bars_id"]
    build_root = folder(settings) / "builds" / ids["build_id"]
    info = {
        "build_id": ids["build_id"], "bars_id": ids["bars_id"],
        "sealed_bars_id": ids["sealed_bars_id"], "research_build_id": ids["research_build_id"],
        "data_version": build.DATA_VERSION, "unsealed": True,
        "sharadar_snapshot": ids["snapshot"].name,
    }  # fmt: skip
    pending = build.write_tables(
        build_root, [open_root, sealed_root], ids["snapshot"], info=info, seal_date=None,
        deadline=deadline,
    )  # fmt: skip
    if not pending:
        (folder(settings) / "builds" / "CURRENT").write_text(ids["build_id"] + "\n")
    return ids["build_id"], pending


def reach(settings: Settings) -> dict:
    """How far the unsealed build goes: sessions added and the last date of each source."""
    authorise(settings, "unsealed build check")
    root, info = current(settings)
    sealed_bars = folder(settings) / "bars" / info["sealed_bars_id"]
    con = duckdb.connect()
    try:
        sessions, first, last = con.execute(
            f"select count(*), min(date), max(date) from "
            f"read_parquet('{sealed_bars}/calendar/*.parquet')"
        ).fetchone()
        sources = {
            table: con.execute(
                f"select max(date) from '{root}/sharadar/{table}.parquet'"
            ).fetchone()[0]
            for table in ("events", "actions", "daily")
        }
        new_rows = con.execute(
            f"select count(*) from read_parquet('{root}/panel/*.parquet') "
            f"where date >= DATE '{HOLDOUT_START.isoformat()}'"
        ).fetchone()[0]
    finally:
        con.close()
    return {
        "build_id": info["build_id"], "research_build_id": info["research_build_id"],
        "holdout_sessions": sessions, "first_session": first, "last_session": last,
        "panel_rows_in_holdout": new_rows, "sharadar_reaches": sources,
    }  # fmt: skip


def current(settings: Settings) -> tuple[Path, dict]:
    builds = folder(settings) / "builds"
    root = builds / (builds / "CURRENT").read_text().strip()
    return root, json.loads((root / "build.json").read_text())


def compare_panels(research: Path, unsealed: Path, *, before: date = HOLDOUT_START) -> dict:
    """Compare two builds' panels on every date before ``before``, row by row and column by
    column. Counts and a few company names only; nothing dated on or after ``before`` is read
    into the result.

    Rows are matched on (date, permaticker). A decimal column counts as the same within
    ``TOLERANCE``: the 60-session return is a running sum of logarithms, and its last digits
    depend on which other companies were computed beside it and on the machine, so two correct
    builds differ there by about one part in 10^16. Every other difference is a real one.
    """
    con = duckdb.connect()
    try:
        cutoff = f"DATE '{before.isoformat()}'"
        described = {
            which: {
                r[0]: r[1]
                for r in con.execute(
                    f"describe select * from read_parquet('{root}/panel/*.parquet')"
                ).fetchall()
            }
            for which, root in (("r", research), ("u", unsealed))
        }
        keys = ("date", "permaticker")
        columns = [c for c in described["r"] if c in described["u"] and c not in keys]
        decimal = {c for c in columns if described["r"][c] in ("DOUBLE", "FLOAT")}
        years = sorted(
            int(p.stem.split("=")[1])
            for p in (research / "panel").glob("year=*.parquet")
            if int(p.stem.split("=")[1]) <= before.year
        )
        con.execute("create table gained (permaticker bigint, date date, symbol varchar)")
        con.execute("create table lost (permaticker bigint, date date, symbol varchar)")
        totals = dict.fromkeys(("rows", "common"), 0)
        differs = dict.fromkeys(columns, 0)
        beyond = dict.fromkeys(columns, 0)
        largest = dict.fromkeys(decimal, 0.0)
        for year in years:
            mine = unsealed / "panel" / f"year={year}.parquet"
            source = f"(select *, true as present from '{{}}' where date < {cutoff})"
            r = source.format(research / "panel" / f"year={year}.parquet")
            u = source.format(mine) if mine.exists() else f"(select * from {r} where false)"
            parts = ["count(*) filter (r.present)", "count(*) filter (r.present and u.present)"]
            for c in columns:
                differ = f"r.present and u.present and r.{c} is distinct from u.{c}"
                parts.append(f"count(*) filter ({differ})")
                if c in decimal:
                    close = (
                        f"coalesce(abs(r.{c} - u.{c}) <= {TOLERANCE} * "
                        f"greatest(1, abs(r.{c}), abs(u.{c})), false)"
                    )
                    parts.append(f"count(*) filter ({differ} and not {close})")
                    parts.append(f"coalesce(max(abs(r.{c} - u.{c})), 0)")
            row = con.execute(
                f"select {', '.join(parts)} from {r} r full join {u} u "
                f"on r.date = u.date and r.permaticker = u.permaticker"
            ).fetchone()
            totals["rows"] += row[0]
            totals["common"] += row[1]
            at = 2
            for c in columns:
                differs[c] += row[at]
                at += 1
                if c in decimal:
                    beyond[c] += row[at]
                    largest[c] = max(largest[c], float(row[at + 1]))
                    at += 2
                else:
                    beyond[c] = differs[c]
            con.execute(
                f"insert into gained select u.permaticker, u.date, u.symbol "
                f"from {u} u anti join {r} r "
                f"on r.date = u.date and r.permaticker = u.permaticker"
            )
            con.execute(
                f"insert into lost select r.permaticker, r.date, r.symbol "
                f"from {r} r anti join {u} u "
                f"on r.date = u.date and r.permaticker = u.permaticker"
            )
        for which, root in (("r", research), ("u", unsealed)):
            con.execute(
                f"create view sec_{which} as select * from '{root}/master/security_master.parquet'"
            )
        con.execute(
            f"create view hist_u as select * from '{unsealed}/master/symbol_history.parquet'"
        )
        # Companies the research build cannot match and the unsealed build can.
        con.execute(
            f"""create view reused as
                select u.permaticker from sec_u u join sec_r r using (permaticker)
                where u.delisted and not r.delisted and regexp_matches(u.ticker, '{_REUSED}')"""
        )
        gained = _groups(
            con,
            """select t.permaticker, t.date,
                      case when t.permaticker in (select permaticker from reused)
                             then 'delisted after the seal; ticker reused since'
                           when t.permaticker not in (select permaticker from sec_r)
                             then 'left out of the research build'
                           else 'unexplained' end as why
               from gained t""",
        )
        # A research row is expected to go when its symbol, on that date, is also claimed by
        # one of those companies: two claims on one symbol are ambiguous and both are dropped
        # (the panel's standing rule).
        lost = _groups(
            con,
            f"""select t.permaticker, t.date,
                       case when c.permaticker is not null then '{AMBIGUOUS}'
                            else 'unexplained' end as why
                from lost t left join (
                    select distinct l.permaticker, l.date from lost l
                    join hist_u h on h.symbol = l.symbol and l.date >= h.valid_from
                     and l.date < h.valid_to and h.permaticker <> l.permaticker
                    join reused e on e.permaticker = h.permaticker) c
                  on c.permaticker = t.permaticker and c.date = t.date""",
        )
    finally:
        con.close()
    out = {
        "rows_before_seal": totals["rows"],
        "rows_in_both": totals["common"],
        "rows_missing_from_unsealed": lost,
        "rows_only_in_unsealed": gained,
        "columns_that_differ": {c: n for c, n in differs.items() if n},
        "columns_beyond_tolerance": {c: n for c, n in beyond.items() if n},
        "largest_decimal_gap": {c: v for c, v in largest.items() if v},
    }
    out["exact"] = not (lost or gained or out["columns_that_differ"])
    out["same_before_seal"] = not (
        out["columns_beyond_tolerance"] or "unexplained" in gained or "unexplained" in lost
    )
    return out


def _groups(con: duckdb.DuckDBPyConnection, classified: str) -> dict:
    """``classified`` yields (permaticker, date, why); summed by reason, five examples each."""
    rows = con.execute(
        f"""with per as (
                select permaticker, why, count(*) as n, min(date) as first, max(date) as last
                from ({classified}) group by 1, 2)
            select p.why, sum(p.n), count(*),
                   list({{'ticker': coalesce(u.ticker, r.ticker), 'rows': p.n,
                          'first': p.first, 'last': p.last}} order by p.n desc)[1:5]
            from per p
            left join sec_u u on u.permaticker = p.permaticker
            left join sec_r r on r.permaticker = p.permaticker
            group by 1 order by 2 desc"""
    ).fetchall()
    return {
        why: {"rows": int(n), "companies": companies, "largest": examples}
        for why, n, companies, examples in rows
    }


def check(settings: Settings) -> dict:
    """Facts about the unsealed build that say nothing about any strategy: how many sessions it
    adds, how far each source reaches, and whether it reproduces the research build on every
    date before the seal. The verdict is saved beside the build; the holdout run reads it."""
    report = reach(settings)
    root, info = current(settings)
    research = settings.data_dir / "builds" / info["research_build_id"]
    report.update(compare_panels(research, root))
    (root / CHECK_NAME).write_text(json.dumps(report, indent=2, default=str) + "\n")
    return report


def checked(settings: Settings) -> bool:
    """Has the current unsealed build passed ``check``?"""
    root, _ = current(settings)
    path = root / CHECK_NAME
    return path.exists() and bool(json.loads(path.read_text())["same_before_seal"])


def covers(report: dict, end: date, *, slack_days: int = 7) -> bool:
    """Do the bars reach ``end``, and the filings and corporate actions to within a week of it?"""
    sources = report["sharadar_reaches"]
    floor = end - timedelta(days=slack_days)
    return report["last_session"] >= end and all(
        sources[t] is not None and sources[t] >= floor for t in ("events", "actions")
    )


TRADE_KEY = ("day", "symbol", "tag", "quantity", "signal_minute", "entry_minute", "exit_minute")
TRADE_MONEY = ("entry_price", "exit_price", "net", "net_2x")


def explained_additions(settings: Settings) -> list[int]:
    """Companies the unsealed build can match before the seal and the research build cannot:
    delisted after the seal, with the ticker reused since (see ``compare_panels``)."""
    root, info = current(settings)
    research = settings.data_dir / "builds" / info["research_build_id"]
    rows = duckdb.sql(
        f"""select u.permaticker from '{root}/master/security_master.parquet' u
            join '{research}/master/security_master.parquet' r using (permaticker)
            where u.delisted and not r.delisted and regexp_matches(u.ticker, '{_REUSED}')"""
    ).fetchall()
    return [r[0] for r in rows]


def compare_trades(reference: Path, candidate: Path, *, explained: list[int] = ()) -> dict:
    """Trade-for-trade comparison of two runs of one config. ``explained`` are companies whose
    extra trades in ``candidate`` are expected (``explained_additions``)."""
    con = duckdb.connect()
    try:
        ref, new = (f"'{d}/trades.parquet'" for d in (reference, candidate))
        on = " and ".join(f"a.{k} = b.{k}" for k in TRADE_KEY)
        near = " and ".join(
            f"abs(a.{c} - b.{c}) <= 1e-6 * greatest(1, abs(a.{c}))" for c in TRADE_MONEY
        )
        known = ", ".join(str(int(p)) for p in explained) or "null"
        n_ref, n_new, net_ref, net_new = con.execute(
            f"""select (select count(*) from {ref}), (select count(*) from {new}),
                       (select sum(net) from {ref}), (select sum(net) from {new})"""
        ).fetchone()
        matched, same_money = con.execute(
            f"select count(*), count(*) filter ({near}) from {ref} a join {new} b on {on}"
        ).fetchone()
        shown = "day, symbol, tag, quantity, entry_minute"
        missing = con.execute(
            f"select {shown} from {ref} a anti join {new} b on {on} order by 1, 2, 3"
        ).fetchall()
        extra = con.execute(
            f"""select {shown}, permaticker in ({known}) from {new} a anti join {ref} b
                on {on}
                order by 1, 2, 3"""
        ).fetchall()
    finally:
        con.close()
    unexplained = [row[:-1] for row in extra if not row[-1]]
    return {
        "research_trades": n_ref, "unsealed_trades": n_new, "matched": matched,
        "matched_with_same_prices_and_profit": same_money,
        "research_net": round(net_ref or 0.0, 2), "unsealed_net": round(net_new or 0.0, 2),
        "missing_from_unsealed": len(missing), "extra_in_unsealed": len(extra),
        "extra_unexplained": len(unexplained),
        "examples_missing": [list(map(str, r)) for r in missing[:10]],
        "examples_extra_unexplained": [list(map(str, r)) for r in unexplained[:10]],
        "identical": n_ref == n_new == matched == same_money,
        "passed": not missing and matched == same_money and not unexplained,
    }  # fmt: skip
