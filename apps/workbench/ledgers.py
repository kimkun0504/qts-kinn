"""The event ledgers kept beside the earnings drift's: big prints and the after-hours short.

Each is read from the state.json its owner tool writes (tools/owner/paper_*.py) and served in
one shape (schema paper-ledger-1), so the Paper page shows every ledger the same way. Nothing
here writes to a ledger.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from kinn import after_hours_paper as ahp
from kinn import big_prints_paper as bpp

STAKE = 2_000.0


@dataclass(frozen=True)
class Ledger:
    name: str
    title: str
    strategy: str
    side: str
    rule: str
    alternative: str
    benchmark: str | None
    command: str
    schedule: str
    folder: Callable[[Path], Path]
    row: Callable[[dict], dict]
    evenings: Callable[[dict], list[dict]]


def _after_hours_row(s: dict) -> dict:
    closed = s.get("net") is not None
    return {
        "day": s["day"], "symbol": s["symbol"], "market_cap": s.get("market_cap"),
        "entry_day": s["day"], "entry": s.get("entry"), "exit_day": None,
        "exit": s.get("next_open"), "gross": s.get("gross"), "net": s.get("net"),
        "alternative": s.get("net_1530"), "benchmark": None,
        "status": "closed" if closed else "open", "set_aside": False, "move": s.get("reaction"),
        "accepted": s.get("accepted"),
        "thin": s.get("entry_dollars") is not None and s["entry_dollars"] < ahp.THIN,
        "borrow": s.get("borrow") or None,
    }  # fmt: skip


def _big_prints_row(s: dict) -> dict:
    status = (
        "waiting" if s.get("entry") is None
        else "closed" if s.get("net") is not None
        else "open"
    )  # fmt: skip
    return {
        "day": s["day"], "symbol": s["symbol"], "market_cap": s.get("market_cap"),
        "entry_day": s.get("entry_day"), "entry": s.get("entry"), "exit_day": s.get("exit_day"),
        "exit": s.get("exit"), "gross": s.get("gross"), "net": s.get("net"),
        "alternative": s.get("net_40"), "benchmark": s.get("benchmark"), "status": status,
        "set_aside": bool(s.get("index_day")), "move": s.get("ret"),
        "footprint": s.get("footprint"), "volume_ratio": s.get("volume_ratio"),
        "stopped": bool(s.get("stopped")),
    }  # fmt: skip


def _after_hours_evenings(state: dict) -> list[dict]:
    looked = Counter(s["day"] for s in state.get("seen", []))
    signals = Counter(s["day"] for s in state.get("signals", []))
    filers = state.get("filers") or {}
    partial = state.get("partial") or {}
    out = []
    for day in state.get("evenings", []):
        note = (
            "read in part" if day in partial
            else "SEC closed" if filers.get(day) == 0
            else "read before filer counts" if day not in filers
            else None
        )  # fmt: skip
        out.append({"day": day, "filers": filers.get(day), "looked_at": looked[day],
                    "signals": signals[day], "note": note})  # fmt: skip
    return out


def _big_prints_evenings(state: dict) -> list[dict]:
    looked = Counter(s["day"] for s in state.get("screened", []))
    signals = Counter(s["day"] for s in state.get("signals", []))
    out = []
    for evening in state.get("evenings", []):
        day = evening["day"]
        index_day = evening.get("share", 0.0) >= bpp.SHARE_MAX
        out.append({"day": day, "filers": None, "looked_at": looked[day] + signals[day],
                    "signals": signals[day], "share": evening.get("share"),
                    "note": "index day: signals set aside" if index_day else None})  # fmt: skip
    return out


LEDGERS = {
    "big_prints": Ledger(
        name="big_prints",
        title="Big prints",
        strategy="big_prints",
        side="long",
        rule=(
            "A company of $50M to $300M trading in pieces three times its normal size on a quiet "
            "up day with no recent 8-K: bought at the next open, sold at the close 20 sessions "
            "later."
        ),
        alternative="Held 40 sessions",
        benchmark="IWM",
        command="uv run python tools/owner/paper_big_prints.py",
        schedule="each evening after 16:30",
        folder=bpp.paper_dir,
        row=_big_prints_row,
        evenings=_big_prints_evenings,
    ),
    "after_hours": Ledger(
        name="after_hours",
        title="After-hours short",
        strategy="after_hours",
        side="short",
        rule=(
            "A company of $300M to $2B down 15% or more half an hour after an after-close results "
            "8-K: sold short at the low of the next minute, bought back at the next open."
        ),
        alternative="Held to 15:30",
        benchmark=None,
        command="uv run python tools/owner/paper_after_hours.py",
        schedule="each morning after 09:35",
        folder=ahp.paper_dir,
        row=_after_hours_row,
        evenings=_after_hours_evenings,
    ),
}


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summary(rows: list[dict]) -> dict:
    rule = [r for r in rows if not r["set_aside"]]
    closed = [r for r in rule if r["status"] == "closed"]
    net = [r["net"] for r in closed]
    alternative = [r["alternative"] for r in closed if r["alternative"] is not None]
    over = [r["net"] - r["benchmark"] for r in closed if r["benchmark"] is not None]
    aside = [r["net"] for r in rows if r["set_aside"] and r["status"] == "closed"]
    return {
        "signals": len(rule), "closed": len(closed),
        "open": sum(r["status"] == "open" for r in rule),
        "waiting": sum(r["status"] == "waiting" for r in rule),
        "mean": _mean(net), "winners": sum(n > 0 for n in net),
        "profit": STAKE * sum(net), "alternative": _mean(alternative),
        "alternative_count": len(alternative), "over_benchmark": _mean(over),
        "set_aside": sum(r["set_aside"] for r in rows), "set_aside_closed": len(aside),
        "set_aside_mean": _mean(aside),
        "borrow_recorded": sum(bool(r.get("borrow")) for r in rule),
    }  # fmt: skip


def curve(rows: list[dict]) -> list[dict]:
    closed = sorted(
        (r for r in rows if r["status"] == "closed" and not r["set_aside"]),
        key=lambda r: (r["exit_day"] or r["day"], r["symbol"]),
    )
    total, out = 0.0, []
    for r in closed:
        total += STAKE * r["net"]
        out.append({"day": r["exit_day"] or r["day"], "symbol": r["symbol"], "total": total})
    return out


def _state(ledger: Ledger, runs_dir: Path) -> tuple[dict, Path] | None:
    path = ledger.folder(runs_dir) / "state.json"
    try:
        return json.loads(path.read_text()), path
    except (FileNotFoundError, ValueError):
        return None


def _updated(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()


def head(ledger: Ledger, state: dict, path: Path) -> dict:
    rows = [ledger.row(s) for s in state.get("signals", [])]
    evenings = [e if isinstance(e, str) else e["day"] for e in state.get("evenings", [])]
    return {
        "schema": "paper-ledger-1", "name": ledger.name, "title": ledger.title,
        "strategy": ledger.strategy, "side": ledger.side, "rule": ledger.rule,
        "alternative": ledger.alternative, "benchmark": ledger.benchmark, "stake": STAKE,
        "command": ledger.command, "schedule": ledger.schedule,
        "updated": _updated(path), "evenings": len(evenings),
        "last_evening": max(evenings) if evenings else None, "summary": summary(rows),
    }  # fmt: skip


def ledgers(runs_dir: Path) -> list[dict]:
    out = []
    for ledger in LEDGERS.values():
        found = _state(ledger, runs_dir)
        if found:
            out.append(head(ledger, *found))
    return out


def ledger(runs_dir: Path, name: str) -> dict | None:
    spec = LEDGERS.get(name)
    found = _state(spec, runs_dir) if spec else None
    if not found:
        return None
    state, path = found
    rows = sorted((spec.row(s) for s in state.get("signals", [])),
                  key=lambda r: (r["day"], r["symbol"]), reverse=True)  # fmt: skip
    return {**head(spec, state, path), "rows": rows, "curve": curve(rows),
            "evening_rows": list(reversed(spec.evenings(state)))}  # fmt: skip
