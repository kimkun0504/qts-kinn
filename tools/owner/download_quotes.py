"""OWNER-ONLY: download NBBO quotes and trades for a planned sample of events.

Run it yourself on the Mac. It needs the Massive key and writes to the raw data folder, both of
which agents must not touch (AGENTS.md).

    uv run python tools/owner/download_quotes.py <path to windows.csv>

The key is read from the environment variable MASSIVE_API_KEY, or from a `.env` file in the
repo root. It is sent only as an Authorization header to api.massive.com and never printed.
Files land in $KINN_RAW_DIR/massive/quotes_sample/<plan>/{quotes,trades}/. Finished files are
skipped, so the script can be re-run. Holdout dates are refused.
"""

from __future__ import annotations

import gzip
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from kinn.core.settings import load_settings
from kinn.data import quotes, seal

HOST = "https://api.massive.com"
REPO = Path(__file__).resolve().parents[2]


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
                raise SystemExit(f"Massive answered HTTP {error.code} for a request") from None
            except (urllib.error.URLError, TimeoutError):
                if attempt == 5:
                    raise SystemExit("could not reach api.massive.com") from None
                time.sleep(2**attempt)
        results.extend(payload.get("results") or [])
        url = payload.get("next_url") or ""
    return results


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    windows_path = Path(sys.argv[1]).expanduser().resolve()
    windows = quotes.read_windows(windows_path)
    out = load_settings().raw_dir / "massive" / "quotes_sample" / windows_path.parent.name
    key = api_key()
    done = skipped = 0
    for index, w in enumerate(windows, 1):
        seal.check_range(w["day"], w["day"], source="quote download")
        for kind in ("quotes", "trades"):
            path = quotes.sample_file(out, kind, w["day"], w["symbol"])
            if path.exists():
                skipped += 1
                continue
            query = urllib.parse.urlencode({
                "timestamp.gte": w["start_ns"], "timestamp.lt": w["end_ns"],
                "order": "asc", "sort": "timestamp", "limit": 50000,
            })  # fmt: skip
            symbol = urllib.parse.quote(w["symbol"], safe="")
            rows = fetch_all(f"{HOST}/v3/{kind}/{symbol}?{query}", key)
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            with gzip.open(tmp, "wt") as handle:
                for row in rows:
                    handle.write(json.dumps(row) + "\n")
            os.replace(tmp, path)
            done += 1
        if index % 25 == 0 or index == len(windows):
            print(f"{index}/{len(windows)} events ({done} files written, {skipped} already there)")
    print(f"finished: {out}")


if __name__ == "__main__":
    main()
