"""The owner's news download: month files, paging, no key in output, holdout refused."""

import gzip
import importlib.util
import json
from pathlib import Path

import pytest

from kinn.data import seal

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def script(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "download_news", REPO / "tools" / "owner" / "download_news.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("RAW", "DATA", "RUNS"):
        monkeypatch.setenv(f"KINN_{name}_DIR", str(tmp_path / name.lower()))
    monkeypatch.setenv("MASSIVE_API_KEY", "not-a-real-key")
    return module


def test_months_are_written_once_paged_and_trimmed(script, tmp_path, monkeypatch, capsys):
    calls = []

    def fake(url, key):
        calls.append(url)
        assert key == "not-a-real-key"
        if "benzinga" in url:
            raise script.FetchError("HTTP 403")
        if "cursor=" in url:
            return {"results": [{"id": "b", "title": "second page"}]}
        row = {"id": "a", "title": "t", "image_url": "x", "publisher": {"name": "Wire", "logo": 1}}
        return {"results": [row], "next_url": "https://api.massive.com:443/v2/x?cursor=1"}

    monkeypatch.setattr(script, "request_json", fake)
    argv = ["download_news.py", "--what", "news,benzinga", "--start", "2020-01-15",
            "--end", "2020-03-10", "--workers", "2"]  # fmt: skip
    monkeypatch.setattr("sys.argv", argv)
    script.main()
    out = tmp_path / "raw" / "massive" / "news"
    assert sorted(p.name for p in out.glob("*.gz")) == [
        "2020-01.jsonl.gz", "2020-02.jsonl.gz", "2020-03.jsonl.gz",
    ]  # fmt: skip
    with gzip.open(out / "2020-02.jsonl.gz", "rt") as handle:
        rows = [json.loads(line) for line in handle]
    assert rows == [{"id": "a", "title": "t", "publisher": "Wire"},
                    {"id": "b", "title": "second page"}]  # fmt: skip
    first = next(u for u in calls if "2020-01-15" in u)
    assert "published_utc.gte=2020-01-15" in first and "published_utc.lt=2020-02-01" in first
    assert any("published_utc.lt=2020-03-11" in u for u in calls)
    printed = capsys.readouterr().out
    assert "not-a-real-key" not in printed and "benzinga: not included" in printed
    before = len(calls)
    monkeypatch.setattr("sys.argv", [*argv[:2], "news", *argv[3:]])
    script.main()  # a second pass fetches nothing
    assert len(calls) == before


def test_holdout_dates_and_other_hosts_are_refused(script, monkeypatch):
    monkeypatch.setattr("sys.argv", ["download_news.py", "--end", "2023-11-09"])
    with pytest.raises(seal.HoldoutError):
        script.main()
    for url in ("https://evil.example/v2/reference/news", "http://api.massive.com/v2/x",
                "https://api.massive.com:8443/v2/x"):  # fmt: skip
        with pytest.raises(SystemExit):
            script.request_json(url, "not-a-real-key")
