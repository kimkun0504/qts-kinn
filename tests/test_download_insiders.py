"""The owner's insider-data download stops before the holdout seal and calls only the SEC."""

import importlib.util
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "owner" / "download_insiders.py"
spec = importlib.util.spec_from_file_location("download_insiders", TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def test_quarters_run_from_2006_to_the_last_one_before_the_seal():
    names = tool.quarters()
    assert names[0] == "2006q1_form345.zip" and names[-1] == "2023q3_form345.zip"
    assert len(names) == 71 and "2023q4_form345.zip" not in names


@pytest.mark.parametrize(
    "url", ["http://www.sec.gov/x", "https://sec.gov.example.com/x", "https://www.sec.gov:8443/x"]
)
def test_only_the_sec_over_https_is_called(url):
    with pytest.raises(SystemExit):
        tool.fetch(url, "Test test@example.com")
