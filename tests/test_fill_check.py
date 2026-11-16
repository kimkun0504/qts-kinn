"""The fill check: a run's orders are rebuilt exactly, and ticks are compared the way the
hypothesis says (through-prints, latency, conditions, size)."""

import gzip
import importlib.util
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from kinn import fill_check
from kinn import run as runner
from kinn.core.settings import load_settings
from kinn.costs import model as cost_model
from kinn.data import build, quotes
from tests import synthetic_raw as syn

REPO = Path(__file__).resolve().parents[1]
COSTS = cost_model.load("ibkr_pro_tiered")
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
            if known.any():
                limit = round(float(sd.close[known][-1]) * 0.9995, 2)
                out.append(Signal(symbol, 600, limit_price=limit, expire_minute=610))
        return out


def build(params):
    return Dip()
"""
CONFIG = """
risk: {equity: 4000, position_dollars: 500, buying_power: 4000}
fills: {participation: 0.05, flatten_before_close: 0}
period: {start: 2023-10-02, end: 2023-11-08}
lookahead_check_rate: 0.0
"""


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("fills")
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
        "name: dip\ncost_calibration: ibkr_pro_tiered\nfamily: test_dip\n"
    )
    (folder / "configs" / "test.yaml").write_text(CONFIG)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("KINN_STRATEGIES_DIR", str(tmp / "strategies"))
        run_dir = runner.start_run("dip", "test", settings=settings, scratch=True, agent="t")
        assert runner.continue_run(run_dir, settings=settings)
        work = tmp / "work"
        assert not fill_check.list_orders(settings, run_dir.name, work, budget_seconds=-1)
        assert fill_check.list_orders(settings, run_dir.name, work)
    return settings, run_dir.name, work, tmp


def write_ticks(raw, order, trades, quote_rows=()):
    for kind, rows in (("trades", trades), ("quotes", quote_rows)):
        path = quotes.sample_file(raw, kind, order["day"], order["symbol"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wt") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")


def test_the_listing_reproduces_the_run_and_the_check_reads_ticks(world):
    settings, run_id, work, tmp = world
    orders = fill_check.read_orders(work, run_id)
    counts = fill_check.check_against_run(settings, run_id, orders)
    trades = pq.read_table(settings.runs_dir / run_id / "trades.parquet").to_pylist()
    assert counts["traded"] == len(trades) > 20
    assert counts["bar_filled"] >= counts["traded"]  # some fills had no capital
    assert counts["orders"] == counts["bar_filled"] + sum(
        counts[k] for k in ("touched", "near", "far")
    )

    out = fill_check.plan(
        settings, "plan", [run_id], work, labels={run_id: "validation"},
        per_cell={"touched": 3, "near": 3, "far": 3},
    )  # fmt: skip
    planned = pq.read_table(out / "orders.parquet").to_pylist()
    windows = quotes.read_windows(out / "windows.csv")
    assert len(windows) == len(planned) >= len(trades)  # one order a symbol a day here
    first = windows[0]
    assert first["entry_ns"] - first["start_ns"] == 60 * 10**9
    assert first["end_ns"] - first["entry_ns"] == 600 * 10**9

    raw = settings.raw_dir / "massive" / "quotes_sample" / "plan"
    traded = [o for o in planned if o["traded"]]
    late, early, none = traded[0::3], traded[1::3], traded[2::3]
    for group, seconds in ((late, 20), (early, 2), (none, None)):
        for o in group:
            _, live, end = fill_check.window_ns(o)
            below, limit = round(o["limit_price"] - 0.01, 2), o["limit_price"]
            rows = [
                {"sip_timestamp": live - 5, "price": below, "size": 10_000},  # before the order
                {"sip_timestamp": live + 30 * 10**9, "price": limit, "size": 700},  # a touch
                {"sip_timestamp": live + 40 * 10**9, "price": below, "size": 900,
                 "conditions": [37]},  # an odd lot: not a through-print
                {"sip_timestamp": live + 41 * 10**9, "price": below, "size": 900,
                 "correction": 8},  # cancelled
                {"sip_timestamp": end, "price": below, "size": 10_000},  # after expiry
            ]  # fmt: skip
            if seconds is not None:
                size = 2 * o["bar_quantity"] if group is late else 1
                rows.append({"sip_timestamp": live + seconds * 10**9, "price": below, "size": size})
            bid = below - 0.01 if group is late else limit + 0.01
            write_ticks(raw, o, rows, [
                {"sip_timestamp": live - 9, "bid_price": limit + 0.02, "ask_price": limit + 0.04},
                {"sip_timestamp": live + 25 * 10**9, "bid_price": bid, "ask_price": bid + 0.02},
            ])  # fmt: skip

    assert not fill_check.measure_orders(settings, "plan", work, costs=COSTS, budget_seconds=-1)
    assert fill_check.measure_orders(settings, "plan", work, costs=COSTS)
    rows = fill_check.assemble(settings, "plan", work)
    result = fill_check.evaluate(rows, COSTS, {run_id: "validation"})
    s = result["periods"]["validation"]["all"]
    assert s["orders"] == s["covered"] == len(traded) and s["coverage"] == 1.0
    n = len(traded)
    assert s["confirmed"] == pytest.approx((len(late) + len(early)) / n)
    assert s["confirmed_with_odd_lots"] == 1.0
    assert s["confirmed_after_5s"] == pytest.approx(len(late) / n)
    assert s["in_full_size"] == pytest.approx(len(late) / n)
    assert s["bid_fell_below_limit"] == pytest.approx(len(late) / n)
    assert s["tick_rule_5s"]["trades"] == len(late)
    assert s["tick_rule_0s"]["trades"] == len(late) + len(early)  # the early ones: one share
    # At the simulated size, the recomputed result is the simulator's own, to the cent.
    for o in late:
        again = fill_check.trade_result(COSTS, o["limit_price"], o["close"], o["bar_quantity"])
        assert again["net"] == pytest.approx(o["sim_net"], abs=1e-9)
        assert again["net_2x"] == pytest.approx(o["sim_net_2x"], abs=1e-9)
    verdict = fill_check.verdict(result, "validation")
    assert verdict["bars"]["coverage_at_least_95pct"]
    assert not verdict["bars"]["confirmed_at_least_97pct_each_period"] and not verdict["passed"]

    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("KINN_STRATEGIES_DIR", str(tmp / "strategies"))
        run_dir = fill_check.study(
            settings, "plan", work, strategy="dip", run_labels={run_id: "validation"},
            validation_label="validation", repo=REPO, scratch=True, agent="t",
            meta={"cost_calibration": "ibkr_pro_tiered", "family": "test_dip"},
        )  # fmt: skip
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["kind"] == "fill_check" and manifest["family"] == "test_dip"

    # A second plan that also reads the first fetches only the windows not yet on disk.
    again = fill_check.plan(
        settings, "plan2", [run_id], work, labels={run_id: "validation"},
        per_cell={"touched": 3, "near": 3, "far": 3}, also_reads=["plan"],
    )  # fmt: skip
    summary = json.loads((again / "plan.json").read_text())
    assert summary["windows_already_downloaded"] == len(traded)
    assert summary["windows"] == len(planned) - len(traded)
    assert len(quotes.read_windows(again / "windows.csv")) == summary["windows"]
    assert fill_check.raw_dirs(settings, "plan2") == [raw.parent / "plan2", raw]
    first = fill_check.order_ticks(
        traded[0], fill_check.raw_dirs(settings, "plan2"), frozenset(), 0.01
    )
    assert first["has_file"] and first["tag"] == ""
    assert "FAILED" in (run_dir / "fill_check.md").read_text()


def test_a_listing_that_does_not_match_the_run_is_refused(world):
    settings, run_id, work, _ = world
    orders = fill_check.read_orders(work, run_id)
    with pytest.raises(fill_check.OrdersMismatch):
        fill_check.check_against_run(settings, run_id, orders[:-1])
    traded = next(o for o in orders if o["kind"] == "filled")
    traded["bar_quantity"] += 1
    with pytest.raises(fill_check.OrdersMismatch):
        fill_check.check_against_run(settings, run_id, orders)


def test_conditions_come_from_the_vendor_table_when_it_is_there(tmp_path):
    assert fill_check.ineligible_conditions(tmp_path) == (
        fill_check.FALLBACK_INELIGIBLE, "fallback list",
    )  # fmt: skip
    table = [
        {"id": 14, "data_types": ["trade"],
         "update_rules": {"consolidated": {"updates_high_low": True}}},
        {"id": 37, "data_types": ["trade"],
         "update_rules": {"consolidated": {"updates_high_low": False}}},
        {"id": 99, "data_types": ["nbbo"],
         "update_rules": {"consolidated": {"updates_high_low": False}}},
    ]  # fmt: skip
    (tmp_path / "conditions.json").write_text(json.dumps(table))
    assert fill_check.ineligible_conditions(tmp_path) == (frozenset({37}), "vendor table")


def test_cap_groups():
    assert [fill_check.cap_group(v) for v in (None, 2.9e8, 3e8, 1.9e9, 2e9)] == [
        "unknown", "under $300M", "$300M–$2B", "$300M–$2B", "over $2B",
    ]  # fmt: skip


def test_owner_download_script_skips_done_files_and_survives_a_refused_window(
    tmp_path, monkeypatch, capsys
):
    spec = importlib.util.spec_from_file_location(
        "download_quotes", REPO / "tools" / "owner" / "download_quotes.py"
    )
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    plan = tmp_path / "data" / "quotes_sample" / "myplan"
    plan.mkdir(parents=True)
    (plan / "windows.csv").write_text(
        "day,symbol,signal_minute,entry_minute,entry_price,adv20_prev,start_ns,entry_ns,end_ns,"
        "bucket,period\n"
        "2020-03-02,AAA,600,601,10.0,1000000,1,2,3,b,p\n"
        "2020-03-02,BAD,600,601,10.0,,1,2,3,b,p\n"
    )
    monkeypatch.setenv("KINN_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("KINN_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("KINN_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("MASSIVE_API_KEY", "not-a-real-key")
    calls = []

    def fake(url, key):
        calls.append(url)
        assert url.startswith("https://api.massive.com/") and key == "not-a-real-key"
        if "/BAD?" in url:
            raise script.FetchError("HTTP 404")
        return [{"id": 1}] if "conditions" in url else [{"sip_timestamp": 2, "price": 9.0}]

    monkeypatch.setattr(script, "fetch_all", fake)
    monkeypatch.setattr(
        "sys.argv", ["download_quotes.py", str(plan / "windows.csv"), "--workers", "2"]
    )
    script.main()
    out = tmp_path / "raw" / "massive" / "quotes_sample" / "myplan"
    assert (out / "conditions.json").exists()
    assert sorted(p.name for p in (out / "trades").iterdir()) == ["2020-03-02_AAA.jsonl.gz"]
    assert len((out / "failed.txt").read_text().splitlines()) == 2
    assert "not-a-real-key" not in capsys.readouterr().out
    before = len(calls)
    script.main()  # a second pass fetches only what is missing
    assert len(calls) - before == 2


def test_owner_download_script_refuses_holdout_dates(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "download_quotes", REPO / "tools" / "owner" / "download_quotes.py"
    )
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    plan = tmp_path / "data" / "quotes_sample" / "p"
    plan.mkdir(parents=True)
    (plan / "windows.csv").write_text(
        "day,symbol,signal_minute,entry_minute,entry_price,adv20_prev,start_ns,entry_ns,end_ns,"
        "bucket,period\n2023-11-09,AAA,600,601,10.0,1000000,1,2,3,b,p\n"
    )
    monkeypatch.setenv("KINN_RAW_DIR", str(tmp_path / "raw"))
    monkeypatch.setenv("KINN_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MASSIVE_API_KEY", "not-a-real-key")
    monkeypatch.setattr(script, "fetch_all", lambda url, key: pytest.fail("no request expected"))
    monkeypatch.setattr("sys.argv", ["download_quotes.py", str(plan / "windows.csv")])
    with pytest.raises(Exception, match="(?i)holdout|seal"):
        script.main()
