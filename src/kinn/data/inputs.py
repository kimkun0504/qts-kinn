"""Versioned inputs: datasets a strategy may read that are not part of the data build.

An input is built from raw files into ``<data>/inputs/<name>/<input_id>/`` and never changes
once written. ``input_id`` is a hash of the input's code version and the raw files it was
built from, so new raw files or new parsing give a new id; ``CURRENT`` names the latest. A
run that uses an input records its id in the manifest and reads exactly that one.

``form4`` is the SEC's Insider Transactions Data Sets (Forms 4 and 4/A, non-derivative
transactions), one row per filing, transaction code and direction. A strategy may use a
filing from the first session after its filing date; :meth:`kinn.data.store.DataStore.form4`
enforces that. Rows dated on or after the holdout seal are never written.

``form8k`` is different in one way: the 8-K item codes are already part of the data build
(Sharadar's EVENTS table), so nothing is built for it. Its id is a hash of its code version
and the build's id, and :meth:`kinn.data.store.DataStore.form8k` reads the build the run is
pinned to, under the same next-session rule.
"""

from __future__ import annotations

import csv
import dataclasses
import gzip
import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from kinn.core.settings import HOLDOUT_START, Settings
from kinn.data import quotes, seal
from kinn.data.raw import sharadar_zip

FORM4_VERSION = "form4-1"
FORM8K_VERSION = "form8k-1"
FORM8K_TIMED_VERSION = "form8k-timed-1"
NEW_YORK = ZoneInfo("America/New_York")
TIMED_SCHEMA = pa.schema(
    [
        ("day", pa.date32()),
        ("permaticker", pa.int64()),
        ("issuer_cik", pa.int64()),
        ("accession", pa.string()),
        ("form", pa.string()),
        ("filed", pa.date32()),
        ("accepted", pa.timestamp("us", tz="UTC")),
        ("items", pa.list_(pa.string())),
        ("earnings", pa.bool_()),
        ("usable_minute", pa.int16()),
    ]
)
# The items of Form 8-K, as Sharadar's event codes (item X.0Y is code XY). Other codes in the
# EVENTS table are Sharadar's own and are passed through without an item number.
FORM8K_ITEMS = frozenset(
    (11, 12, 13, 14, 15, 21, 22, 23, 24, 25, 26, 31, 32, 33, 41, 42, 51, 52, 53, 54, 55, 56,
     57, 58, 61, 62, 63, 64, 65, 71, 81, 91)
)  # fmt: skip
EARNINGS_CODE = 22  # item 2.02, results of operations and financial condition
NAMES = ("form4", "form8k", "form8k_timed", "nbbo_replenishment")
CURRENT_NAME = "CURRENT"
_TABLES = ("SUBMISSION", "REPORTINGOWNER", "NONDERIV_TRANS")
_READ = "read_csv('{}/{}.tsv', delim='\t', header=true, all_varchar=true, quote='')"


class InputError(RuntimeError):
    """An input is missing, or does not cover what was asked of it."""


def root(settings: Settings, name: str) -> Path:
    return settings.data_dir / "inputs" / name


def _form4_raw(settings: Settings) -> list[Path]:
    return sorted((settings.raw_dir / "sec" / "insiders").glob("*_form345.zip"))


def form4_id(settings: Settings) -> str:
    """The id the current raw files and code version give."""
    files = [(p.name, p.stat().st_size) for p in _form4_raw(settings)]
    if not files:
        raise InputError(
            "no insider files under raw/sec/insiders; the owner downloads them with "
            "tools/owner/download_insiders.py"
        )
    text = json.dumps({"version": FORM4_VERSION, "files": files}, sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()[:10]


def form8k_id(build_id: str) -> str:
    """The id of the form8k input as read from one data build."""
    text = json.dumps({"version": FORM8K_VERSION, "build": build_id}, sort_keys=True)
    return hashlib.sha256(text.encode()).hexdigest()[:10]


def item(code: int) -> str:
    """The 8-K item a Sharadar event code stands for: 22 is "2.02"."""
    return f"{code // 10}.{code % 10:02d}"


def build_form4(settings: Settings) -> str:
    """Build the form4 input from the raw zips (read only) if it is not built. Returns its id."""
    input_id = form4_id(settings)
    out = root(settings, "form4") / input_id
    if not (out / "input.json").exists():
        out.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as scratch:
            con = duckdb.connect()
            con.execute(f"set threads=2; set memory_limit='1500MB'; set temp_directory='{scratch}'")
            parts = []
            for path in _form4_raw(settings):
                folder = Path(scratch) / path.stem
                with zipfile.ZipFile(path) as z:
                    for table in _TABLES:
                        z.extract(f"{table}.tsv", folder)
                part = Path(scratch) / f"{path.stem}.parquet"
                con.execute(f"copy ({_form4_sql(folder)}) to '{part}' (format parquet)")
                parts.append(str(part))
                for table in _TABLES:
                    (folder / f"{table}.tsv").unlink()
            tmp = out / "transactions.parquet.tmp"
            con.execute(
                f"""copy (select * from read_parquet({parts})
                          order by filed, accession, transaction_code, acquired)
                    to '{tmp}' (format parquet, compression zstd, row_group_size 100000)"""
            )
            os.replace(tmp, out / "transactions.parquet")
            rows, first, last = con.execute(
                f"""select count(*), min(filed)::varchar, max(filed)::varchar
                    from '{out / "transactions.parquet"}'"""
            ).fetchall()[0]
            con.close()
        info = {
            "input": "form4", "version": FORM4_VERSION, "input_id": input_id,
            "raw_files": [p.name for p in _form4_raw(settings)], "rows": rows,
            "first_filed": first, "last_filed": last,
            "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }  # fmt: skip
        tmp = out / "input.json.tmp"
        tmp.write_text(json.dumps(info, indent=2) + "\n")
        os.replace(tmp, out / "input.json")
    (root(settings, "form4") / CURRENT_NAME).write_text(input_id + "\n")
    return input_id


def _form4_sql(folder: Path) -> str:
    seal = HOLDOUT_START.isoformat()
    return f"""
        with t as (
            select ACCESSION_NUMBER as a, TRANS_CODE as code,
                   coalesce(TRANS_ACQUIRED_DISP_CD, '') as acquired,
                   sum(try_cast(TRANS_SHARES as double)) as shares,
                   sum(try_cast(TRANS_SHARES as double) * try_cast(TRANS_PRICEPERSHARE as double))
                       filter (try_cast(TRANS_PRICEPERSHARE as double) > 0) as amount,
                   min(try_strptime(TRANS_DATE, '%d-%b-%Y')::date) as first_traded,
                   max(try_strptime(TRANS_DATE, '%d-%b-%Y')::date) as last_traded,
                   count(*) as lines
            from {_READ.format(folder, "NONDERIV_TRANS")}
            where TRANS_CODE is not null and TRANS_CODE <> '' group by 1, 2, 3),
        o as (
            select ACCESSION_NUMBER as a, min(RPTOWNERCIK) as owner_cik,
                   arg_min(RPTOWNERNAME, RPTOWNERCIK) as owner_name, count(*) as owners,
                   coalesce(bool_or(RPTOWNER_RELATIONSHIP ilike '%officer%'), false) as officer,
                   coalesce(bool_or(RPTOWNER_RELATIONSHIP ilike '%director%'), false) as director,
                   coalesce(bool_or(RPTOWNER_RELATIONSHIP ilike '%tenpercent%'), false)
                       as ten_percent_owner,
                   arg_min(RPTOWNER_TITLE, RPTOWNERCIK) as title
            from {_READ.format(folder, "REPORTINGOWNER")} group by 1)
        select s.ACCESSION_NUMBER as accession, s.ISSUERCIK as issuer_cik,
               s.ISSUERNAME as issuer_name, upper(trim(s.ISSUERTRADINGSYMBOL)) as symbol,
               try_strptime(s.FILING_DATE, '%d-%b-%Y')::date as filed,
               s.DOCUMENT_TYPE as document_type, t.code as transaction_code, t.acquired,
               t.shares, t.amount,
               case when t.code = 'P' and t.acquired = 'A' then t.amount end as purchase_amount,
               t.first_traded, t.last_traded, t.lines, o.owner_cik, o.owner_name, o.owners,
               o.officer, o.director, o.ten_percent_owner, o.title
        from {_READ.format(folder, "SUBMISSION")} s
        join t on t.a = s.ACCESSION_NUMBER left join o on o.a = s.ACCESSION_NUMBER
        where s.DOCUMENT_TYPE in ('4', '4/A')
          and try_strptime(s.FILING_DATE, '%d-%b-%Y')::date < DATE '{seal}'"""


def _content_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timed_identity(tickers: Path, master: Path) -> tuple[dict[int, int], dict]:
    """Only CIK/identity fields; ambiguous issuer-to-security mappings are excluded."""
    allowed = set(pq.read_table(master, columns=["permaticker"])["permaticker"].to_pylist())
    by_cik, by_company = defaultdict(set), defaultdict(set)
    rejected = Counter()
    with zipfile.ZipFile(tickers) as archive:
        (member,) = archive.namelist()
        with archive.open(member) as handle:
            reader = pacsv.open_csv(
                handle,
                convert_options=pacsv.ConvertOptions(
                    include_columns=["table", "permaticker", "secfilings"],
                    column_types={
                        "table": pa.string(),
                        "permaticker": pa.int64(),
                        "secfilings": pa.string(),
                    },
                ),
            )
            for batch in reader:
                for row in batch.to_pylist():
                    company = row["permaticker"]
                    if row["table"] != "SEP" or company not in allowed:
                        continue
                    match = re.search(r"[?&]CIK=0*(\d+)(?:&|$)", row["secfilings"] or "", re.I)
                    if not match or int(match[1]) <= 0:
                        rejected["missing_cik"] += 1
                        continue
                    cik = int(match[1])
                    by_cik[cik].add(company)
                    by_company[company].add(cik)
    mapping = {
        cik: next(iter(companies))
        for cik, companies in by_cik.items()
        if len(companies) == 1 and len(by_company[next(iter(companies))]) == 1
    }
    rejected["ambiguous_ciks"] = len(by_cik) - len(mapping)
    return mapping, dict(rejected)


def _timed_record(row: dict) -> dict:
    """Parse one accession; source dates and timestamps must pass the seal independently."""
    from datetime import date

    if row.get("form") != "8-K":
        raise ValueError("other_form")
    try:
        filed = date.fromisoformat(row["filed"])
    except (ValueError, TypeError, KeyError):
        raise ValueError("invalid_filed") from None
    if filed >= HOLDOUT_START:
        raise ValueError("sealed_filed")
    try:
        accepted = datetime.fromisoformat(row["accepted"])
        if accepted.tzinfo is None or accepted.utcoffset() is None:
            raise ValueError
        accepted = accepted.astimezone(UTC)
        local = accepted.astimezone(NEW_YORK)
    except (ValueError, TypeError, KeyError, OverflowError):
        raise ValueError("invalid_timestamp") from None
    if local.date() >= HOLDOUT_START:
        raise ValueError("sealed_accepted")
    accession = row.get("accession")
    if not isinstance(accession, str) or not accession.strip():
        raise ValueError("missing_accession")
    raw_items = row.get("items")
    if not isinstance(raw_items, str):
        raise ValueError("invalid_items")
    items = tuple(sorted({x.strip() for x in raw_items.split(",") if x.strip()}))
    if any(not re.fullmatch(r"[1-9]\.\d{2}", x) for x in items):
        raise ValueError("invalid_items")
    try:
        cik = int(row["cik"])
        if cik <= 0:
            raise ValueError
    except (ValueError, TypeError, KeyError):
        raise ValueError("invalid_cik") from None
    return {
        "day": local.date(),
        "cik": cik,
        "accession": accession.strip(),
        "form": "8-K",
        "filed": filed,
        "accepted": accepted,
        "items": list(items),
        "earnings": "2.02" in items,
        "usable_minute": local.hour * 60 + local.minute + 1,
    }


def build_form8k_timed(settings: Settings) -> str:
    """Build only the separately authorized timed input; never rebuild bars or panel."""
    pointer = settings.data_dir / "builds" / "CURRENT"
    if not pointer.exists():
        raise InputError("the timed input needs an existing pinned data build")
    build_id = pointer.read_text().strip()
    build_root = pointer.parent / build_id
    build_info = json.loads((build_root / "build.json").read_text())
    source = settings.raw_dir / "sec" / "filing_times" / "8k.jsonl.gz"
    if not source.is_file():
        raise InputError("existing raw SEC 8-K timestamp file is missing; no download attempted")
    tickers = sharadar_zip(
        settings.raw_dir / "sharadar" / build_info["sharadar_snapshot"], "TICKERS"
    )
    master = build_root / "master" / "security_master.parquet"
    hashes = {
        "sec_8k": _content_hash(source),
        "tickers": _content_hash(tickers),
        "master": _content_hash(master),
    }
    identity = {"version": FORM8K_TIMED_VERSION, "data_build_id": build_id, "sha256": hashes}
    input_id = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()[:10]
    base = root(settings, "form8k_timed")
    base.mkdir(parents=True, exist_ok=True)
    out = base / input_id
    if not (out / "input.json").exists():
        mapping, identity_rejections = _timed_identity(tickers, master)
        if not mapping:
            raise InputError("timed input has no unambiguous issuer identities")
        rejected, buffer = Counter(), []
        coverage_start = coverage_end = None
        # Write a bounded batch at a time, then reject conflicting accessions as a group.
        with tempfile.TemporaryDirectory(prefix=".timed-", dir=base) as staging:
            staging = Path(staging)
            raw_table = staging / "staged.parquet"
            with pq.ParquetWriter(raw_table, TIMED_SCHEMA, compression="zstd") as writer:
                with gzip.open(source, "rt", encoding="utf-8") as handle:
                    for line in handle:
                        try:
                            row = json.loads(line)
                            if not isinstance(row, dict):
                                raise ValueError("invalid_json")
                            record = _timed_record(row)
                        except (ValueError, TypeError) as error:
                            reason = (
                                "invalid_json"
                                if isinstance(error, json.JSONDecodeError)
                                else str(error)
                            )
                            rejected[reason] += 1
                            continue
                        day = record["day"]
                        coverage_start = min(coverage_start, day) if coverage_start else day
                        coverage_end = max(coverage_end, day) if coverage_end else day
                        cik = record.pop("cik")
                        company = mapping.get(cik)
                        if company is None:
                            rejected["unmapped_or_ambiguous_cik"] += 1
                        record["permaticker"] = company
                        record["issuer_cik"] = cik
                        if not record["items"]:
                            rejected["empty_items_retained"] += 1
                        buffer.append(record)
                        if len(buffer) >= 10000:
                            writer.write_table(pa.Table.from_pylist(buffer, schema=TIMED_SCHEMA))
                            buffer.clear()
                if buffer:
                    writer.write_table(pa.Table.from_pylist(buffer, schema=TIMED_SCHEMA))
            con = duckdb.connect()
            try:
                con.execute("set threads=2")
                con.execute("set memory_limit='1500MB'")
                con.execute("set temp_directory=?", [str(staging / "spill")])
                con.execute(
                    "create temp table distinct_rows as select distinct * from read_parquet(?)",
                    [str(raw_table)],
                )
                # The same accession must not acquire a different issuer, time, date or items.
                con.execute("""create temp table conflicts as select accession from distinct_rows
                               group by accession having count(*) > 1""")
                rejected["conflicting_accessions"] = con.sql(
                    "select count(*) from conflicts"
                ).fetchall()[0][0]
                rejected["exact_duplicates"] = (
                    pq.read_metadata(raw_table).num_rows
                    - con.sql("select count(*) from distinct_rows").fetchall()[0][0]
                )
                target = staging / "reports.parquet"
                con.execute(
                    """copy (select * from distinct_rows
                    where permaticker is not null
                      and accession not in (select accession from conflicts)
                    order by day, accepted, accession, permaticker)
                    to ? (format parquet, compression zstd)""",
                    [str(target)],
                )
                n, first, last, last_filed = con.execute(
                    "select count(*), min(day), max(day), max(filed) from read_parquet(?)",
                    [str(target)],
                ).fetchall()[0]
            finally:
                con.close()
            if not n or coverage_start is None:
                raise InputError("timed input has no usable records after parsing/identity checks")
            meta = {
                **identity,
                "input": "form8k_timed",
                "input_id": input_id,
                "rows": n,
                "first_accepted_day": first.isoformat(),
                "last_accepted_day": last.isoformat(),
                "last_filed": last_filed.isoformat(),
                "coverage_start": coverage_start.isoformat(),
                "coverage_end": coverage_end.isoformat(),
                "coverage_basis": (
                    "observed valid original filing archive envelope; completeness unverified"
                ),
                "rejections": dict(rejected),
                "identity_rejections": identity_rejections,
                "raw_files": [source.name, tickers.name],
                "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }
            (staging / "input.json").write_text(json.dumps(meta, indent=2) + "\n")
            # Only completed, immutable outputs are published, with metadata written last.
            out.mkdir(parents=True, exist_ok=True)
            os.replace(target, out / "reports.parquet")
            os.replace(staging / "input.json", out / "input.json")
    if not (out / "reports.parquet").is_file():
        raise InputError("the immutable timed input is incomplete; no current pointer changed")
    tmp = base / "CURRENT.tmp"
    tmp.write_text(input_id + "\n")
    os.replace(tmp, base / CURRENT_NAME)
    return input_id


def current(settings: Settings, name: str) -> str:
    pointer = root(settings, name) / CURRENT_NAME
    if not pointer.exists():
        raise InputError(f"the {name} input is not built; run `kinn inputs build {name}`")
    return pointer.read_text().strip()


def info(settings: Settings, name: str, input_id: str | None = None) -> dict:
    input_id = input_id or current(settings, name)
    path = root(settings, name) / input_id / "input.json"
    if not path.exists():
        raise InputError(f"{name} input {input_id} is not on disk under {path.parent}")
    return json.loads(path.read_text())


NBBO_SNAPSHOT = pa.struct(
    [
        ("sip_timestamp", pa.int64()),
        ("bid_price", pa.float64()),
        ("ask_price", pa.float64()),
        ("bid_size", pa.int64()),
        ("ask_size", pa.int64()),
    ]
)
NBBO_SCHEMA = pa.schema(
    [
        ("day", pa.date32()),
        ("symbol", pa.string()),
        ("permaticker", pa.int64()),
        ("minute", pa.int16()),
        ("status", pa.string()),
        ("early", NBBO_SNAPSHOT),
        ("late", NBBO_SNAPSHOT),
    ]
)


def validate_nbbo_plan(settings: Settings, plan: Path) -> tuple[dict, list[dict], Path]:
    """Authenticate a complete price population before reading any raw quote values.

    The data layer reads saved identities/times and pre-open fields, never forward outcomes.
    A future price-only plan can reference the same original development control.
    """
    plan = Path(plan).expanduser().resolve()
    if plan.name in ("windows.csv", "plan.json"):
        plan = plan.parent
    base = (settings.data_dir / "quotes_sample").resolve()
    if plan.parent != base or "sealed" in plan.parts:
        raise InputError("NBBO plan must be one directory under processed quotes_sample")
    meta = json.loads((plan / "plan.json").read_text())
    if meta.get("schema") != quotes.NBBO_PLAN_VERSION or meta.get("raw_plan_name") != plan.name:
        raise InputError("unknown NBBO plan schema or conflicting raw plan name")
    return _validate_nbbo_sources(settings, meta, plan)


def _validate_nbbo_sources(settings: Settings, meta: dict, plan: Path):
    """Validate staged or published content without publishing a partial plan."""
    source_run = meta.get("source_run", "")
    if not source_run or any(x in source_run for x in ("/", "\\", "..")):
        raise InputError("invalid NBBO source run")
    source = settings.runs_dir / source_run
    manifest_path, events_path = source / "manifest.json", source / "events.parquet"
    if (
        _content_hash(manifest_path) != meta.get("source_manifest_sha256")
        or _content_hash(events_path) != meta.get("source_events_sha256")
        or _content_hash(plan / "windows.csv") != meta.get("windows_sha256")
    ):
        raise InputError("NBBO source manifest/events or window hash changed")
    manifest = json.loads(manifest_path.read_text())
    development = {"start": "2003-09-10", "end": "2016-12-30"}
    if not (
        manifest.get("run_id") == source_run
        and manifest.get("strategy") == "bid_replenishment_reversal"
        and manifest.get("kind") == "event_study"
        and manifest.get("config") == "development_control"
        and manifest.get("status") == "complete"
        and manifest.get("scratch") is False
        and manifest.get("git", {}).get("dirty") is False
        and re.fullmatch(r"[0-9a-f]{40}", manifest["git"].get("commit", ""))
        and manifest.get("resolved_config", {}).get("params") == {"use_quotes": False}
        and manifest.get("period") == development
        and meta.get("data_build_id") == manifest.get("data_build_id")
        and meta.get("source_git") == manifest.get("git")
    ):
        raise InputError("NBBO requires the clean, completed registered development control")
    source_kind = meta.get("source_kind", "event_study")
    if source_kind == "event_study":
        candidates_path = events_path
        if meta.get("period") != development:
            raise InputError("NBBO control plan period changed")
    elif source_kind == "price_plan":
        candidates_path = plan / "candidates.parquet"
        if _content_hash(candidates_path) != meta.get("candidates_sha256"):
            raise InputError("NBBO price-only candidate hash changed")
        if pq.read_schema(candidates_path).names != list(quotes.NBBO_CANDIDATE_COLUMNS):
            raise InputError("price-only plan must contain only candidate features")
    else:
        raise InputError("unknown NBBO candidate source kind")
    start, end = (date.fromisoformat(meta["period"][key]) for key in ("start", "end"))
    seal.check_range(start, end, source="NBBO candidate plan")
    # Guard dates before loading any other source columns, including for malformed sources.
    days = pq.read_table(candidates_path, columns=["day"])["day"].to_pylist()
    if not all(start <= d <= end for d in days):
        raise InputError("NBBO candidate date outside the registered source period")
    candidates = pq.read_table(
        candidates_path, columns=list(quotes.NBBO_CANDIDATE_COLUMNS)
    ).to_pylist()
    expected = quotes.replenishment_windows(candidates)
    with (plan / "windows.csv").open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(quotes.NBBO_FIELDS):
            raise InputError("NBBO window fields changed")
        windows = list(reader)
    # String comparison preserves exact nanoseconds and checks every parent field.
    normalized = [
        {k: "" if r[k] is None else str(r[k]) for k in quotes.NBBO_FIELDS} for r in expected
    ]
    if (
        windows != normalized
        or len(windows) != meta.get("events")
        or len(windows) != meta.get("windows")
    ):
        raise InputError("NBBO windows must equal every first parent candidate exactly")
    if not windows:
        raise InputError("NBBO plan has no price candidates")
    for key, value in (
        ("early_offset_ns", -5_000_000_000),
        ("late_offset_ns", -1),
        ("max_age_ns", 1_000_000_000),
        ("window_start_offset_ns", -10_000_000_000),
        ("window_end_offset_ns", 2_000_000_000),
    ):
        if meta.get(key) != value:
            raise InputError("NBBO target/window definition changed")
    return meta, expected, plan


def _nbbo_records(path: Path, window: dict) -> list[dict]:
    """Read exactly one pre-seal acquisition window; malformed provenance aborts."""
    records = []
    day = date.fromisoformat(window["day"])
    with gzip.open(path, "rt") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except (ValueError, TypeError) as error:
                raise InputError(f"malformed quote JSON in {path.name}") from error
            timestamp = row.get("sip_timestamp") if isinstance(row, dict) else None
            if type(timestamp) is not int or not 0 < timestamp <= 2**63 - 1:
                raise InputError(f"invalid SIP nanosecond timestamp in {path.name}")
            quote_day = (
                datetime.fromtimestamp(timestamp // 1_000_000_000, UTC).astimezone(NEW_YORK).date()
            )
            seal.check_range(quote_day, quote_day, source="NBBO quote timestamp")
            if quote_day != day or not window["start_ns"] <= timestamp < window["end_ns"]:
                raise InputError(f"quote date/window mismatch in {path.name}")
            if row.get("ticker", window["symbol"]) != window["symbol"]:
                raise InputError(f"quote symbol mismatch in {path.name}")
            records.append(row)
    return records


def _nbbo_coverage(rows: list[dict]) -> dict:
    def summarize(selected):
        count = len(selected)
        valid = sum(r["status"] == "available" for r in selected)
        return {
            "parents": count,
            "valid_pairs": valid,
            "valid_pair_fraction": valid / count if count else None,
            "statuses": dict(sorted(Counter(r["status"] for r in selected).items())),
        }

    return {
        "all": summarize(rows),
        "2013_2016": summarize([r for r in rows if 2013 <= r["day"].year <= 2016]),
        "2022_2023": summarize([r for r in rows if 2022 <= r["day"].year <= 2023]),
        "by_year": {
            str(y): summarize([r for r in rows if r["day"].year == y])
            for y in sorted({r["day"].year for r in rows})
        },
    }


def build_nbbo_replenishment(settings: Settings, plan: Path) -> str:
    """Build only this separate immutable input. Never acquires or modifies raw files."""
    meta, windows, plan = validate_nbbo_plan(settings, plan)
    build_id = (settings.data_dir / "builds" / CURRENT_NAME).read_text().strip()
    if meta["data_build_id"] != build_id:
        raise InputError("NBBO source data build differs from the current data build")
    raw_root = (settings.raw_dir / "massive/quotes_sample" / meta["raw_plan_name"]).resolve()
    if not raw_root.is_relative_to(settings.raw_dir.resolve()) or "sealed" in raw_root.parts:
        raise InputError("unsafe NBBO raw source path")
    files = [
        quotes.sample_file(raw_root, "quotes", date.fromisoformat(w["day"]), w["symbol"])
        for w in windows
    ]
    if any(
        "sealed" in p.resolve().parts or not p.resolve().is_relative_to(raw_root) for p in files
    ):
        raise InputError("unsafe NBBO raw quote file")
    missing = [p for p in files if not p.is_file()]
    if missing:
        raise InputError(
            f"NBBO acquisition incomplete: {len(missing)} of {len(files)} quote files missing; "
            "owner must run the download in strategies/bid_replenishment_reversal/OWNER_ACTIONS.md"
        )
    raw_hashes = {p.name: _content_hash(p) for p in files}
    identity = {
        "version": quotes.NBBO_VERSION,
        "data_build_id": build_id,
        "source_plan_sha256": _content_hash(plan / "plan.json"),
        "source_manifest_sha256": meta["source_manifest_sha256"],
        "source_events_sha256": meta["source_events_sha256"],
        "windows_sha256": meta["windows_sha256"],
        "source_git": meta["source_git"],
        "source_run": meta["source_run"],
        "source_kind": meta.get("source_kind", "event_study"),
        "candidates_sha256": meta.get("candidates_sha256"),
        "raw_files_sha256": raw_hashes,
    }
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    input_id = fingerprint[:10]
    base = root(settings, "nbbo_replenishment")
    out = base / input_id
    if not out.exists():
        rows = []
        for window, path in zip(windows, files, strict=True):
            status, early, late = quotes.replenishment_pair(
                _nbbo_records(path, window), window["decision_ns"]
            )
            rows.append(
                {
                    "day": date.fromisoformat(window["day"]),
                    "symbol": window["symbol"],
                    "permaticker": window["permaticker"],
                    "minute": window["signal_minute"],
                    "status": status,
                    "early": dataclasses.asdict(early) if early else None,
                    "late": dataclasses.asdict(late) if late else None,
                }
            )
        # A concurrently completed/replaced download cannot create mixed provenance.
        if raw_hashes != {p.name: _content_hash(p) for p in files}:
            raise InputError("NBBO raw sources changed while building; no input published")
        validate_nbbo_plan(settings, plan)
        if _content_hash(plan / "plan.json") != identity["source_plan_sha256"]:
            raise InputError("NBBO plan changed while building; no input published")
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".building-", dir=base) as temporary:
            staging = Path(temporary) / "publish"
            staging.mkdir()
            pq.write_table(
                pa.Table.from_pylist(rows, schema=NBBO_SCHEMA), staging / "pairs.parquet"
            )
            output = {
                **identity,
                "input": "nbbo_replenishment",
                "input_id": input_id,
                "fingerprint": fingerprint,
                "rows": len(rows),
                "coverage_start": meta["period"]["start"],
                "coverage_end": meta["period"]["end"],
                "coverage_basis": (
                    "all registered first price candidates, including unavailable quotes"
                ),
                "coverage": _nbbo_coverage(rows),
                "plan_directory": str(plan),
                "pairs_sha256": _content_hash(staging / "pairs.parquet"),
                "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }
            (staging / "input.json").write_text(json.dumps(output, indent=2) + "\n")
            os.replace(staging, out)
    existing = info(settings, "nbbo_replenishment", input_id)
    if existing.get("fingerprint") != fingerprint or _content_hash(
        out / "pairs.parquet"
    ) != existing.get("pairs_sha256"):
        raise InputError("immutable NBBO input was changed or is incomplete")
    with tempfile.NamedTemporaryFile(
        mode="w", dir=base, prefix=".CURRENT-", delete=False
    ) as handle:
        handle.write(input_id + "\n")
    os.replace(handle.name, base / CURRENT_NAME)
    return input_id


def write_nbbo_price_plan(
    settings: Settings, source_run: str, candidates: list[dict], period: dict, output: Path
) -> Path:
    """Publish price-only acquisition metadata; the runner supplies frozen strategy triggers.

    This is not a backtest and contains no entries, exits, returns or P&L.
    """
    output = output.expanduser().resolve()
    if output.parent != (settings.data_dir / "quotes_sample").resolve() or "sealed" in output.parts:
        raise InputError("NBBO plan must be one directory under processed quotes_sample")
    if not source_run or any(x in source_run for x in ("/", "\\", "..")):
        raise InputError("invalid NBBO source run")
    source = settings.runs_dir / source_run
    manifest = json.loads((source / "manifest.json").read_text())
    start, end = (date.fromisoformat(period[key]) for key in ("start", "end"))
    seal.check_range(start, end, source="NBBO price-only planning")
    if not all(start <= r["day"] <= end for r in candidates):
        raise InputError("price-only candidate outside the requested period")
    windows = quotes.replenishment_windows(candidates)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=quotes.NBBO_FIELDS)
    writer.writeheader()
    writer.writerows(windows)
    payload = stream.getvalue().encode()
    schema = pa.schema(
        [
            ("day", pa.date32()),
            ("symbol", pa.string()),
            ("permaticker", pa.int64()),
            ("signal_minute", pa.int64()),
            ("prev_close", pa.float64()),
            ("adv20_prev", pa.float64()),
        ]
    )
    # Serialize once so candidate content and its hash are stable and cannot include outcomes.
    table = pa.Table.from_pylist(
        sorted(candidates, key=lambda r: (r["day"], r["symbol"])), schema=schema
    )
    sink = pa.BufferOutputStream()
    pq.write_table(table, sink)
    candidate_payload = sink.getvalue().to_pybytes()
    meta = {
        "schema": quotes.NBBO_PLAN_VERSION,
        "source_kind": "price_plan",
        "source_run": source_run,
        "source_manifest_sha256": _content_hash(source / "manifest.json"),
        "source_events_sha256": _content_hash(source / "events.parquet"),
        "source_git": manifest["git"],
        "data_build_id": manifest["data_build_id"],
        "period": period,
        "events": len(windows),
        "windows": len(windows),
        "sampling": "all frozen price triggers, no availability/return filter",
        "early_offset_ns": -5_000_000_000,
        "late_offset_ns": -1,
        "max_age_ns": 1_000_000_000,
        "window_start_offset_ns": -10_000_000_000,
        "window_end_offset_ns": 2_000_000_000,
        "entry_price_field": "prior close compatibility placeholder; not a fill assumption",
        "postdecision_quotes": "never features; reserved for a future registered execution audit",
        "raw_plan_name": output.name,
        "windows_sha256": hashlib.sha256(payload).hexdigest(),
        "candidates_sha256": hashlib.sha256(candidate_payload).hexdigest(),
    }
    if output.exists():
        validate_nbbo_plan(settings, output)
        if json.loads((output / "plan.json").read_text()) != meta:
            raise InputError("refusing to overwrite a different published NBBO plan")
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".plan-", dir=output.parent) as temporary:
        staging = Path(temporary) / output.name
        staging.mkdir()
        (staging / "candidates.parquet").write_bytes(candidate_payload)
        (staging / "windows.csv").write_bytes(payload)
        (staging / "plan.json").write_text(json.dumps(meta, indent=2) + "\n")
        _validate_nbbo_sources(settings, meta, staging)
        os.replace(staging, output)
    return output
