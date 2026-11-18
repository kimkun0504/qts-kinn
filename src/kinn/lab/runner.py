"""One Lab run, start to finish, in the worker process. Progress and results go to the run's
folder; the Workbench reads them from there."""

from __future__ import annotations

import json
import time
import traceback
from collections.abc import Callable
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
from kinn.lab.settings import PERIODS, SettingsError, parse

COST_MODEL = "ibkr_pro_tiered"


def _period_label(settings) -> str:
    if settings.period == "custom":
        first, last = settings.window()
        return f"{first} to {last}"
    return PERIODS[settings.period][2]


def run(run_dir: Path, open_store: Callable[[], DataStore] | None = None) -> None:
    """``open_store`` is for tests; the worker reads the sealed store of this checkout."""
    started = time.time()
    request = json.loads((run_dir / "request.json").read_text())
    code = (run_dir / "algorithm.py").read_text()

    def progress(stage: str, share: float) -> None:
        store.set_status(run_dir, "running", stage=stage, progress=round(min(max(share, 0), 1), 3))

    try:
        progress("Reading your algorithm", 0.01)
        algorithm = alg.load(code)
        settings = parse(request.get("settings"), algorithm.settings)
        data_store = open_store() if open_store else DataStore(load_settings())
        data = LabData(data_store, settings, progress)

        progress("Running your algorithm", 0.36)
        entries, exits = alg.signals(algorithm, data, settings.entry.mode)
        trial = 1 + sum(1 for r in store.list_runs(run_dir.parent.parent, request["algorithm"])
                        if r["trial"] and r["run_id"] != run_dir.name)  # fmt: skip
        store.set_status(run_dir, "running", signals_computed=True, trial_number=trial)

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
        trades = simulate(
            market, entries, exits, settings, Costs(load_costs(COST_MODEL)), data.first_row,
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
        summary.update(
            period_label=_period_label(settings), settings=settings.to_dict(),
            signals=int(np.count_nonzero(np.isfinite(window) if window.dtype != bool else window)),
            universe_stocks=int(len(data.columns)),
            sessions=int(data.last_signal_row - data.first_row + 2),
            trial_number=trial, cost_model=COST_MODEL, has_exit_signal=algorithm.has_exit,
            seconds=round(time.time() - started, 1),
        )  # fmt: skip
        capital = summary.get("capital") or settings.book.position_size
        store._write(run_dir / "summary.json", summary)
        store._write(run_dir / "lookahead.json", look)
        (run_dir / "by_year.json").write_text(
            json.dumps(metrics.by_year(table, daily, data.sessions))
        )
        (run_dir / "by_stock.json").write_text(json.dumps(metrics.by_stock(table)))
        (run_dir / "equity.json").write_text(
            json.dumps(metrics.equity(daily, data.sessions, spy, data.first_row, capital))
        )
        manifest = json.loads((run_dir / "manifest.json").read_text())
        manifest.update(
            settings=settings.to_dict(), data_build_id=data._store.build_id,
            finished_at=datetime.now(UTC).isoformat(),
        )  # fmt: skip
        store._write(run_dir / "manifest.json", manifest)
        store.set_status(run_dir, "complete", stage="Done", progress=1.0,
                         seconds=round(time.time() - started, 1))  # fmt: skip
    except (alg.AlgorithmError, SettingsError, DataError) as error:
        store.set_status(run_dir, "failed", stage="Stopped", error=str(error))
    except MemoryError:
        store.set_status(run_dir, "failed", stage="Stopped",
                         error="The run ran out of memory. Use a shorter period, a narrower "
                               "universe or fewer fields.")  # fmt: skip
    except Exception:  # noqa: BLE001 - a bug in the Lab: report it whole
        trace = traceback.format_exc()
        store.set_status(run_dir, "failed", stage="Stopped",
                         error="The Lab failed (not your code):\n" + trace)  # fmt: skip
