import importlib.util
import json
import zipfile
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "owner" / "download_edgar_times.py"
spec = importlib.util.spec_from_file_location("download_edgar_times", TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def lists(*filings):
    names = ("accessionNumber", "filingDate", "acceptanceDateTime", "form", "items")
    return {name: [filing[i] for filing in filings] for i, name in enumerate(names)}


def test_only_8ks_before_the_seal_are_kept(tmp_path):
    main = {"cik": "1234", "filings": {"recent": lists(
        ("a-1", "2023-11-08", "2023-11-08T21:05:11.000Z", "8-K", "2.02,9.01"),
        ("a-2", "2023-11-09", "2023-11-09T12:00:00.000Z", "8-K", "2.02"),   # the seal: dropped
        ("a-3", "2022-05-03", "2022-05-03T20:10:00.000Z", "10-Q", ""),      # not an 8-K
        ("a-4", "2002-12-31", "2002-12-31T15:00:00.000Z", "8-K", "5"),      # before the range
    )}}  # fmt: skip
    older = lists(("b-1", "2009-02-17", "2009-02-17T11:31:02.000Z", "8-K/A", "8.01"))
    archive = tmp_path / "submissions.zip"
    with zipfile.ZipFile(archive, "w") as bulk:
        bulk.writestr("CIK0000001234.json", json.dumps(main))
        bulk.writestr("CIK0000001234-submissions-001.json", json.dumps(older))
        bulk.writestr("CIK0000005678.json", "not json")
        bulk.writestr("placeholder.txt", "ignored")
    found = list(tool.extract(archive))
    assert [(r["cik"], r["accession"], r["form"]) for r in found] == [
        (1234, "a-1", "8-K"),
        (1234, "b-1", "8-K/A"),
    ]
    assert found[0]["accepted"] == "2023-11-08T21:05:11.000Z" and found[0]["items"] == "2.02,9.01"


def test_a_document_without_the_lists_gives_nothing():
    assert list(tool.rows({"filings": {"recent": {"form": ["8-K"]}}}, 1)) == []


def test_other_forms_are_kept_on_request(tmp_path):
    document = lists(
        ("c-1", "2015-06-01", "2015-06-01T20:01:00.000Z", "SC 13D", ""),
        ("c-2", "2015-06-02", "2015-06-02T20:01:00.000Z", "8-K", "8.01"),
        ("c-3", "2015-06-03", "2015-06-03T20:01:00.000Z", "SC TO-T", ""),
    )
    forms = tool.KINDS["other"][2]
    assert [r["form"] for r in tool.rows(document, 9, forms)] == ["SC 13D", "SC TO-T"]
    assert [r["form"] for r in tool.rows(document, 9)] == ["8-K"]
