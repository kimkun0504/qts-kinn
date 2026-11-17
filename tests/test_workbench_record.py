"""The Workbench's research record: the board, a strategy's page, studies, trades and the paper
ledger, read from strategy.yaml records and hand-made run folders."""

from __future__ import annotations

import json
from datetime import date

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from apps.workbench import record

DRIFT = """
name: drift
owner: claude
family: swing
prior_trials: 100
status: developing
record:
  title: Drift
  idea: Drift in small companies
  horizon: 15 sessions
  verdict: passed_holdout
  result: "Holdout: +5% a trade"
  summary: Buy the jump.
  periods:
    - {key: holdout, label: Holdout, config: holdout, note: run once}
    - {key: search, label: Search years, config: research}
    - {key: test, label: Test years, config: never_run}
  in_test:
    - {title: Quality test, verdict: testing, label: "Unproven, in paper", result: no losing year}
  waiting: [Run the ledger.]
  studies:
    - {name: Holdout run, when: 2026-11-16, trials: 1, result: passed, verdict: passed}
    - {name: Exits, when: 2026-11-15, trials: 23, result: one lead, verdict: lead}
"""
SEARCH = """
name: search
owner: claude
family: swing
prior_trials: 12000
record:
  title: Search
  verdict: closed
  board: false
  studies: [{name: Grid, when: 2026-11-14, trials: 12000}]
"""
DIPS = """
name: dips
owner: claude
family: funds
prior_trials: 8
record: {title: Dips, horizon: days, verdict: closed, result: "0.1% a trade"}
"""


def _run(runs, run_id, strategy, config, *, family, start, end, agent="claude", scratch=False,
         status="complete", months=((2024, 1, 100.0), (2024, 2, -40.0))):  # fmt: skip
    folder = runs / run_id
    folder.mkdir(parents=True)
    manifest = {
        "schema": "manifest-1", "run_id": run_id, "kind": "swing", "strategy": strategy,
        "family": family, "prior_trials": 0, "config": config, "status": status,
        "scratch": scratch, "agent": agent, "started_at": f"2026-11-16T10:00:{len(run_id):02d}",
        "period": {"start": start, "end": end}, "git": {"branch": "b", "commit": "c" * 40,
                                                         "dirty": False},
        "data_build_id": "x", "resolved_config": {},
    }  # fmt: skip
    (folder / "manifest.json").write_text(json.dumps(manifest))
    side = {"mean_return": 0.05, "median_return": 0.01, "win_rate": 0.52, "total_net": 60.0,
            "sharpe": 1.4, "max_drawdown": -30.0}  # fmt: skip
    metrics = {"schema": "metrics-1", "equity": 20000.0, "trades": 2, "counts": {"signals": 5},
               "slippage_1x": side, "slippage_2x": {**side, "mean_return": 0.046, "sharpe": 1.3},
               "swing": {"marked_to_market": {"max_drawdown": -70.0}}}  # fmt: skip
    (folder / "metrics.json").write_text(json.dumps(metrics))
    days = [date(y, m, d) for y, m, _ in months for d in (3, 17)]
    net = [v / 2 for _, _, v in months for _ in (0, 1)]
    pq.write_table(pa.table({"date": days, "net": net}), folder / "equity.parquet")
    pq.write_table(
        pa.table({"day": [date(2024, 1, 17), date(2024, 2, 3)], "symbol": ["AAA", "BBB"],
                  "quantity": [10, 20], "entry_price": [10.0, 5.0], "exit_price": [11.0, 4.0],
                  "notional": [100.0, 100.0], "net": [9.0, -21.0], "net_2x": [8.0, -22.0],
                  "exit_reason": ["time", "time"], "tag": ["a", "b"], "extra": [1, 2]}),
        folder / "trades.parquet",
    )  # fmt: skip


@pytest.fixture
def world(tmp_path):
    strategies, runs = tmp_path / "strategies", tmp_path / "runs"
    for name, text in (("drift", DRIFT), ("search", SEARCH), ("dips", DIPS)):
        (strategies / name).mkdir(parents=True)
        (strategies / name / "strategy.yaml").write_text(text)
    (strategies / "_template").mkdir()
    (strategies / "_template" / "strategy.yaml").write_text("name: template\n")
    (strategies / "drift" / "REPORT.md").write_text("# Drift\n\nIt works.\n")
    _run(runs, "r1_holdout", "drift", "holdout", family="swing", start="2023-11-09",
         end="2026-11-06")  # fmt: skip
    _run(runs, "r2_research_old", "drift", "research", family="swing", start="2010-01-04",
         end="2022-12-30", months=((2010, 1, 1.0),))  # fmt: skip
    _run(runs, "r3_research_newer", "drift", "research", family="swing", start="2010-01-04",
         end="2022-12-30", months=((2010, 1, 10.0), (2010, 3, 5.0)))  # fmt: skip
    _run(runs, "r4_scratch", "drift", "holdout", family="swing", start="2023-11-09",
         end="2026-11-06", scratch=True)  # fmt: skip
    _run(runs, "r5_other", "gap_idea", "dev", family="gaps", start="2010-01-04",
         end="2016-12-30", agent="gpt")  # fmt: skip
    return runs, strategies


def test_the_board_lists_each_idea_once_with_its_family_trials_and_verdict(world):
    runs, strategies = world
    board = record.board(runs, strategies)
    ideas = [(r["idea"], r["group"], r["trials"], r["label"]) for r in board["rows"]]
    assert ideas == [
        ("Drift in small companies", "works", 12003, "Passed holdout"),  # 12,000 prior + 3 runs
        ("Quality test", "testing", None, "Unproven, in paper"),  # a variant: counted above
        ("Dips", "closed", 8, "Closed"),
    ]  # the search is board: false, the template is skipped
    assert board["counts"] == {"works": 1, "testing": 1, "closed": 1}
    assert board["waiting"] == [{"strategy": "drift", "text": "Run the ledger."}]
    assert board["others"] == [
        {"strategy": "gap_idea", "agent": "gpt", "runs": 1, "status": "not declared"}
    ]


def test_a_strategy_page_joins_its_record_to_the_latest_counted_run_of_each_period(world):
    runs, strategies = world
    page = record.strategy_page(runs, strategies, "drift")
    assert page["label"] == "Passed holdout" and page["trials"] == 12003 and page["runs"] == 4
    assert page["has_report"] and not page["has_hypothesis"]
    assert "studies" not in page["record"] and [s["name"] for s in page["studies"]] == [
        "Holdout run", "Exits"
    ]  # fmt: skip
    by_key = {p["key"]: p for p in page["periods"]}
    assert [p["key"] for p in page["periods"]] == ["search", "holdout", "test"]  # by start date
    assert by_key["search"]["run_id"] == "r3_research_newer"  # the newest, not the first
    assert by_key["search"]["months"] == [["2010-01", 10.0], ["2010-03", 5.0]]
    assert by_key["holdout"]["run_id"] == "r1_holdout"  # the scratch run is never used
    stats = by_key["holdout"]["stats"]
    assert stats["trades"] == 2 and stats["signals"] == 5 and stats["net_2x"] == 0.046
    assert stats["drawdown"] == -70.0  # marked daily, when the run has it
    assert [t["met"] for t in by_key["holdout"]["targets"]] == [True, True, True]
    assert by_key["search"]["targets"] is None  # targets are judged on the holdout only
    assert by_key["test"]["run_id"] is None and by_key["test"]["months"] == []
    assert record.strategy_page(runs, strategies, "nothing") is None
    assert record.strategy_page(runs, strategies, "../drift") is None


def test_studies_documents_and_trades(world):
    runs, strategies = world
    found = record.studies(strategies)
    assert [(s["name"], s["strategy"], s["trials"]) for s in found] == [
        ("Holdout run", "drift", 1), ("Exits", "drift", 23), ("Grid", "search", 12000)
    ]  # fmt: skip
    documents = record.documents(strategies, "drift")
    assert documents == {"report": "# Drift\n\nIt works.\n", "hypothesis": None}
    assert record.documents(strategies, "..") is None
    trades = record.trades(runs, "r1_holdout")
    assert trades["count"] == 2 and trades["rows"][0]["symbol"] == "BBB"  # newest first
    assert "extra" not in trades["rows"][0] and trades["rows"][1]["net"] == 9.0
    assert record.trades(runs, "missing") is None and record.trades(runs, "../runs") is None


def test_the_paper_ledger_is_read_from_its_snapshot_or_rebuilt_from_an_older_ledger(tmp_path):
    assert record.paper(tmp_path, {}, 15) is None
    state = {"last_session": "2026-11-16", "tracks": [
        {"symbol": "AAA", "signal_day": "2026-10-27", "status": "open", "sessions": 14,
         "entry_day": "2026-10-28", "entry_open": 10.0,
         "books": {"ten": {"shares": 200, "notional": 2000.0}}},
        {"symbol": "BBB", "signal_day": "2026-10-20", "status": "closed", "sessions": 15,
         "gross_return": -0.1,
         "books": {"ten": {"shares": 100, "notional": 2000.0, "net": -210.0, "net_2x": -220.0}}},
        {"symbol": "CCC", "signal_day": "2026-11-16", "status": "pending", "sessions": 0,
         "books": {}},
    ]}  # fmt: skip
    (tmp_path / "state.json").write_text(json.dumps(state))
    (tmp_path / "report.md").write_text(
        "## Held now\n\n| Stock | Signal | Bought | At | Now | Sessions | Books |\n|---|\n"
        "| AAA | 2026-10-27 | 2026-10-28 | 10.00 | 12.00 (+20.0%) | 14 of 15 | ten |\n"
        "\n## Results so far\n\n| ten | 1 | (-10.5%) |\n"
    )
    books = {
        "ten": {"account": 20000, "slots": 10},
        "ten_quality": {"account": 20000, "slots": 10, "skip_fallen_cash_rich": True},
    }
    old = record.paper(tmp_path, books, 15)
    assert old["schema"] == "paper-snapshot-0" and old["last_session"] == "2026-11-16"
    (position,) = old["positions"]
    assert position["symbol"] == "AAA" and position["change"] == pytest.approx(0.2)
    ten, quality = old["books"]
    assert ten["open"] == 1 and ten["unrealised"] == pytest.approx(400.0) and ten["net"] == -210.0
    assert quality["quality"] and quality["open"] == 0 and quality["trades"] == 0
    assert old["sell_next_close"] == [{"symbol": "AAA", "books": ["ten"]}]
    assert old["buy_next_open"] == [{"symbol": "CCC", "note": None}]
    assert old["followed"]["finished"] == 1 and old["followed"]["mean_gross"] == -0.1
    (tmp_path / "snapshot.json").write_text(json.dumps({"schema": "paper-snapshot-1"}))
    assert record.paper(tmp_path, books, 15) == {"schema": "paper-snapshot-1"}
