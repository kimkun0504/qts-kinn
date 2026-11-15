"""The holdout seal, code layer (ARCHITECTURE.md rule 7, decision 0002).

Every read of dated data goes through :func:`check_range`. Dates on or after ``HOLDOUT_START``
raise unless the caller passes ``unseal=True`` *and* ``KINN_UNSEAL_TOKEN`` is set in the
environment. Only the owner sets that variable. Every unseal is appended to a log.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from kinn.core.settings import HOLDOUT_START

LAST_OPEN_DATE = HOLDOUT_START - timedelta(days=1)
TOKEN_VARIABLE = "KINN_UNSEAL_TOKEN"
UNSEAL_LOG_NAME = "unseal_log.jsonl"


class HoldoutError(RuntimeError):
    """Raised when code asks for a holdout date without a valid unseal."""


def is_holdout(day: date) -> bool:
    return day >= HOLDOUT_START


def check_range(
    start: date,
    end: date,
    *,
    source: str,
    unseal: bool = False,
    log_dir: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> None:
    """Allow ``[start, end]`` (inclusive) or raise :class:`HoldoutError`."""
    if end < start:
        raise ValueError(f"end {end} is before start {start}")
    if not is_holdout(end):
        return
    env = os.environ if env is None else env
    token = env.get(TOKEN_VARIABLE, "")
    if not unseal or not token:
        raise HoldoutError(
            f"{source}: {start}..{end} reaches the holdout (from {HOLDOUT_START}). "
            f"Only the owner can unseal, with --unseal and {TOKEN_VARIABLE}."
        )
    if log_dir is None:
        raise HoldoutError(f"{source}: an unseal must be logged, but no log folder was given.")
    log_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source": source,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "token_fingerprint": hashlib.sha256(token.encode()).hexdigest()[:8],
    }
    with (log_dir / UNSEAL_LOG_NAME).open("a") as handle:
        handle.write(json.dumps(record) + "\n")
