"""The trader as a running thing: one session at a time, a thread that steps it, and the
snapshot the screen reads. Finished sessions are written to the paper folder."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import UTC, date, datetime
from pathlib import Path

import pyarrow.parquet as pq
import yaml

from apps.trader.engine import Rung, Session
from apps.trader.tape import ReplayTape, Tape
from kinn.core.settings import HOLDOUT_START, Settings
from kinn.costs import model as cost_model
from kinn.data.store import DataStore
from kinn.engine.intraday.simulator import FillConfig
from kinn.registry import runs as registry
from kinn.risk.sizing import RiskConfig
from kinn.run import REPO_ROOT, load_config, load_strategy, strategies_dir

TAPE_ROWS = 250
MAIN_EVENTS = ("fill", "closed", "halt", "resume", "session")
LADDER_ROWS = 80


def paper_dir(settings: Settings) -> Path:
    """Where finished sessions are kept: beside the run store, never inside it."""
    return Path(os.environ.get("KINN_PAPER_DIR") or settings.runs_dir.parent / "paper")


def clock(minute: int | None) -> str | None:
    return None if minute is None else f"{minute // 60:02d}:{minute % 60:02d}"


class NoCandidate(RuntimeError):
    """The strategy has no candidate config to trade."""


class Trader:
    """Runs the strategy's candidate config. One session at a time."""

    def __init__(self, settings: Settings, strategy: str, *, repo: Path = REPO_ROOT):
        self.settings = settings
        self.strategy_name, self.config_name = strategy, self._candidate(strategy)
        self.meta, self.config = load_config(strategy, self.config_name)
        self.costs = cost_model.load(self.meta["cost_calibration"])
        self.risk = RiskConfig(**self.config.get("risk", {}))
        self.fills = FillConfig(**self.config.get("fills", {}))
        try:
            self.commit = registry.git_state(repo)["commit"][:8]
        except Exception:  # not a git checkout: the app still runs
            self.commit = None
        self._lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.session: Session | None = None
        self.tape: Tape | None = None
        self.mode = "idle"
        self.status = "idle"  # idle | loading | running | halted | finished | stopped | failed
        self.error: str | None = None
        self.speed = 0.0
        self.saved: str | None = None
        self.expected = self._expected()

    @staticmethod
    def _candidate(strategy: str) -> str:
        meta = yaml.safe_load((strategies_dir() / strategy / "strategy.yaml").read_text()) or {}
        if not meta.get("candidate"):
            raise NoCandidate(f"{strategy} names no candidate config in its strategy.yaml")
        return str(meta["candidate"])

    def _expected(self) -> dict | None:
        """What the candidate's own validation run did: the yardstick for paper results."""
        found = None
        for manifest in registry.read_manifests(self.settings.runs_dir):
            if (
                manifest["strategy"] == self.strategy_name
                and manifest["config"] == self.config_name
                and manifest["status"] == "complete"
                and not manifest["scratch"]
                and manifest.get("kind", "backtest") == "backtest"
            ):
                found = manifest
        if found is None:
            return None
        metrics = json.loads(
            (self.settings.runs_dir / found["run_id"] / "metrics.json").read_text()
        )
        one, two, counts = metrics["slippage_1x"], metrics["slippage_2x"], metrics["counts"]
        placed = counts["signals"] - counts["rejected_capital"] - counts["rejected_size"]
        return {
            "run_id": found["run_id"], "period": found["period"],
            "net_per_trade_1x": one["mean_return"], "net_per_trade_2x": two["mean_return"],
            "win_rate": one["win_rate"], "trades_per_session": metrics["trades_per_session"],
            "net_per_session": one["total_net"] / metrics["sessions"],
            "fill_share": metrics["trades"] / placed if placed else None,
            "sessions_with_trades": metrics["sessions_with_trades"] / metrics["sessions"],
        }  # fmt: skip

    # -- controls --------------------------------------------------------------------------
    def start_replay(self, day: date, *, seconds_per_minute: float = 0.0) -> None:
        """Play a past session through the paper book as if it were live."""
        if day >= HOLDOUT_START:
            raise ValueError(
                f"{day} is in the sealed holdout; only earlier sessions can be replayed"
            )
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise RuntimeError("a session is already running; stop it first")
            self._stop.clear()
            self.mode, self.status, self.error, self.saved = "replay", "loading", None, None
            self.speed = max(0.0, float(seconds_per_minute))
            self.session = self.tape = None
            self._thread = threading.Thread(target=self._run_replay, args=(day,), daemon=True)
            self._thread.start()

    def _run_replay(self, day: date) -> None:
        try:
            strategy = load_strategy(self.strategy_name, self.config.get("params", {}))
            tape = ReplayTape(DataStore(self.settings), day, strategy.universe)
            session = Session(
                day=day, strategy=strategy, risk=self.risk, fills=self.fills, costs=self.costs,
                open_minute=tape.open_minute, close_minute=tape.close_minute,
            )  # fmt: skip
            with self._lock:
                self.tape, self.session, self.status = tape, session, "running"
            for minute, view in tape.minutes():
                if self._stop.is_set():
                    with self._lock:
                        self.status = "stopped"
                    return
                with self._lock:
                    session.step(minute, view)
                if self.speed:
                    self._stop.wait(self.speed)
            with self._lock:
                session.finish(*tape.close())
                self.status = "finished"
                self.saved = self._save(session)
        except Exception as error:  # shown on the screen instead of dying silently
            with self._lock:
                self.status, self.error = "failed", f"{type(error).__name__}: {error}"

    def halt(self) -> None:
        with self._lock:
            if self.session and not self.session.finished:
                self.session.halt()
                self.status = "halted"

    def resume(self) -> None:
        with self._lock:
            if self.session and self.session.halted and not self.session.finished:
                self.session.resume()
                self.status = "running"

    def stop(self) -> None:
        """Abandon the session being replayed. Nothing is saved."""
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=10)

    def wait(self, timeout: float = 600.0) -> None:
        if self._thread:
            self._thread.join(timeout=timeout)

    # -- what the screen reads -------------------------------------------------------------
    def spec(self) -> dict:
        params = self.config.get("params", {})
        ladder = params.get("ladder") or [[params.get("limit_offset", 0.0), 1.0]]
        return {
            "strategy": self.strategy_name, "config": self.config_name, "commit": self.commit,
            "equity": self.risk.equity, "position_dollars": self.risk.position_dollars,
            "buying_power": self.risk.buying_power, "ladder": ladder,
            "rest_minutes": params.get("rest_minutes"), "drop": params.get("drop"),
            "cost_calibration": self.meta["cost_calibration"],
        }  # fmt: skip

    def snapshot(self) -> dict:
        with self._lock:
            out = {
                "mode": self.mode, "status": self.status, "error": self.error,
                "speed": self.speed, "saved": self.saved, "spec": self.spec(),
                "expected": self.expected, "holdout_start": HOLDOUT_START.isoformat(),
                "live": {"available": False,
                         "reason": "The live data feed is not connected yet. Replay a past "
                                   "session to see the book work."},
                "session": None,
            }  # fmt: skip
            if self.session is not None:
                out["session"] = session_view(self.session)
            return out

    # -- finished sessions -----------------------------------------------------------------
    def _save(self, session: Session) -> str:
        folder = paper_dir(self.settings) / self.mode
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        name = f"{session.day.isoformat()}_{stamp}"
        payload = {
            "schema": "paper-session-1", "id": name, "mode": self.mode,
            "saved_at": datetime.now(UTC).isoformat(timespec="seconds"), "spec": self.spec(),
            "data_build_id": DataStore(self.settings).build_id, **session_view(session, full=True),
        }  # fmt: skip
        registry.write_json(folder / f"{name}.json", payload)
        return name

    def sessions(self) -> list[dict]:
        """Finished sessions, newest first, without their details."""
        out = []
        for path in sorted(paper_dir(self.settings).glob("*/*.json"), reverse=True):
            try:
                data = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
            out.append({k: data.get(k) for k in ("id", "mode", "day", "saved_at", "summary")})
        return sorted(out, key=lambda s: s["saved_at"] or "", reverse=True)

    def saved_session(self, name: str) -> dict | None:
        for path in paper_dir(self.settings).glob(f"*/{Path(name).name}.json"):
            return json.loads(path.read_text())
        return None

    def suggested_days(self, count: int = 12) -> dict:
        """Past sessions worth replaying: the busiest days of the candidate's validation run."""
        out = {"first": "2003-09-10", "last": None, "days": []}
        if not self.expected:
            return out
        run = self.settings.runs_dir / self.expected["run_id"]
        table = pq.read_table(run / "trades.parquet", columns=["day", "net"]).to_pydict()
        days: dict[date, list[float]] = {}
        for day, net in zip(table["day"], table["net"], strict=True):
            days.setdefault(day, []).append(net)
        busiest = sorted(days.items(), key=lambda item: (-len(item[1]), item[0]))[:count]
        out["days"] = [{"day": d.isoformat(), "trades": len(n), "net": sum(n)} for d, n in busiest]
        out["first"], out["last"] = self.expected["period"]["start"], self.expected["period"]["end"]
        return out


def _ladders(session: Session, limit: int | None) -> list[dict]:
    by_symbol: dict[str, list[Rung]] = {}
    for rung in session.rungs:
        by_symbol.setdefault(rung.symbol, []).append(rung)
    rows = []
    for symbol, rungs in by_symbol.items():
        rungs.sort(key=lambda r: -(r.signal.limit_price or 0.0))
        first = rungs[0]
        held = sum(r.held for r in rungs)
        filled = sum(r.filled for r in rungs)
        value = sum(r.entry_value for r in rungs)
        last = session.last_price(symbol)
        working = any(r.status == "working" for r in rungs)
        refused = all(r.status == "refused" for r in rungs)
        net = sum(r.trade.net for r in rungs if r.trade) if session.finished and filled else None
        state = (
            "refused" if refused else "working" if working else "holding" if held > 0
            else "closed" if filled else "cancelled" if any(r.status == "cancelled" for r in rungs)
            else "expired"
        )  # fmt: skip
        rows.append({
            "symbol": symbol, "state": state, "signal_minute": first.signal.minute,
            "signal_clock": clock(first.signal.minute), "expires": first.last_entry,
            "expires_clock": clock(first.last_entry + 1), "event_price": first.event_price,
            "prev_close": first.prev_close, "marketcap": first.marketcap, "last": last,
            "drop": (first.event_price / first.prev_close - 1)
            if first.event_price and first.prev_close else None,
            "held": held, "filled": filled, "avg_price": value / filled if filled else None,
            "invested": value,
            "marked": (held * last - value * held / filled) if held and last and filled else None,
            "net": net, "note": first.note,
            "rungs": [
                {"tag": r.signal.tag, "limit": r.signal.limit_price, "quantity": r.quantity,
                 "filled": r.filled, "status": r.status,
                 "below": 1 - r.signal.limit_price / first.event_price
                 if first.event_price and r.signal.limit_price else None}
                for r in rungs
            ],
        })  # fmt: skip
    order = {"working": 0, "holding": 1, "closed": 2, "cancelled": 3, "expired": 4, "refused": 5}
    rows.sort(key=lambda r: (order[r["state"]], -r["signal_minute"], r["symbol"]))
    return rows if limit is None else rows[:limit]


def session_view(session: Session, *, full: bool = False) -> dict:
    """A session as plain data: the live snapshot, or (``full``) the record that is saved."""
    rungs = session.rungs
    placed = [r for r in rungs if r.status != "refused"]
    trades = session.trades
    notional = sum(t.notional for t in trades)
    summary = {
        "signals": session.signals, "orders": len(placed),
        "refused": len(rungs) - len(placed),
        "working": sum(r.status == "working" for r in rungs),
        "holding": len({r.symbol for r in rungs if r.held > 0}),
        "filled_orders": sum(r.filled > 0 for r in rungs),
        "expired": sum(r.status == "expired" for r in rungs),
        "trades": len(trades),
        "marked": session.marked_pnl(),
        "net": sum(t.net for t in trades) if session.finished else None,
        "net_2x": sum(t.net_2x for t in trades) if session.finished else None,
        "net_per_trade": (sum(t.net / t.notional for t in trades) / len(trades))
        if trades else None,
        "winners": sum(t.net > 0 for t in trades) if session.finished else None,
        "invested": notional if session.finished else sum(r.entry_value for r in rungs),
        "in_use": session.capital_in_use() if not session.finished else 0.0,
    }  # fmt: skip
    events = session.events
    if not full:  # the screen gets every fill and control, and the latest of the routine rest
        routine = [e for e in events if e["kind"] not in MAIN_EVENTS][-TAPE_ROWS:]
        keep = {id(e) for e in routine}
        events = [e for e in events if e["kind"] in MAIN_EVENTS or id(e) in keep]
    out = {
        "day": session.day.isoformat(), "minute": session.minute, "clock": clock(session.minute),
        "open_minute": session.open_minute, "close_minute": session.close_minute,
        "halted": session.halted, "finished": session.finished, "summary": summary,
        "ladders": _ladders(session, None if full else LADDER_ROWS),
        "ladders_total": len({r.symbol for r in rungs}),
        "tape": [{**e, "clock": clock(e["minute"])} for e in reversed(events)],
        "curve": [[m, round(v, 2)] for m, v in session.curve],
    }  # fmt: skip
    if full:
        out["trades"] = [
            {"symbol": t.symbol, "tag": t.tag, "quantity": t.quantity,
             "entry_minute": t.entry_minute, "entry_price": t.entry_price,
             "exit_price": t.exit_price, "notional": t.notional, "gross": t.gross,
             "costs": t.commission + t.fees + t.slippage, "net": t.net, "net_2x": t.net_2x}
            for t in trades
        ]  # fmt: skip
    return out


def sleep_until_done(trader: Trader, poll: float = 0.05) -> None:
    while trader.status in ("loading", "running", "halted"):
        time.sleep(poll)
