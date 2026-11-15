"""Find vendor files under ``KINN_RAW_DIR``. Read-only. Holdout-dated files are never returned."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from kinn.data.seal import is_holdout

MASSIVE_FOLDERS = {"day": "day_aggs_v1", "minute": "minute_aggs_v1"}


@dataclass(frozen=True)
class RawFile:
    day: date
    path: Path
    size: int


def massive_files(raw_dir: Path, kind: str) -> list[RawFile]:
    """Massive flat files of ``kind`` ('day' or 'minute') dated before the holdout, oldest first."""
    base = raw_dir / "massive" / "us_stocks_sip" / MASSIVE_FOLDERS[kind]
    files = []
    for path in sorted(base.glob("*/*/*.csv.gz")):
        day = date.fromisoformat(path.name[:10])
        if is_holdout(day):
            continue  # belongs in sealed/; never opened
        files.append(RawFile(day, path, path.stat().st_size))
    return files


def sharadar_snapshot(raw_dir: Path) -> Path:
    """The newest Sharadar snapshot folder (named by snapshot date)."""
    snapshots = sorted(p for p in (raw_dir / "sharadar").iterdir() if p.is_dir())
    if not snapshots:
        raise FileNotFoundError(f"no Sharadar snapshot under {raw_dir / 'sharadar'}")
    return snapshots[-1]


def sharadar_zip(snapshot: Path, table: str) -> Path:
    matches = sorted(snapshot.glob(f"SHARADAR_{table}_*.zip"))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected one {table} zip in {snapshot}, found {len(matches)}")
    return matches[0]


def fingerprint(entries: list[tuple[str, int]], *extra: str) -> str:
    """A short hash of file names and sizes plus any version strings."""
    digest = hashlib.sha256()
    for name, size in sorted(entries):
        digest.update(f"{name}:{size}\n".encode())
    for item in extra:
        digest.update(f"{item}\n".encode())
    return digest.hexdigest()[:10]
