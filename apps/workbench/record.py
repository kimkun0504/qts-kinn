"""The research record for the Workbench: what was tested, what came of it, and where it stands.

Runs live in the run store; much of the research did not run through it (searches over
thousands of cells are measured by scripts). So each strategy folder carries a ``record:``
block in its ``strategy.yaml`` saying, in the owner's words, what the idea is, its verdict, the
evidence in order and the studies done. These functions join that block to the run store.
They read yaml, markdown and run files only: never strategy code, never market data.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pyarrow.parquet as pq
import yaml

from kinn.registry import runs as registry
from kinn.validation import targets

NAME = re.compile(r"^[a-z0-9_]+$")
# verdict -> (label, group). Groups: what works, what is still being tested, what is closed.
VERDICTS = {
    "passed_holdout": ("Passed holdout", "works"),
    "testing": ("In test", "testing"),
    "weak": ("Weak", "testing"),
    "failed_holdout": ("Failed holdout", "closed"),
    "parked": ("Parked", "closed"),
    "closed": ("Closed", "closed"),
}
MAX_TRADES = 5000


def _declared(strategies_dir: Path) -> dict[str, dict]:
    out = {}
    for path in sorted(strategies_dir.glob("*/strategy.yaml")):
        if path.parent.name.startswith("_"):
            continue
        try:
            out[path.parent.name] = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError:
            out[path.parent.name] = {}
    return out


def _trials(manifests: list[dict], declared: dict[str, dict], family: str) -> int:
    """Trials charged to a family: counted runs plus the largest declared count of prior looks."""
    runs = sum(
        1 for m in manifests
        if (m.get("family") or m["strategy"]) == family and registry.counts_as_trial(m)
    )  # fmt: skip
    prior = [int(m.get("prior_trials") or 0) for m in declared.values()
             if (m.get("family") or m.get("name")) == family]  # fmt: skip
    prior += [int(m.get("prior_trials") or 0) for m in manifests
              if (m.get("family") or m["strategy"]) == family]  # fmt: skip
    return runs + max(prior, default=0)


def _verdict(record: dict) -> tuple[str, str, str]:
    key = str(record.get("verdict") or "parked")
    label, group = VERDICTS.get(key, (key.replace("_", " ").capitalize(), "closed"))
    return key, str(record.get("label") or label), group


def board(runs_dir: Path, strategies_dir: Path) -> dict:
    """Everything tested, one row an idea, with what is waiting on the owner."""
    manifests = registry.read_manifests(runs_dir)
    declared = _declared(strategies_dir)
    rows, waiting = [], []
    for name, meta in declared.items():
        record = meta.get("record") or {}
        if not record or record.get("board") is False:
            continue
        key, label, group = _verdict(record)
        family = meta.get("family") or name
        rows.append({
            "strategy": name, "idea": record.get("idea") or record.get("title") or name,
            "title": record.get("title") or name, "owner": meta.get("owner") or "claude",
            "horizon": record.get("horizon"), "family": family,
            "trials": _trials(manifests, declared, family), "result": record.get("result"),
            "summary": record.get("short") or record.get("summary"),
            "verdict": key, "label": label, "group": group, "variant": False,
            "paper": bool(record.get("paper")),
        })  # fmt: skip
        for item in record.get("in_test") or []:
            _, item_label, item_group = _verdict(item)
            rows.append({
                "strategy": name, "idea": item.get("title"), "title": item.get("title"),
                "owner": meta.get("owner") or "claude", "horizon": record.get("horizon"),
                "family": family, "trials": None, "result": item.get("result"),
                "summary": item.get("summary"), "verdict": item.get("verdict") or "testing",
                "label": item_label, "group": item_group, "variant": True, "paper": False,
                "stats": item.get("stats") or [], "settle": item.get("settle") or [],
            })  # fmt: skip
        waiting += [{"strategy": name, "text": str(text)} for text in record.get("waiting") or []]
    order = {"works": 0, "testing": 1, "closed": 2}
    # Within a group the most-tested idea first; a variant sits at the head of its group.
    rows.sort(
        key=lambda r: (order[r["group"]], -(r["trials"] if r["trials"] is not None else 1e12))
    )
    # Ideas with runs and no record here: other agents' folders, which this checkout may not hold.
    known = {name for name, meta in declared.items() if meta.get("record")}
    others: dict[str, dict] = {}
    for m in manifests:
        name = m["strategy"]
        if name in known or m.get("status") == "abandoned":
            continue
        entry = others.setdefault(name, {"strategy": name, "agent": m["agent"], "runs": 0,
                                         "status": str((declared.get(name) or {}).get("status")
                                                       or "not declared")})  # fmt: skip
        entry["runs"] += 1
    counts = {g: sum(1 for r in rows if r["group"] == g) for g in order}
    return json.loads(json.dumps(
        {"rows": rows, "others": sorted(others.values(), key=lambda o: (o["agent"], o["strategy"])),
         "waiting": waiting, "counts": counts}, default=float))  # fmt: skip


def studies(strategies_dir: Path) -> list[dict]:
    """Every study recorded in a strategy folder, newest first."""
    out = []
    for name, meta in _declared(strategies_dir).items():
        record = meta.get("record") or {}
        for study in record.get("studies") or []:
            out.append({
                "strategy": name, "strategy_title": record.get("title") or name,
                "name": study.get("name"), "when": str(study.get("when") or ""),
                "trials": study.get("trials"), "result": study.get("result"),
                "verdict": study.get("verdict") or "note",
            })  # fmt: skip
    return sorted(out, key=lambda s: s["when"], reverse=True)


def _latest_run(manifests: list[dict], strategy: str, config: str) -> dict | None:
    found = [m for m in manifests if m["strategy"] == strategy and m["config"] == config
             and m.get("status") == "complete" and not m["scratch"]]  # fmt: skip
    return max(found, key=lambda m: m["started_at"]) if found else None


def _months(run_dir: Path) -> list[list]:
    """Net profit by calendar month, [["2024-03", 8150.2], ...], from the run's daily table."""
    path = run_dir / "equity.parquet"
    if not path.exists():
        return []
    table = pq.read_table(path, columns=["date", "net"]).to_pydict()
    sums: dict[str, float] = {}
    for day, net in zip(table["date"], table["net"], strict=True):
        key = str(day)[:7]
        sums[key] = sums.get(key, 0.0) + float(net or 0.0)
    return [[key, sums[key]] for key in sorted(sums)]


def _period(runs_dir: Path, manifests: list[dict], strategy: str, spec: dict) -> dict:
    out = {"key": spec.get("key"), "label": spec.get("label"), "note": spec.get("note"),
           "config": spec.get("config"), "run_id": None, "stats": None, "months": [],
           "targets": None}  # fmt: skip
    manifest = _latest_run(manifests, strategy, str(spec.get("config")))
    if manifest is None:
        return out
    run_dir = runs_dir / manifest["run_id"]
    metrics = json.loads((run_dir / "metrics.json").read_text())
    one, two = metrics.get("slippage_1x", {}), metrics.get("slippage_2x", {})
    marked = (metrics.get("swing") or {}).get("marked_to_market") or {}
    period = manifest["period"]
    out.update(
        run_id=manifest["run_id"], start=period["start"], end=period["end"],
        equity=metrics.get("equity"), months=_months(run_dir),
        stats={
            "trades": metrics.get("trades"),
            "signals": (metrics.get("counts") or {}).get("signals"),
            "net": one.get("mean_return"), "net_2x": two.get("mean_return"),
            "total": one.get("total_net"), "total_2x": two.get("total_net"),
            "sharpe": one.get("sharpe"), "sharpe_2x": two.get("sharpe"),
            "drawdown": marked.get("max_drawdown", one.get("max_drawdown")),
            "win_rate": one.get("win_rate"), "median": one.get("median_return"),
            "spread_crossed": (metrics.get("swing") or {}).get("spread_crossed_mean_return"),
        },
    )  # fmt: skip
    if spec.get("key") == "holdout" and two:
        out["targets"] = targets.check(metrics)
    return out


def strategy_page(runs_dir: Path, strategies_dir: Path, name: str) -> dict | None:
    """One strategy: its record, and the runs behind each period the record names."""
    declared = _declared(strategies_dir)
    if not NAME.match(name) or name not in declared:
        return None
    meta = declared[name]
    record = meta.get("record") or {}
    manifests = registry.read_manifests(runs_dir)
    key, label, group = _verdict(record)
    family = meta.get("family") or name
    periods = [_period(runs_dir, manifests, name, spec) for spec in record.get("periods") or []]
    periods.sort(key=lambda p: p.get("start") or "9999")
    folder = strategies_dir / name
    return json.loads(json.dumps({
        "strategy": name, "family": family, "owner": meta.get("owner"),
        "status": str(meta.get("status") or ""), "verdict": key, "label": label, "group": group,
        "trials": _trials(manifests, declared, family),
        "runs": sum(1 for m in manifests
                    if m["strategy"] == name and m.get("status") != "abandoned"),
        "record": {k: v for k, v in record.items() if k != "studies"},
        "studies": [s for s in studies(strategies_dir) if s["strategy"] == name],
        "periods": periods,
        "has_report": (folder / "REPORT.md").exists(),
        "has_hypothesis": (folder / "HYPOTHESIS.md").exists(),
    }, default=str))  # fmt: skip


def documents(strategies_dir: Path, name: str) -> dict | None:
    """The strategy's written report and plan, as markdown text."""
    if not NAME.match(name) or not (strategies_dir / name / "strategy.yaml").exists():
        return None
    out = {}
    for key, filename in (("report", "REPORT.md"), ("hypothesis", "HYPOTHESIS.md")):
        path = strategies_dir / name / filename
        out[key] = path.read_text() if path.exists() else None
    return out


def trades(runs_dir: Path, run_id: str) -> dict | None:
    """A run's trades, newest first (at most ``MAX_TRADES``)."""
    run_dir = runs_dir / run_id
    path = run_dir / "trades.parquet"
    if run_dir.resolve().parent != runs_dir.resolve() or not path.exists():
        return None
    columns = ["day", "symbol", "quantity", "entry_price", "exit_price", "notional", "net",
               "net_2x", "exit_reason", "tag"]  # fmt: skip
    table = pq.read_table(path)
    table = table.select([c for c in columns if c in table.column_names])
    rows = sorted(table.to_pylist(), key=lambda r: (str(r["day"]), r["symbol"]), reverse=True)
    return json.loads(json.dumps({"count": len(rows), "rows": rows[:MAX_TRADES]}, default=str))


def _held_from_page(page: str) -> dict[str, float]:
    """Each held stock's change since entry, read from an older ledger's report.md (before the
    ledger wrote snapshot.json)."""
    out, inside = {}, False
    for line in page.splitlines():
        if line.startswith("## "):
            inside = line.strip() == "## Held now"
            continue
        match = re.match(r"\| (\S+) \|.*\(([+-]\d+(?:\.\d+)?)%\)", line) if inside else None
        if match:
            out[match.group(1)] = float(match.group(2)) / 100
    return out


def paper(folder: Path, books: dict | None, hold: int | None) -> dict | None:
    """The paper ledger of one strategy: the snapshot its nightly run wrote, or, for a ledger
    from before snapshots, the same shape rebuilt from its state and report."""
    state_path = folder / "state.json"
    if not state_path.exists():
        return None
    state = json.loads(state_path.read_text())
    snapshot = folder / "snapshot.json"
    if snapshot.exists():
        try:
            data = json.loads(snapshot.read_text())
        except ValueError:
            data = None
        # A snapshot older than the ledger (a night it could not be built) is not shown.
        if data and data.get("last_session") == state.get("last_session"):
            return data
    page = (folder / "report.md").read_text() if (folder / "report.md").exists() else ""
    changes = _held_from_page(page)
    names = list(books or {}) or sorted({n for t in state["tracks"] for n in t["books"]})
    positions = []
    for t in state["tracks"]:
        if t["status"] != "open":
            continue
        positions.append({
            "symbol": t["symbol"], "signal_day": t["signal_day"], "entry_day": t.get("entry_day"),
            "entry_open": t.get("entry_open"), "last": None, "change": changes.get(t["symbol"]),
            "benchmark": None, "sessions": t["sessions"], "books": sorted(t["books"]),
            "kept": t.get("kept"), "note": None,
        })  # fmt: skip
    out_books = []
    for name in names:
        spec = (books or {}).get(name) or {}
        closed = [t["books"][name] for t in state["tracks"] if name in t["books"]
                  and "net" in t["books"][name]]  # fmt: skip
        held = [t for t in state["tracks"] if t["status"] == "open" and name in t["books"]]
        unrealised = sum(t["books"][name]["notional"] * changes.get(t["symbol"], 0.0) for t in held)
        out_books.append({
            "name": name, "account": spec.get("account"), "slots": spec.get("slots"),
            "quality": bool(spec.get("skip_fallen_cash_rich")), "exit": spec.get("exit"),
            "open": len(held), "unrealised": unrealised, "hedged": None, "trades": len(closed),
            "net": sum(r["net"] for r in closed), "net_2x": sum(r["net_2x"] for r in closed),
            "mean": (sum(r["net"] / r["notional"] for r in closed) / len(closed))
            if closed else None,
        })  # fmt: skip
    finished = [t for t in state["tracks"] if t["status"] == "closed"]
    gross = [t["gross_return"] for t in finished]
    return {
        "schema": "paper-snapshot-0", "last_session": state["last_session"], "hold": hold,
        "buy_next_open": [{"symbol": t["symbol"], "note": None} for t in state["tracks"]
                          if t["status"] == "pending"],
        "sell_next_open": [],
        "sell_next_close": [{"symbol": t["symbol"], "books": sorted(t["books"])}
                            for t in state["tracks"] if t["status"] == "open" and hold
                            and t["sessions"] + 1 >= hold],
        "positions": positions, "books": out_books,
        "followed": {"signals": len(state["tracks"]), "finished": len(finished),
                     "mean_gross": sum(gross) / len(gross) if gross else None,
                     "winners": sum(g > 0 for g in gross), "passed": None, "failed": None},
    }  # fmt: skip
