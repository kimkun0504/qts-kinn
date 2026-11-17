import importlib.util
from datetime import date
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "owner" / "paper_earnings_drift.py"
spec = importlib.util.spec_from_file_location("paper_earnings_drift", TOOL)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def test_quality_facts_never_stop_the_ledger(monkeypatch, capsys):
    def unreachable(*args):
        raise tool.FetchError("HTTP 503 from data.sec.gov")

    def odd_figures(*args):
        raise TypeError("unsupported operand")

    monkeypatch.setattr(tool, "_quality_facts", unreachable)
    assert tool.quality_facts("AAA", date(2026, 11, 17), 1, "key", "me@x") == {}
    monkeypatch.setattr(tool, "_quality_facts", odd_figures)
    assert tool.quality_facts("AAA", date(2026, 11, 17), 1, "key", "me@x") == {}
    said = capsys.readouterr().out
    assert "could not be fetched" in said and "could not be read (TypeError" in said


def test_a_snapshot_that_cannot_be_built_is_left_out(monkeypatch, capsys):
    class Rule:
        hold = 15

    def broken(*args, **kwargs):
        raise KeyError("kept")

    monkeypatch.setattr(tool.swing_paper, "snapshot", broken)
    assert tool.snapshot_of({}, {}, Rule(), {}) is None
    assert "the ledger itself is saved" in capsys.readouterr().out
    monkeypatch.setattr(tool.swing_paper, "snapshot", lambda *a, **k: {"schema": "x"})
    assert tool.snapshot_of({}, {}, Rule(), {}) == {"schema": "x"}
