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
        opened.bars_id, sealed_bars, build.DATA_VERSION, "unsealed",
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


def check(settings: Settings) -> dict:
    """Facts about the unsealed build that say nothing about any strategy: how many sessions it
    adds, how far each source reaches, and whether it reproduces the research build on every
    date before the seal."""
    authorise(settings, "unsealed build check")
    builds = folder(settings) / "builds"
    build_id = (builds / "CURRENT").read_text().strip()
    root = builds / build_id
    info = json.loads((root / "build.json").read_text())
    research = settings.data_dir / "builds" / info["research_build_id"]
    sealed_bars = folder(settings) / "bars" / info["sealed_bars_id"]
    seal_sql = f"DATE '{HOLDOUT_START.isoformat()}'"
    con = duckdb.connect()
    try:
        sessions, first, last = con.execute(
            f"select count(*), min(date), max(date) from "
            f"read_parquet('{sealed_bars}/calendar/*.parquet')"
        ).fetchone()
        reach = {}
        for table, column in (("events", "date"), ("actions", "date"), ("daily", "date")):
            reach[table] = con.execute(
                f"select max({column}) from '{root}/sharadar/{table}.parquet'"
            ).fetchone()[0]
        new_rows = con.execute(
            f"select count(*) from read_parquet('{root}/panel/*.parquet') where date >= {seal_sql}"
        ).fetchone()[0]
        shared = [
            r[0]
            for r in con.execute(
                f"describe select * from read_parquet('{research}/panel/*.parquet')"
            ).fetchall()
        ]
        columns = ", ".join(shared)
        before = (
            f"(select {columns} from read_parquet('{{}}/panel/*.parquet') where date < {seal_sql})"
        )
        mine, theirs = before.format(root), before.format(research)
        only_research, only_unsealed, rows = con.execute(
            f"""select (select count(*) from ({theirs} except {mine})),
                       (select count(*) from ({mine} except {theirs})),
                       (select count(*) from {theirs})"""
        ).fetchone()
    finally:
        con.close()
    return {
        "build_id": build_id, "research_build_id": info["research_build_id"],
        "holdout_sessions": sessions, "first_session": first, "last_session": last,
        "panel_rows_in_holdout": new_rows, "sharadar_reaches": reach,
        "rows_before_seal": rows, "rows_only_in_research_build": only_research,
        "rows_only_in_unsealed_build": only_unsealed,
        "same_before_seal": only_research == 0 and only_unsealed == 0,
    }  # fmt: skip


def covers(report: dict, end: date, *, slack_days: int = 7) -> bool:
    """Do the bars reach ``end``, and the filings and corporate actions to within a week of it?"""
    reach = report["sharadar_reaches"]
    floor = end - timedelta(days=slack_days)
    return report["last_session"] >= end and all(
        reach[t] is not None and reach[t] >= floor for t in ("events", "actions")
    )
