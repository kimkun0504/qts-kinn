"""Shared reading of the SEC filing times the owner downloaded
(tools/owner/download_edgar_times.py): which stock a filer is, and which session a filing
belongs to."""

from __future__ import annotations

import bisect
import csv
import gzip
import io
import json
import re
import zipfile
from collections import defaultdict
from collections.abc import Iterator
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from kinn.core.settings import load_settings
from kinn.data.store import DataStore

NEW_YORK = ZoneInfo("America/New_York")
CLOSE = 960  # 16:00 as a minute of the day


def numbers() -> dict[int, set[int]]:
    """{SEC number: the stocks (permatickers) of that company}, from Sharadar's ticker table."""
    raw = max((load_settings().raw_dir / "sharadar").iterdir())
    found = defaultdict(set)
    with zipfile.ZipFile(next(raw.glob("SHARADAR_TICKERS_*.zip"))) as z, z.open(z.namelist()[0]) as handle:
        for row in csv.DictReader(io.TextIOWrapper(handle, "utf-8")):
            match = re.search(r"CIK=0*(\d+)", row.get("secfilings") or "")
            if match and row["table"] == "SEP":
                found[int(match.group(1))].add(int(row["permaticker"]))
    return found


def filings(name: str) -> Iterator[dict]:
    """The rows of one downloaded file (``8k.jsonl.gz`` or ``other_forms.jsonl.gz``)."""
    with gzip.open(load_settings().raw_dir / "sec" / "filing_times" / name, "rt") as handle:
        for line in handle:
            yield json.loads(line)


def sessions() -> list[date]:
    return DataStore(load_settings()).sessions(date(2003, 6, 2), date(2023, 11, 8))


def accepted(row: dict) -> tuple[date, int] | None:
    """The New York day and minute at which the SEC accepted a filing."""
    if not row.get("accepted"):
        return None
    when = datetime.strptime(row["accepted"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    local = when.astimezone(NEW_YORK)
    return local.date(), local.hour * 60 + local.minute


def reaction_session(days: list[date], when: tuple[date, int]) -> date | None:
    """The first session whose close comes after the filing was accepted."""
    day, minute = when
    at = bisect.bisect_left(days, day)
    if at < len(days) and days[at] == day and minute < CLOSE:
        return day
    at = bisect.bisect_right(days, day)
    return days[at] if at < len(days) and (days[at] - day).days <= 5 else None


def session_after(days: list[date], filed: date) -> date | None:
    """The first session after a filing's date (how A50 reads an 8-K's date)."""
    at = bisect.bisect_right(days, filed)
    return days[at] if at < len(days) and (days[at] - filed).days <= 5 else None
