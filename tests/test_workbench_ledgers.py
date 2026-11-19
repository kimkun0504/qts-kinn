import json
from datetime import date

from apps.workbench import ledgers
from kinn import after_hours_paper as ahp
from kinn import big_prints_paper as bpp


def after_hours_signal(day, symbol, net, held, entry_dollars=80_000.0, borrow=None):
    return {
        "day": day, "cik": 1, "symbol": symbol, "accepted": "16:05", "market_cap": 5e8,
        "adv": 3e6, "reaction": -0.2, "traded": 9e4, "entry": 10.0,
        "entry_dollars": entry_dollars, "next_open": None if net is None else 9.0,
        "gross": None if net is None else 0.1, "net": net, "price_1530": None,
        "net_1530": held, "borrow": borrow,
    }  # fmt: skip


def write(folder, state):
    folder.mkdir(parents=True)
    (folder / "state.json").write_text(json.dumps(state))


def test_the_after_hours_ledger_in_the_common_shape(tmp_path, monkeypatch):
    monkeypatch.setenv("KINN_PAPER_DIR", str(tmp_path / "paper"))
    runs = tmp_path / "runs"
    state = ahp.new_state()
    ahp.record(state, date(2026, 11, 9), [after_hours_signal("2026-11-09", "AAA", 0.05, 0.10)],
               [{"day": "2026-11-09", "cik": 1, "symbol": "AAA", "why": "signal"},
                {"day": "2026-11-09", "cik": 2, "symbol": "BBB", "why": "not down 15%"}],
               filers=700)  # fmt: skip
    ahp.record(state, date(2026, 11, 11), [], [], filers=0)
    ahp.record(state, date(2026, 11, 12),
               [after_hours_signal("2026-11-12", "CCC", -0.02, None, 1_000.0, "yes, 3%")], [],
               filers=600, read=[3], complete=False)  # fmt: skip
    write(ahp.paper_dir(runs), state)
    heads = ledgers.ledgers(runs)
    assert [h["name"] for h in heads] == ["after_hours"]
    page = ledgers.ledger(runs, "after_hours")
    assert page["schema"] == "paper-ledger-1" and page["side"] == "short"
    assert [r["symbol"] for r in page["rows"]] == ["CCC", "AAA"]
    ccc = page["rows"][0]
    assert ccc["thin"] and ccc["borrow"] == "yes, 3%" and ccc["status"] == "closed"
    s = page["summary"]
    assert s["signals"] == 2 and s["closed"] == 2 and s["winners"] == 1
    assert abs(s["mean"] - 0.015) < 1e-12 and abs(s["profit"] - 60.0) < 1e-9
    assert s["alternative"] == 0.10 and s["alternative_count"] == 1 and s["borrow_recorded"] == 1
    assert [p["total"] for p in page["curve"]] == [100.0, 60.0]
    notes = {e["day"]: e for e in page["evening_rows"]}
    assert notes["2026-11-12"]["note"] == "read in part"
    assert notes["2026-11-11"]["note"] == "SEC closed"
    assert notes["2026-11-09"]["looked_at"] == 2 and notes["2026-11-09"]["filers"] == 700
    assert ledgers.ledger(runs, "big_prints") is None and ledgers.ledger(runs, "nope") is None


def test_big_prints_sets_index_day_signals_apart(tmp_path, monkeypatch):
    monkeypatch.setenv("KINN_PAPER_DIR", str(tmp_path / "paper"))
    runs = tmp_path / "runs"
    base = {"footprint": 4.0, "adv": 1e6, "prev_close": 10.0, "close": 10.2, "ret": 0.02,
            "volume_ratio": 2.0, "market_cap": 1e8}  # fmt: skip
    state = {
        "strategy": "big_prints",
        "evenings": [{"day": "2026-10-20", "share": 0.01}, {"day": "2026-10-21", "share": 0.08}],
        "signals": [
            {**base, "day": "2026-10-20", "symbol": "AAA", "entry_day": "2026-10-21",
             "entry": 10.0, "exit_day": "2026-11-18", "exit": 11.0, "gross": 0.1, "net": 0.09,
             "benchmark": 0.02, "net_40": None},
            {**base, "day": "2026-10-20", "symbol": "BBB", "entry_day": "2026-10-21",
             "entry": 10.0},
            {**base, "day": "2026-10-21", "symbol": "CCC", "index_day": True},
        ],
        "screened": [{**base, "day": "2026-10-20", "symbol": "DDD", "why": "news"}],
    }  # fmt: skip
    write(bpp.paper_dir(runs), state)
    page = ledgers.ledger(runs, "big_prints")
    s = page["summary"]
    assert s["signals"] == 2 and s["closed"] == 1 and s["open"] == 1 and s["set_aside"] == 1
    assert abs(s["over_benchmark"] - 0.07) < 1e-12 and page["benchmark"] == "IWM"
    statuses = {r["symbol"]: r["status"] for r in page["rows"]}
    assert statuses == {"AAA": "closed", "BBB": "open", "CCC": "waiting"}
    notes = {e["day"]: e for e in page["evening_rows"]}
    assert notes["2026-10-21"]["note"].startswith("index day")
    assert notes["2026-10-20"]["looked_at"] == 3 and notes["2026-10-20"]["signals"] == 2
    assert page["curve"] == [{"day": "2026-11-18", "symbol": "AAA", "total": 180.0}]
