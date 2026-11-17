"""OWNER-ONLY: download the SEC's quarterly index of every EDGAR filing (form type, company,
CIK, date, file name).

Run it yourself on the Mac. It writes to the raw data folder, which agents must not touch
(AGENTS.md). The files are free and need no key; the SEC asks who is calling:

    export SEC_USER_AGENT="Your Name your@email"
    uv run python tools/owner/download_edgar_index.py

One file a quarter from 2005 Q1 lands in $KINN_RAW_DIR/sec/index/. It stops at 2023 Q3: the
next quarter holds filings from after the holdout seal (2023-11-09). Finished files are
skipped, so the script can be run again until nothing is left.
"""

from __future__ import annotations

import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from kinn.core.settings import load_settings

HOST = "www.sec.gov"
ROUTE = "/Archives/edgar/full-index/{year}/QTR{quarter}/form.gz"
FIRST, LAST = (2005, 1), (2023, 3)  # 2023 Q4 reaches past the seal


def quarters(first: tuple[int, int] = FIRST, last: tuple[int, int] = LAST) -> list[tuple[int, int]]:
    out, (year, quarter) = [], first
    while (year, quarter) <= last:
        out.append((year, quarter))
        year, quarter = (year, quarter + 1) if quarter < 4 else (year + 1, 1)
    return out


def fetch(url: str, agent: str) -> bytes:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname != HOST or parts.port not in (None, 443):
        raise SystemExit("refusing to call an unexpected host")
    request = urllib.request.Request(url, headers={"User-Agent": agent})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < 4:
                time.sleep(2**attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 4:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("no response")


def main() -> None:
    agent = os.environ.get("SEC_USER_AGENT", "").strip()
    if "@" not in agent:
        raise SystemExit('set SEC_USER_AGENT="Your Name your@email" (the SEC requires it)')
    out = load_settings().raw_dir / "sec" / "index"
    try:
        out.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise SystemExit(
            f"cannot create {out}: its parent is read-only. Create it yourself, e.g.\n"
            f"  chmod u+w {out.parent} && mkdir -p {out} && chmod u-w {out.parent}"
        ) from None
    written = skipped = 0
    failed: list[str] = []
    for year, quarter in quarters():
        path = out / f"{year}q{quarter}_form.gz"
        if path.exists():
            skipped += 1
            continue
        try:
            data = fetch(f"https://{HOST}{ROUTE.format(year=year, quarter=quarter)}", agent)
        except (urllib.error.URLError, TimeoutError, ConnectionError, RuntimeError):
            data = b""
        if data[:2] != b"\x1f\x8b":  # not a gzip file
            failed.append(path.name)
            continue
        tmp = Path(str(path) + ".tmp")
        tmp.write_bytes(data)
        os.replace(tmp, path)
        written += 1
        print(f"{path.name}: {len(data) / 1e6:.1f} MB", flush=True)
        time.sleep(0.3)  # well under the SEC's ten requests a second
    print(f"finished: {written} written, {skipped} already there, {len(failed)} failed -> {out}")
    if failed:
        print("failed: " + ", ".join(failed) + " (run again; if it persists, paste this line)")


if __name__ == "__main__":
    main()
