"""The form4 input: what is preserved, when a filing becomes visible, and that a run is pinned
to the version it started with."""

from __future__ import annotations

import json
import os
import zipfile
from dataclasses import replace
from datetime import date

import pyarrow.parquet as pq
import pytest

from kinn import run as runner
from kinn.data import inputs
from kinn.data.store import DataStore
from kinn.data.universe import Universe
from kinn.engine.intraday.data import load_day

SUBMISSION = ["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE", "ISSUERCIK", "ISSUERNAME",
              "ISSUERTRADINGSYMBOL"]  # fmt: skip
OWNER = ["ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNERNAME", "RPTOWNER_RELATIONSHIP",
         "RPTOWNER_TITLE"]  # fmt: skip
TRANS = ["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_CODE", "TRANS_SHARES", "TRANS_PRICEPERSHARE",
         "TRANS_ACQUIRED_DISP_CD"]  # fmt: skip
UNIVERSE = Universe("everything", min_sessions_prior=1)


def _zip(raw, name: str, filings: list[tuple]) -> None:
    """``filings``: (accession, filed, type, symbol, [(code, shares, price, acquired), ...])."""
    folder = raw / "sec" / "insiders"
    folder.mkdir(parents=True, exist_ok=True)

    def tsv(head, rows):
        return "\n".join("\t".join(str(v) for v in row) for row in [head, *rows]) + "\n"

    with zipfile.ZipFile(folder / f"{name}_form345.zip", "w") as z:
        z.writestr("SUBMISSION.tsv", tsv(SUBMISSION, [
            (a, filed, kind, "0000012345", f"{symbol} Corp", symbol.lower())
            for a, filed, kind, symbol, _ in filings]))  # fmt: skip
        z.writestr(
            "REPORTINGOWNER.tsv",
            tsv(
                OWNER,
                [(a, "0000099999", "Doe Jane", "Director,Officer", "CFO") for a, *_ in filings],
            ),
        )
        z.writestr("NONDERIV_TRANS.tsv", tsv(TRANS, [
            (a, filed, code, shares, price, acquired)
            for a, filed, _, _, lines in filings
            for code, shares, price, acquired in lines]))  # fmt: skip


@pytest.fixture
def world(built, tmp_path):
    """The synthetic build with its own raw folder for insider files, and two of its symbols."""
    data = tmp_path / "processed"
    data.mkdir()
    for name in ("builds", "bars"):
        os.symlink(built.data_dir / name, data / name)
    settings = replace(built, raw_dir=tmp_path / "raw", data_dir=data, runs_dir=tmp_path / "runs")
    store = DataStore(built)
    symbols = store.panel(date(2023, 10, 3), date(2023, 10, 3), universe=UNIVERSE,
                          columns="symbol")["symbol"].to_pylist()  # fmt: skip
    one, two = symbols[0], symbols[1]
    _zip(settings.raw_dir, "2023q4", [
        ("A1", "02-OCT-2023", "4", one,
         [("P", 1000, 5, "A"), ("P", 500, 6, "A"), ("S", 200, 6, "D")]),
        ("A2", "07-OCT-2023", "4", two, [("P", 100, 10, "A")]),  # a Saturday
        ("A3", "09-NOV-2023", "4", one, [("P", 999, 9, "A")]),  # after the seal
        ("A4", "03-OCT-2023", "4/A", one, [("A", 50, 0, "A")]),
        ("A5", "03-OCT-2023", "3", one, [("P", 1, 1, "A")]),  # not a Form 4
    ])  # fmt: skip
    return settings, one, two


def _rows(table):
    return {(r["accession"], r["transaction_code"]): r for r in table.to_pylist()}


def test_the_build_keeps_issuer_accession_code_and_purchase_amount(world):
    settings, one, _ = world
    input_id = inputs.build_form4(settings)
    meta = inputs.info(settings, "form4")
    assert meta["input_id"] == input_id == inputs.current(settings, "form4")
    assert meta["version"] == inputs.FORM4_VERSION and meta["last_filed"] == "2023-10-07"
    path = inputs.root(settings, "form4") / input_id / "transactions.parquet"
    rows = _rows(pq.read_table(path))
    assert set(rows) == {("A1", "P"), ("A1", "S"), ("A2", "P"), ("A4", "A")}  # no A3, no A5
    bought = rows[("A1", "P")]
    assert bought["issuer_cik"] == "0000012345" and bought["issuer_name"] == f"{one} Corp"
    assert bought["symbol"] == one and bought["filed"] == date(2023, 10, 2)
    assert bought["shares"] == 1500 and bought["amount"] == bought["purchase_amount"] == 8000
    assert bought["officer"] and bought["director"] and not bought["ten_percent_owner"]
    assert rows[("A1", "S")]["amount"] == 1200 and rows[("A1", "S")]["purchase_amount"] is None
    assert rows[("A4", "A")]["document_type"] == "4/A" and rows[("A4", "A")]["amount"] is None
    assert inputs.build_form4(settings) == input_id  # the same raw files give the same id
    _zip(settings.raw_dir, "2024q1", [("B1", "05-OCT-2023", "4", one, [("P", 1, 1, "A")])])
    assert inputs.build_form4(settings) != input_id  # new raw files give a new one


def test_a_filing_is_visible_from_the_session_after_its_filing_date(world):
    settings, _, _ = world
    inputs.build_form4(settings)
    store = DataStore(settings)

    def seen(day, sessions=1):
        table = store.form4(date.fromisoformat(day), sessions=sessions)
        assert all(filed < date.fromisoformat(day) for filed in table["filed"].to_pylist())
        return sorted(set(table["accession"].to_pylist()))

    assert seen("2023-10-02") == []  # A1 is filed that day: not yet
    assert seen("2023-10-03") == ["A1"]
    assert seen("2023-10-04") == ["A4"]
    assert seen("2023-10-04", sessions=2) == ["A1", "A4"]
    assert seen("2023-10-06") == []
    assert seen("2023-10-09") == ["A2"]  # filed on Saturday, visible on Monday
    with pytest.raises(inputs.InputError, match="ends at 2023-10-07"):
        store.form4(date(2023, 10, 20))


def test_later_filings_are_hidden_when_a_past_session_is_replayed(world):
    settings, one, two = world
    first = inputs.build_form4(settings)
    day = date(2023, 10, 4)
    before = load_day(DataStore(settings), day, UNIVERSE, form4_sessions=5).view
    assert [d.accession for d in before.disclosures[one]] == ["A1", "A1", "A4"]
    assert two not in before.disclosures and before.disclosures[one][0].purchase_amount == 8000
    assert before.upto(600).disclosures == before.disclosures  # known before the open
    # Filings from that day and after arrive in a newer input: the session sees the same.
    _zip(settings.raw_dir, "2024q1", [
        ("C1", "04-OCT-2023", "4", one, [("P", 7, 7, "A")]),
        ("C2", "05-OCT-2023", "4", two, [("P", 8, 8, "A")]),
    ])  # fmt: skip
    second = inputs.build_form4(settings)
    assert second != first
    after = load_day(DataStore(settings), day, UNIVERSE, form4_sessions=5).view
    assert after.disclosures == before.disclosures
    next_day = load_day(DataStore(settings), date(2023, 10, 5), UNIVERSE, form4_sessions=1).view
    assert [d.accession for d in next_day.disclosures[one]] == ["C1"]
    # A store pinned to the first input still reads the first input.
    pinned = DataStore(settings, inputs={"form4": first})
    assert pinned.form4(date(2023, 10, 5)).num_rows == 0


STRATEGY = """
from kinn.core.types import Signal
from kinn.data.universe import Universe


class Buyers:
    name = "buyers"
    features = ()
    inputs = {"form4": {"sessions": 1}}
    universe = Universe("everything", min_sessions_prior=1)

    def signals(self, view, features):
        out = []
        for symbol, filings in view.disclosures.items():
            sd = view.symbols[symbol]
            if len(sd.minute) and any(d.purchase_amount for d in filings):
                out.append(Signal(symbol, int(sd.minute[0]), max_hold_minutes=30))
        return out


def build(params):
    return Buyers()
"""


def test_a_run_records_the_input_version_and_keeps_reading_it(world, tmp_path, monkeypatch):
    settings, one, two = world
    first = inputs.build_form4(settings)
    folder = tmp_path / "strategies" / "buyers"
    (folder / "configs").mkdir(parents=True)
    (folder / "strategy.py").write_text(STRATEGY)
    (folder / "strategy.yaml").write_text(
        "name: buyers\nfamily: buyers\nprior_trials: 0\ncost_calibration: ibkr_pro_tiered\n"
    )
    (folder / "configs" / "week.yaml").write_text(
        "period: {start: 2023-10-02, end: 2023-10-06}\nlookahead_check_rate: 1.0\n"
    )
    monkeypatch.setenv("KINN_STRATEGIES_DIR", str(tmp_path / "strategies"))
    run_dir = runner.start_run("buyers", "week", settings=settings, scratch=True, agent="test")
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["inputs"]["form4"]["input_id"] == first
    assert manifest["inputs"]["form4"]["version"] == inputs.FORM4_VERSION
    # A newer input appears before the run's sessions are simulated: the run does not see it.
    _zip(settings.raw_dir, "2024q1", [("D1", "04-OCT-2023", "4", two, [("P", 9, 9, "A")])])
    assert inputs.build_form4(settings) != first
    assert runner.continue_run(run_dir, settings=settings)
    metrics = json.loads((run_dir / "metrics.json").read_text())
    assert metrics["counts"]["signals"] == 1  # A1 on 3 October; D1 would have been a second


def test_one_companys_open_market_trades(world):
    settings, one, two = world
    inputs.build_form4(settings)
    table, meta = DataStore(settings).form4_of([one])
    assert meta["last_filed"] == "2023-10-07"
    assert sorted((r["accession"], r["transaction_code"]) for r in table.to_pylist()) == [
        ("A1", "P"),
        ("A1", "S"),
    ]
    assert DataStore(settings).form4_of([two])[0].num_rows == 1
