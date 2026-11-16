"""OWNER-ONLY: download Massive's news archive and short-sale data for research.

Run it yourself on the Mac. It needs the Massive key and writes to the raw data folder, both of
which agents must not touch (AGENTS.md).

    uv run python tools/owner/download_news.py                 # everything, to the seal
    uv run python tools/owner/download_news.py --what news --start 2022-01-01

What it fetches, one file per month under $KINN_RAW_DIR/massive/<name>/:

    news            /v2/reference/news        timed articles with tickers (from 2016-06-22)
    benzinga        /benzinga/v2/news         Benzinga headlines with channels and tags
    short_interest  /stocks/v1/short-interest FINRA short interest, twice a month
    short_volume    /stocks/v1/short-volume   daily off-exchange short volume

The key is read from MASSIVE_API_KEY, or from a `.env` file in the repo root. It is sent only
as an Authorization header to api.massive.com and never printed. Finished months are skipped,
so the script can be re-run until nothing is left. Holdout dates are refused. A dataset the
plan does not include is reported and skipped.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

from kinn.core.settings import HOLDOUT_START, load_settings
from kinn.data import seal

HOST = "api.massive.com"
REPO = Path(__file__).resolve().parents[2]
# name -> (path, date field, sort value, page sizes to try, fields dropped to save space)
DATASETS = {
    "news": ("/v2/reference/news", "published_utc", "published_utc", (1000,),
             ("image_url", "amp_url")),
    "benzinga": ("/benzinga/v2/news", "published", "published.asc", (1000, 100),
                 ("body", "images")),
    "short_interest": ("/stocks/v1/short-interest", "settlement_date", "settlement_date.asc",
                       (50000, 5000, 1000), ()),
    "short_volume": ("/stocks/v1/short-volume", "date", "date.asc", (50000, 5000, 1000), ()),
}  # fmt: skip
FIRST = {"news": date(2016, 6, 22), "benzinga": date(2009, 4, 27)}


class FetchError(Exception):
    """The vendor refused a request (the message never contains the key or the URL)."""


def api_key() -> str:
    key = os.environ.get("MASSIVE_API_KEY", "")
    env_file = REPO / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "MASSIVE_API_KEY":
                key = value.strip().strip("'\"")
    if not key:
        raise SystemExit("MASSIVE_API_KEY is not set and was not found in .env")
    return key


def request_json(url: str, key: str) -> dict:
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname != HOST or parts.port not in (None, 443):
        raise SystemExit("refusing to send the key to an unexpected host")
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(2**attempt)
                continue
            raise FetchError(f"HTTP {error.code}") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == 5:
                raise FetchError("could not reach api.massive.com") from None
            time.sleep(2**attempt)
    raise FetchError("no response")


def months(start: date, end: date) -> list[tuple[date, date]]:
    """[first day, day after the last day) for each month touching start..end."""
    out, cursor = [], start
    while cursor <= end:
        following = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)
        out.append((cursor, min(following, end + timedelta(days=1))))
        cursor = following
    return out


def fetch_month(out: Path, name: str, first: date, until: date, key: str) -> tuple[str, int]:
    """One month of one dataset. Returns ("written" | "skipped", rows)."""
    path = out / f"{first.isoformat()[:7]}.jsonl.gz"
    if path.exists():
        return "skipped", 0
    route, field, sort, sizes, dropped = DATASETS[name]
    rows: list[dict] = []
    for size in sizes:
        query = {f"{field}.gte": first.isoformat(), f"{field}.lt": until.isoformat(),
                 "sort": sort, "limit": size}  # fmt: skip
        if name == "news":
            query["order"] = "asc"
        url = f"https://{HOST}{route}?{urllib.parse.urlencode(query)}"
        try:
            while url:
                payload = request_json(url, key)
                rows.extend(payload.get("results") or [])
                url = payload.get("next_url") or ""
            break
        except FetchError as error:
            if str(error) != "HTTP 400" or size == sizes[-1]:
                raise
            rows = []  # the page size was refused: try a smaller one
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as handle:
        for row in rows:
            for unwanted in dropped:
                row.pop(unwanted, None)
            if isinstance(row.get("publisher"), dict):
                row["publisher"] = row["publisher"].get("name")
            handle.write(json.dumps(row) + "\n")
    os.replace(tmp, path)
    return "written", len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--what", default=",".join(DATASETS), help="comma-separated datasets")
    parser.add_argument("--start", default="2016-06-22")
    parser.add_argument("--end", default=(HOLDOUT_START - timedelta(days=1)).isoformat())
    parser.add_argument("--workers", type=int, default=6, help="months fetched in parallel")
    args = parser.parse_args()
    start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    seal.check_range(start, end, source="news download")
    key = api_key()
    base = load_settings().raw_dir / "massive"
    for name in args.what.split(","):
        if name not in DATASETS:
            raise SystemExit(f"unknown dataset {name!r}; choose from {', '.join(DATASETS)}")
        out = base / name
        out.mkdir(parents=True, exist_ok=True)
        spans = months(max(start, FIRST.get(name, start)), end)
        counts = {"written": 0, "skipped": 0}
        rows, failed, refused, started = 0, [], False, time.time()
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            futures = {pool.submit(fetch_month, out, name, a, b, key): a for a, b in spans}
            for future in as_completed(futures):
                try:
                    state, n = future.result()
                    counts[state] += 1
                    rows += n
                except FetchError as error:
                    failed.append(f"{futures[future].isoformat()[:7]}: {error}")
                    if str(error) in ("HTTP 401", "HTTP 403"):
                        refused = True
        if refused and not counts["written"]:
            print(f"{name}: not included in this plan or key refused (HTTP 401/403); skipped")
            continue
        (out / "failed.txt").write_text("\n".join(sorted(failed)) + ("\n" if failed else ""))
        print(f"{name}: {counts['written']} months written ({rows:,} rows), "
              f"{counts['skipped']} already there, {len(failed)} failed, "
              f"{time.time() - started:.0f} s -> {out}")  # fmt: skip
        if failed:
            print(f"  run the same command again; refused months are in {out / 'failed.txt'}")


if __name__ == "__main__":
    main()
