"""The paper trader is the backtest run a minute at a time: replaying a session must give the
backtest's trades exactly. Plus the halt, the saved record and the controls."""

import json
import threading
import urllib.error
import urllib.request
from datetime import date
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from apps.trader.__main__ import Handler
from apps.trader.engine import Session
from apps.trader.service import NoCandidate, Trader, paper_dir
from apps.trader.tape import ReplayTape
from kinn import run as runner
from kinn.core.settings import load_settings
from kinn.costs import model as cost_model
from kinn.data import build
from kinn.data.store import DataStore
from kinn.engine.intraday.simulator import FillConfig
from kinn.risk.sizing import RiskConfig
from tests import synthetic_raw as syn

REPO = Path(__file__).resolve().parents[1]
DIP = """
from kinn.core.types import Signal
from kinn.data.universe import Universe


class Dip:
    name, features = "dip", ()
    universe = Universe("dip", min_sessions_prior=5)

    def signals(self, view, features):
        out = []
        for symbol, sd in view.symbols.items():
            known = sd.minute <= 600
            if known.any() and sd.minute[known][-1] == 600:
                close = float(sd.close[known][-1])
                for share, offset, tag in ((0.5, 0.0003, "near"), (0.5, 0.0009, "deep")):
                    out.append(Signal(symbol, 600, limit_price=round(close * (1 - offset), 2),
                                      expire_minute=620, weight=share, tag=tag))
        return out


def build(params):
    return Dip()
"""
# Buying power for five positions among twenty signals: capital runs out every session.
CONFIG = """
risk: {equity: 4000, position_dollars: 800, buying_power: 4000}
fills: {participation: 0.05, flatten_before_close: 0}
period: {start: 2023-10-02, end: 2023-10-13}
lookahead_check_rate: 1.0
"""


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("trader")
    raw = syn.make_random_walk_raw(tmp / "raw")
    settings = load_settings(
        {
            "KINN_RAW_DIR": str(raw),
            "KINN_DATA_DIR": str(tmp / "processed"),
            "KINN_RUNS_DIR": str(tmp / "runs"),
        }
    )
    assert build.build_bars(settings, budget_seconds=300, workers=2)[1] == 0
    assert not build.build_tables(settings)[1]
    folder = tmp / "strategies" / "dip"
    (folder / "configs").mkdir(parents=True)
    (folder / "strategy.py").write_text(DIP)
    (folder / "strategy.yaml").write_text(
        "name: dip\ncost_calibration: ibkr_pro_tiered\nfamily: test_dip\ncandidate: test\n"
    )
    (folder / "configs" / "test.yaml").write_text(CONFIG)
    (tmp / "strategies" / "idle").mkdir()
    (tmp / "strategies" / "idle" / "strategy.yaml").write_text("name: idle\nstatus: parked\n")
    patch = pytest.MonkeyPatch()
    patch.setenv("KINN_STRATEGIES_DIR", str(tmp / "strategies"))
    patch.setenv("KINN_PAPER_DIR", str(tmp / "paper"))
    run_dir = runner.start_run("dip", "test", settings=settings, scratch=True, agent="t")
    assert runner.continue_run(run_dir, settings=settings)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    manifest["scratch"] = False  # the trader's yardstick is a counted run
    (run_dir / "manifest.json").write_text(json.dumps(manifest))
    yield settings, run_dir
    patch.undo()


def backtest_trades(run_dir, day):
    rows = pq.read_table(run_dir / "trades.parquet").to_pylist()
    return {
        (t["symbol"], t["tag"]): (t["quantity"], t["entry_minute"], t["entry_price"], t["net"])
        for t in rows if t["day"] == day
    }  # fmt: skip


def paper_session(settings, day):
    meta, config = runner.load_config("dip", "test")
    strategy = runner.load_strategy("dip", {})
    tape = ReplayTape(DataStore(settings), day, strategy.universe)
    session = Session(
        day=day, strategy=strategy, risk=RiskConfig(**config["risk"]),
        fills=FillConfig(**config["fills"]), costs=cost_model.load(meta["cost_calibration"]),
        open_minute=tape.open_minute, close_minute=tape.close_minute,
    )  # fmt: skip
    return session, tape


def test_replaying_a_session_gives_exactly_the_backtest_trades(world):
    settings, run_dir = world
    total = 0
    days = json.loads((run_dir / "manifest.json").read_text())["sessions"]
    for day in (date.fromisoformat(d) for d in days):  # every session of the backtest
        session, tape = paper_session(settings, day)
        for minute, view in tape.minutes():
            session.step(minute, view)
        trades = session.finish(*tape.close())
        got = {
            (t.symbol, t.tag): (t.quantity, t.entry_minute, t.entry_price, t.net) for t in trades
        }
        want = backtest_trades(run_dir, day)
        assert got.keys() == want.keys()
        for key, value in want.items():
            assert got[key] == pytest.approx(value, abs=1e-9)
        # Capital ran out, as in the backtest: some orders were refused for buying power.
        assert any(r.note == "not enough buying power" for r in session.rungs)
        assert session.curve[-1][1] == pytest.approx(sum(t.net for t in trades))
        total += len(trades)
    all_trades = pq.read_table(run_dir / "trades.parquet").num_rows
    assert total == all_trades >= 10


def test_a_halt_cancels_resting_orders_and_keeps_positions_to_the_close(world):
    settings, _ = world
    day = date(2023, 10, 3)
    free, tape = paper_session(settings, day)
    halted, _ = paper_session(settings, day)
    for minute, view in tape.minutes():
        free.step(minute, view)
        halted.step(minute, view)
        if minute == 603:
            halted.halt()
            assert not any(r.status == "working" for r in halted.rungs)
    free.finish(*tape.close())
    trades = halted.finish(*tape.close())
    before = [f for r in halted.rungs for f in r.entry]
    assert all(f.minute <= 603 for f in before)  # nothing filled after the halt
    assert len(before) < sum(len(r.entry) for r in free.rungs)  # the halt did cost fills
    assert all(t.exit_reason == "auction" and t.exit_minute == halted.close_minute for t in trades)
    assert {t.symbol for t in trades} == {r.symbol for r in halted.rungs if r.entry}
    assert any(e["kind"] == "halt" for e in halted.events)


def test_the_trader_replays_saves_and_refuses_the_holdout(world):
    settings, run_dir = world
    trader = Trader(settings, "dip", repo=REPO)
    assert trader.spec()["config"] == "test" and trader.expected["run_id"] == run_dir.name
    assert trader.snapshot()["session"] is None and trader.snapshot()["live"]["available"] is False
    with pytest.raises(ValueError, match="holdout"):
        trader.start_replay(date(2023, 11, 9))
    trader.start_replay(date(2023, 10, 9))
    trader.wait()
    state = trader.snapshot()
    assert (state["status"], state["error"]) == ("finished", None)
    summary = state["session"]["summary"]
    want = backtest_trades(run_dir, date(2023, 10, 9))
    assert summary["trades"] == len(want)
    assert summary["net"] == pytest.approx(sum(v[3] for v in want.values()))
    ladder = next(row for row in state["session"]["ladders"] if row["state"] == "closed")
    assert [r["tag"] for r in ladder["rungs"]] == ["near", "deep"] and ladder["net"] is not None
    assert state["session"]["tape"][0]["kind"] == "session"
    saved = trader.saved_session(state["saved"])
    assert saved["schema"] == "paper-session-1" and saved["mode"] == "replay"
    assert len(saved["trades"]) == len(want) and saved["spec"]["strategy"] == "dip"
    assert (paper_dir(settings) / "replay" / f"{state['saved']}.json").exists()
    assert trader.sessions()[0]["id"] == state["saved"]
    assert trader.suggested_days(3)["days"]
    with pytest.raises(NoCandidate):
        Trader(settings, "idle", repo=REPO)


def test_controls_need_the_page_header_and_listen_locally(world):
    settings, _ = world
    Handler.trader = Trader(settings, "dip", repo=REPO)
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(REPO)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    def post(path, body, headers):
        request = urllib.request.Request(
            base + path, data=json.dumps(body).encode(), method="POST",
            headers={"Content-Type": "application/json", **headers},
        )  # fmt: skip
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    try:
        with pytest.raises(urllib.error.HTTPError) as refused:
            post("/api/replay", {"day": "2023-10-09"}, {})
        assert refused.value.code == 403
        with pytest.raises(urllib.error.HTTPError) as sealed:
            post("/api/replay", {"day": "2024-01-05"}, {"X-Kinn-Trader": "1"})
        assert sealed.value.code == 409
        started = post("/api/replay", {"day": "2023-10-09"}, {"X-Kinn-Trader": "1"})
        assert started["mode"] == "replay"
        Handler.trader.wait()
        with urllib.request.urlopen(base + "/api/state", timeout=30) as response:
            assert json.load(response)["status"] == "finished"
    finally:
        server.shutdown()
