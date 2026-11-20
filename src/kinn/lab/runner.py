"""One Lab run, start to finish, in the worker process. Progress and results go to the run's
folder; the Workbench reads them from there.

The run's log (``log.txt``) gets one line a stage, with the time; ``summary.json`` keeps how long
each stage took. A run that passes its time limit stops with a message rather than running on.
"""

from __future__ import annotations

import contextlib
import json
import signal
import sys
import time
import traceback
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from kinn.core.settings import load_settings
from kinn.costs.model import load as load_costs
from kinn.data.store import DataStore
from kinn.lab import algorithm as alg
from kinn.lab import book, metrics, store
from kinn.lab.data import DataError, LabData
from kinn.lab.engine import Costs, Market, simulate
from kinn.lab.settings import PERIODS, SettingsError, parse, sweep_settings

COST_MODEL = "ibkr_pro_tiered"
SUMMARY_SCHEMA = "lab-summary-1"


class RunTimeout(BaseException):  # noqa: N818 - a BaseException, so the owner's code cannot catch it
    """The run passed its time limit. Not an ``Exception``: the code's own ``except
    Exception`` cannot swallow it."""


@contextlib.contextmanager
def _time_limit(seconds: float | None) -> Iterator[None]:
    """Raise :class:`RunTimeout` after ``seconds`` of wall time (main thread, POSIX only)."""
    if not seconds or not hasattr(signal, "setitimer"):
        yield
        return

    def stop(signum, frame):
        raise RunTimeout

    previous = signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _period_label(settings) -> str:
    if settings.period == "custom":
        first, last = settings.window()
        return f"{first} to {last}"
    return PERIODS[settings.period][2]


class _Stages:
    """Progress for the page, a line a stage for the log, and the time each stage took."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.started = time.time()
        self.current: str | None = None
        self.since = self.started
        self.timings: dict[str, float] = {}

    @staticmethod
    def _key(stage: str) -> str:
        """The stage a timing is filed under: "Loading prices for 2014" is "Loading prices"."""
        head, _, tail = stage.rpartition(" for ")
        return head if head and tail.isdigit() else stage

    def __call__(self, stage: str, share: float) -> None:
        if stage != self.current:
            now = time.time()
            if self.current:
                key = self._key(self.current)
                self.timings[key] = round(self.timings.get(key, 0) + now - self.since, 2)
            self.current, self.since = stage, now
            self.log(stage)
        share = round(min(max(share, 0), 1), 3)
        store.set_status(self.run_dir, "running", stage=stage, progress=share)

    def log(self, text: str) -> None:
        """A line in the run's log.txt, with the time (UTC)."""
        stamp = datetime.now(UTC).strftime("%H:%M:%S")
        with contextlib.suppress(OSError), open(self.run_dir / "log.txt", "a") as log:
            log.write(f"{stamp} {text}\n")

    def finish(self) -> dict[str, float]:
        self("Done", 1.0)
        return self.timings

    @property
    def seconds(self) -> float:
        return round(time.time() - self.started, 1)


def run(run_dir: Path, open_store: Callable[[], DataStore] | None = None,
        time_limit: float | None = None) -> None:  # fmt: skip
    """``open_store`` is for tests; the worker reads the sealed store of this checkout.
    ``time_limit`` is in seconds of wall time."""
    request = json.loads((run_dir / "request.json").read_text())
    code = (run_dir / "algorithm.py").read_text()
    package = run_dir / "pkg"
    if package.is_dir():  # the library, as it was when the run was made: import lab.<module>
        sys.path.insert(0, str(package))
    progress = _Stages(run_dir)
    try:
        with _time_limit(time_limit):
            _run(run_dir, request, code, open_store, progress)
    except RunTimeout:
        minutes = (time_limit or 0) / 60
        store.set_status(run_dir, "failed", stage="Stopped",
                         error=f"The run passed its time limit of {minutes:g} minutes and was "
                               "stopped. Use a shorter period or a narrower universe, or look "
                               "for a slow loop in the code.")  # fmt: skip
    except (alg.AlgorithmError, SettingsError, DataError) as error:
        store.set_status(run_dir, "failed", stage="Stopped", error=str(error))
    except MemoryError:
        store.set_status(run_dir, "failed", stage="Stopped",
                         error="The run ran out of memory. Use a shorter period, a narrower "
                               "universe or fewer fields.")  # fmt: skip
    except Exception:  # noqa: BLE001 - a bug in the Lab: report it whole
        trace = traceback.format_exc()
        progress.log("The Lab failed:\n" + trace)
        store.set_status(run_dir, "failed", stage="Stopped",
                         error="The Lab failed (not your code):\n" + trace)  # fmt: skip
    finally:
        with contextlib.suppress(ValueError):
            sys.path.remove(str(package))
        for name in [m for m in sys.modules if m == "lab" or m.startswith("lab.")]:
            del sys.modules[name]  # a later run in this process reads its own library


SWEEP_FIELDS = ("trades", "mean_net", "mean_net_2x", "win_rate", "t_weekly", "book_profit",
                "sharpe", "max_drawdown", "annual_return", "average_positions", "years_positive",
                "years")  # fmt: skip


def _setting(settings, field: str):
    section, key = field.split(".")
    return getattr(getattr(settings, section), key)


def _run(run_dir: Path, request: dict, code: str, open_store, progress: _Stages) -> None:
    progress("Reading your algorithm", 0.01)
    algorithm = alg.load(code)
    settings = parse(request.get("settings"), algorithm.settings)
    sweep = request.get("sweep")
    variants = sweep_settings(request.get("settings"), algorithm.settings, sweep)
    longest = max([settings, *(v for _, v in variants)], key=lambda s: s.exit.hold_days)
    data_store = open_store() if open_store else DataStore(load_settings())
    data = LabData(data_store, longest, progress, cache_dir=run_dir.parent.parent / "cache")

    progress("Running your algorithm", 0.36)
    entries, exits = alg.signals(algorithm, data, settings.entry.mode)
    base_value = _setting(settings, sweep["field"]) if variants else None
    tried = any(v == base_value for v, _ in variants)
    trials = len(variants) + (0 if tried else 1) if variants else 1
    earlier = store.list_runs(run_dir.parent.parent, request["algorithm"])
    trial = 1 + sum(r["trials"] for r in earlier if r["run_id"] != run_dir.name)
    store.set_status(run_dir, "running", signals_computed=True, trial_number=trial, trials=trials)

    progress("Checking your code for lookahead", 0.5)
    look = alg.lookahead(algorithm, data, settings.entry.mode, entries, exits)

    progress("Simulating trades", 0.65)
    market = Market(
        open=data.array("open"), high=data.array("high"), low=data.array("low"),
        close=data.array("close"), adj_close=data.array("adj_close"),
        eligible=data.array("eligible"), adv=data.array("adv20"),
        dollar_volume=data.array("dollar_volume"),
        universe_return=data.array("universe_return"),
        universe_intraday=data.array("universe_intraday"),
    )  # fmt: skip
    costs = Costs(load_costs(COST_MODEL))
    trades = simulate(
        market, entries, exits, settings, costs, data.first_row,
        data.last_signal_row,
        progress=lambda share: progress("Simulating trades", 0.65 + 0.2 * share),
    )  # fmt: skip

    progress("Building the book", 0.86)
    taken = book.select(trades, settings.book.max_positions)
    daily = book.daily(trades, taken, market)
    spy = data.array("spy")

    progress("Summarising", 0.92)
    static = {key: data._static[key].tolist() for key in ("name", "sector")}
    table = metrics.trades_table(trades, taken, data.sessions, list(data.columns), static)
    table.to_parquet(run_dir / "trades.parquet", index=False)
    summary = metrics.summary(table, daily, data.sessions, data.first_row, settings, spy, look)
    window = entries[data.first_row : data.last_signal_row + 1]
    timings = progress.finish()
    summary.update(
        schema=SUMMARY_SCHEMA, period_label=_period_label(settings), settings=settings.to_dict(),
        signals=int(np.count_nonzero(np.isfinite(window) if window.dtype != bool else window)),
        universe_stocks=int(len(data.columns)),
        tickers_not_found=getattr(data, "not_found", []),
        sessions=int(data.last_signal_row - data.first_row + 2),
        trial_number=trial, trials=trials,
        sweep={"field": sweep["field"], "values": len(variants)} if variants else None,
        cost_model=COST_MODEL, has_exit_signal=algorithm.has_exit,
        seconds=progress.seconds, timings=timings, cache=getattr(data, "cache_state", None),
    )  # fmt: skip
    capital = summary.get("capital") or settings.book.position_size
    store._write(run_dir / "summary.json", summary)
    store._write(run_dir / "lookahead.json", look)
    (run_dir / "by_year.json").write_text(json.dumps(metrics.by_year(table, daily, data.sessions)))
    (run_dir / "by_stock.json").write_text(json.dumps(metrics.by_stock(table)))
    curve = metrics.equity(daily, data.sessions, spy, data.first_row, capital,
                           settings.book.position_size)  # fmt: skip
    (run_dir / "equity.json").write_text(json.dumps(curve))
    path = metrics.signal_path(trades, market.adj_close, market.universe_cum,
                               settings.exit.hold_days)  # fmt: skip
    if path:
        (run_dir / "path.json").write_text(json.dumps(path))
    if variants:
        rows = []
        for k, (value, variant) in enumerate(variants):
            progress(f"Sweep: {sweep['field']} = {value}", 0.9 + 0.06 * k / len(variants))
            v_trades = simulate(market, entries, exits, variant, costs, data.first_row,
                                data.last_signal_row)  # fmt: skip
            v_taken = book.select(v_trades, variant.book.max_positions)
            v_daily = book.daily(v_trades, v_taken, market)
            v_table = metrics.trades_table(v_trades, v_taken, data.sessions, list(data.columns),
                                           static)  # fmt: skip
            v_summary = metrics.summary(v_table, v_daily, data.sessions, data.first_row, variant,
                                        spy, look)  # fmt: skip
            rows.append({"value": value, **{f: v_summary.get(f) for f in SWEEP_FIELDS}})
        store._write(run_dir / "sweep.json", {"field": sweep["field"], "base": base_value,
                                              "rows": rows})  # fmt: skip
    if settings.entry.mode == "rank":
        progress("Measuring the ranking", 0.96)
        factor = metrics.factor_report(entries, market, data.sessions, data.first_row,
                                       data.last_signal_row, settings.exit.hold_days,
                                       settings.entry.rank_order)  # fmt: skip
        if factor:
            (run_dir / "factor.json").write_text(json.dumps(factor))
    manifest = json.loads((run_dir / "manifest.json").read_text())
    manifest.update(
        settings=settings.to_dict(), data_build_id=data._store.build_id,
        finished_at=datetime.now(UTC).isoformat(),
    )  # fmt: skip
    store._write(run_dir / "manifest.json", manifest)
    store.set_status(run_dir, "complete", stage="Done", progress=1.0, seconds=progress.seconds)
