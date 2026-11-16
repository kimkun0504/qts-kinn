"""OWNER-ONLY: download NBBO quotes and trades for a planned sample of events or orders.

Run it yourself on the Mac. It needs the Massive key and writes to the raw data folder, both of
which agents must not touch (AGENTS.md).

    uv run python tools/owner/download_quotes.py <path to windows.csv> [--workers 8]

The key is read from the environment variable MASSIVE_API_KEY, or from a `.env` file in the
repo root. It is sent only as an Authorization header to api.massive.com and never printed.
Files land in $KINN_RAW_DIR/massive/quotes_sample/<plan>/{quotes,trades}/, with the vendor's
table of trade conditions beside them (conditions.json). Finished files are skipped, so the
script can be re-run until nothing is left. Holdout dates are refused. A window the vendor
refuses is listed in failed.txt and the rest continue.
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
from pathlib import Path

from kinn.core.settings import load_settings
from kinn.data import quotes, seal

HOST = "https://api.massive.com"
REPO = Path(__file__).resolve().parents[2]


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


def fetch_all(url: str, key: str) -> list[dict]:
    results: list[dict] = []
    while url:
        if not url.startswith(HOST + "/"):
            raise SystemExit("refusing to send the key to an unexpected host")
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    payload = json.load(response)
                break
            except urllib.error.HTTPError as error:
                if error.code in (429, 500, 502, 503, 504) and attempt < 5:
                    time.sleep(2**attempt)
                    continue
                raise FetchError(f"HTTP {error.code}") from None
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt == 5:
                    raise FetchError("could not reach api.massive.com") from None
                time.sleep(2**attempt)
        results.extend(payload.get("results") or [])
        url = payload.get("next_url") or ""
    return results


def fetch_window(out: Path, kind: str, window: dict, key: str) -> str:
    """Fetch one file. Returns "written" or "skipped"."""
    path = quotes.sample_file(out, kind, window["day"], window["symbol"])
    if path.exists():
        return "skipped"
    query = urllib.parse.urlencode({
        "timestamp.gte": window["start_ns"], "timestamp.lt": window["end_ns"],
        "order": "asc", "sort": "timestamp", "limit": 50000,
    })  # fmt: skip
    symbol = urllib.parse.quote(window["symbol"], safe="")
    rows = fetch_all(f"{HOST}/v3/{kind}/{symbol}?{query}", key)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")
    os.replace(tmp, path)
    return "written"


def fetch_conditions(out: Path, key: str) -> None:
    """The vendor's table of trade conditions (which ones update the high and low)."""
    path = out / "conditions.json"
    if path.exists():
        return
    try:
        rows = fetch_all(f"{HOST}/v3/reference/conditions?asset_class=stocks&limit=1000", key)
    except FetchError as error:
        print(f"conditions table not downloaded ({error}); the check will use its built-in list")
        return
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows))
    os.replace(tmp, path)
    print(f"conditions table: {len(rows)} rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("windows", help="path to a windows.csv written by kinn")
    parser.add_argument("--workers", type=int, default=8, help="parallel requests")
    args = parser.parse_args()
    windows_path = Path(args.windows).expanduser().resolve()
    windows = quotes.read_windows(windows_path)
    for w in windows:
        seal.check_range(w["day"], w["day"], source="quote download")
    out = load_settings().raw_dir / "massive" / "quotes_sample" / windows_path.parent.name
    for kind in ("quotes", "trades"):
        (out / kind).mkdir(parents=True, exist_ok=True)
    key = api_key()
    fetch_conditions(out, key)
    jobs = [(kind, w) for w in windows for kind in ("quotes", "trades")]
    counts = {"written": 0, "skipped": 0}
    failed: list[str] = []
    started = time.time()
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(fetch_window, out, kind, w, key): (kind, w) for kind, w in jobs}
        for done, future in enumerate(as_completed(futures), 1):
            kind, w = futures[future]
            try:
                counts[future.result()] += 1
            except FetchError as error:
                failed.append(f"{w['day']} {w['symbol']} {kind}: {error}")
                if str(error) in ("HTTP 401", "HTTP 403"):
                    pool.shutdown(cancel_futures=True)
                    raise SystemExit(f"Massive refused the key ({error}); stopped") from None
            if done % 500 == 0 or done == len(jobs):
                print(
                    f"{done}/{len(jobs)} files ({counts['written']} written, "
                    f"{counts['skipped']} already there, {len(failed)} failed, "
                    f"{time.time() - started:.0f} s)"
                )
    (out / "failed.txt").write_text("\n".join(sorted(failed)) + ("\n" if failed else ""))
    print(f"finished: {out}")
    if failed:
        print(f"{len(failed)} files failed (see failed.txt); run the command again to retry them")


if __name__ == "__main__":
    main()
