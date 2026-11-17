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

import hashlib
import json
import os
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from kinn.core.settings import HOLDOUT_START, Settings

FORM4_VERSION = "form4-1"
FORM8K_VERSION = "form8k-1"
# The items of Form 8-K, as Sharadar's event codes (item X.0Y is code XY). Other codes in the
# EVENTS table are Sharadar's own and are passed through without an item number.
FORM8K_ITEMS = frozenset(
    (11, 12, 13, 14, 15, 21, 22, 23, 24, 25, 26, 31, 32, 33, 41, 42, 51, 52, 53, 54, 55, 56,
     57, 58, 61, 62, 63, 64, 65, 71, 81, 91)
)  # fmt: skip
EARNINGS_CODE = 22  # item 2.02, results of operations and financial condition
NAMES = ("form4", "form8k")
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
