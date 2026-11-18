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

import gzip
import hashlib
import json
import os
import re
import tempfile
import zipfile
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
import pyarrow as pa
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

from kinn.core.settings import HOLDOUT_START, Settings
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
NAMES = ("form4", "form8k", "form8k_timed")
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
