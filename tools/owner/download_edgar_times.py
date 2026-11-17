"""OWNER-ONLY: download the time of day at which the SEC accepted every 8-K.

Run it yourself on the Mac. It writes to the raw data folder, which agents must not touch
(AGENTS.md). The file is free and needs no key; the SEC asks who is calling:

    export SEC_USER_AGENT="Your Name your@email"
    uv run python tools/owner/download_edgar_times.py

Why: the 8-K data on disk gives the day of a filing, not the minute. With the minute, what a
stock does in the first hours after any kind of company news can be tested on 2005 to 2023.

What it does: fetches the SEC's nightly bulk file of every filer's filing list
(`submissions.zip`, about 1.5 GB) to a temporary folder, keeps the 8-K rows filed before the
holdout seal (2023-11-09), writes them to $KINN_RAW_DIR/sec/filing_times/8k.jsonl.gz with a
small manifest, and deletes the bulk file. Rows from the seal onward are never written.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Iterator
from datetime import UTC, date, datetime
from pathlib import Path

from kinn.core.settings import HOLDOUT_START, load_settings

HOST = "www.sec.gov"
ROUTE = "/Archives/edgar/daily-index/bulkdata/submissions.zip"
FIRST = date(2003, 1, 1)
FORMS = {"8-K", "8-K/A"}
FILER = re.compile(r"CIK(\d{10})")
FIELDS = ("accessionNumber", "filingDate", "acceptanceDateTime", "form", "items")


def rows(document: dict, cik: int) -> Iterator[dict]:
    """The 8-K rows of one filer's document that were filed before the seal. The main
    document holds its lists under filings.recent; the overflow documents hold them at the
    top."""
    lists = (document.get("filings") or {}).get("recent") or document
    if not all(isinstance(lists.get(name), list) for name in FIELDS):
        return
    for accession, filed, accepted, form, items in zip(*(lists[n] for n in FIELDS), strict=False):
        if form not in FORMS:
            continue
        try:
            day = date.fromisoformat(filed)
        except (TypeError, ValueError):
            continue
        if FIRST <= day < HOLDOUT_START:
            yield {"cik": cik, "accession": accession, "form": form, "filed": filed,
                   "accepted": accepted, "items": items or ""}  # fmt: skip


def extract(archive: Path) -> Iterator[dict]:
    """Every pre-seal 8-K row in the bulk file."""
    with zipfile.ZipFile(archive) as bulk:
        for name in bulk.namelist():
            match = FILER.search(name)
            if not match or not name.endswith(".json"):
                continue
            try:
                document = json.loads(bulk.read(name))
            except (ValueError, KeyError):
                continue
            yield from rows(document, int(match.group(1)))


def download(url: str, agent: str, target: Path) -> None:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname != HOST or parts.port not in (None, 443):
        raise SystemExit("refusing to call an unexpected host")
    request = urllib.request.Request(url, headers={"User-Agent": agent})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as out:
                done, shown = 0, 0
                while chunk := response.read(1 << 20):
                    out.write(chunk)
                    done += len(chunk)
                    if done - shown >= 100 << 20:
                        shown = done
                        print(f"  {done / 1e6:,.0f} MB", flush=True)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            if attempt == 3:
                raise SystemExit(f"the download failed: {error}") from None
            time.sleep(5 * (attempt + 1))


def main() -> None:
    agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if "@" not in agent:
        raise SystemExit('set SEC_USER_AGENT="Your Name your@email" (the SEC requires it)')
    out = load_settings().raw_dir / "sec" / "filing_times"
    try:
        out.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise SystemExit(
            f"cannot create {out}: its parent is read-only. Create it yourself, e.g.\n"
            f"  chmod u+w {out.parent} && mkdir -p {out} && chmod u-w {out.parent}"
        ) from None
    path = out / "8k.jsonl.gz"
    if path.exists():
        raise SystemExit(f"{path} is already there; delete it first to download again")
    with tempfile.TemporaryDirectory() as scratch:
        archive = Path(scratch) / "submissions.zip"
        print("downloading the SEC's bulk file (about 1.5 GB)", flush=True)
        download(f"https://{HOST}{ROUTE}", agent, archive)
        print("reading it", flush=True)
        count, first, last = 0, None, None
        tmp = Path(str(path) + ".tmp")
        with gzip.open(tmp, "wt", encoding="utf-8") as handle:
            for row in extract(archive):
                handle.write(json.dumps(row, separators=(",", ":")) + "\n")
                count += 1
                first = row["filed"] if first is None or row["filed"] < first else first
                last = row["filed"] if last is None or row["filed"] > last else last
    if not count:
        tmp.unlink(missing_ok=True)
        raise SystemExit("no 8-K rows were found; the bulk file's layout may have changed")
    os.replace(tmp, path)
    manifest = {"source": f"https://{HOST}{ROUTE}", "downloaded": datetime.now(UTC).isoformat(),
                "rows": count, "first_filed": first, "last_filed": last,
                "kept": f"8-K and 8-K/A filed before {HOLDOUT_START.isoformat()}"}  # fmt: skip
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{count:,} filings from {first} to {last} written to {path}")


if __name__ == "__main__":
    main()
