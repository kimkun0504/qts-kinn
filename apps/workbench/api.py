"""Read the run store for the Workbench. Pure functions over ``runs/<run_id>/`` files.

The Workbench reads only what runs wrote, in their versioned schemas. It never imports strategy
code and never touches market data.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from kinn.registry import runs as registry
from kinn.validation import stats

KNOWN_SCHEMAS = {"manifest": {"manifest-1"}, "metrics": {"metrics-1"}, "study": {"study-1"}}
MAX_POINTS = 700


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _flat(value, prefix="") -> dict:
    if not isinstance(value, dict):
        return {prefix: value}
    out = {}
    for key, inner in value.items():
        out.update(_flat(inner, f"{prefix}.{key}" if prefix else key))
    return out


def list_runs(runs_dir: Path) -> list[dict]:
    """One row per run, newest first, with headline numbers and its parameters."""
    rows = []
    for manifest in registry.read_manifests(runs_dir):
        run_dir = runs_dir / manifest["run_id"]
        kind = manifest.get("kind", "backtest")
        row = {
            "run_id": manifest["run_id"], "strategy": manifest["strategy"],
            "family": manifest.get("family"), "config": manifest["config"], "kind": kind,
            "agent": manifest["agent"], "branch": manifest["git"]["branch"],
            "commit": manifest["git"]["commit"][:8], "dirty": manifest["git"]["dirty"],
            "scratch": manifest["scratch"], "status": manifest["status"],
            "started_at": manifest["started_at"], "period": manifest["period"],
            "data_build_id": manifest["data_build_id"],
            "params": _flat(manifest.get("resolved_config", {})),
            "schema_ok": manifest.get("schema") in KNOWN_SCHEMAS["manifest"],
        }  # fmt: skip
        if kind == "event_study":
            study = _load(run_dir / "study.json") or {}
            close = study.get("curve", {}).get("r_close", {})
            row.update(
                trades=study.get("events"),
                net_1x=close.get("net_1x", {}).get("mean"),
                net_2x=close.get("net_2x", {}).get("mean"),
                gross=close.get("gross", {}).get("mean"), sharpe=None, total_net=None,
                t_stat_2x=None,
            )  # fmt: skip
        elif kind == "tick_study":
            tick = (_load(run_dir / "tick_study.json") or {}).get("all", {})
            strict = tick.get("strict", {}).get("net_per_fill", {})
            row.update(
                trades=strict.get("n"), net_1x=strict.get("mean"), net_2x=None, gross=None,
                sharpe=None, total_net=None, t_stat_2x=None,
            )  # fmt: skip
        elif kind == "book":
            # A book has no round trips: its headline is the return a year, and "trades" are fills.
            m = _load(run_dir / "metrics.json") or {}
            one, two = m.get("slippage_1x", {}), m.get("slippage_2x", {})
            row.update(
                trades=m.get("fills", _rows(run_dir / "fills.parquet")),
                net_1x=one.get("annual_return"),
                net_2x=two.get("annual_return"), gross=None, sharpe=one.get("sharpe"),
                total_net=one.get("total_net"), t_stat_2x=two.get("t_stat_daily"),
            )  # fmt: skip
        else:
            m = _load(run_dir / "metrics.json") or {}
            one, two = m.get("slippage_1x", {}), m.get("slippage_2x", {})
            row.update(
                trades=m.get("trades"), net_1x=one.get("mean_return"),
                net_2x=two.get("mean_return"), gross=m.get("gross_mean_return"),
                sharpe=one.get("sharpe"), total_net=one.get("total_net"),
                t_stat_2x=two.get("t_stat_daily"),
            )  # fmt: skip
        rows.append(row)
    return sorted(rows, key=lambda r: r["started_at"], reverse=True)


def _rows(path: Path) -> int | None:
    return pq.read_metadata(path).num_rows if path.exists() else None


def _thin(n: int) -> list[int]:
    step = max(1, n // MAX_POINTS)
    index = list(range(0, n, step))
    if index and index[-1] != n - 1:
        index.append(n - 1)
    return index


def run_detail(runs_dir: Path, run_id: str) -> dict | None:
    run_dir = runs_dir / run_id
    manifest = _load(run_dir / "manifest.json")
    if manifest is None or run_dir.resolve().parent != runs_dir.resolve():
        return None
    manifest = {k: v for k, v in manifest.items() if k != "sessions"}
    out: dict = {"manifest": manifest}
    if manifest.get("kind") == "event_study":
        out["study"] = _load(run_dir / "study.json")
        return out
    if manifest.get("kind") == "tick_study":
        out["tick_study"] = _load(run_dir / "tick_study.json")
        return out
    out["metrics"] = _load(run_dir / "metrics.json")
    if (run_dir / "equity.parquet").exists():
        equity = pq.read_table(run_dir / "equity.parquet").to_pydict()
        index = _thin(len(equity["date"]))
        out["equity"] = {
            "date": [str(equity["date"][i]) for i in index],
            "cum_net": [equity["cum_net"][i] for i in index],
            "cum_net_2x": [equity["cum_net_2x"][i] for i in index],
        }
    if manifest.get("kind") == "book":
        out.update(_book_detail(run_dir))
    if (run_dir / "trades.parquet").exists():
        trades = pq.read_table(run_dir / "trades.parquet", columns=["net", "notional"]).to_pydict()
        returns = np.array(trades["net"]) / np.array(trades["notional"]) if trades["net"] else []
        if len(returns) >= 5:
            low, high = np.percentile(returns, [1, 99])
            if high > low:
                counts, edges = np.histogram(np.clip(returns, low, high), bins=40)
                out["histogram"] = {"counts": counts.tolist(), "edges": edges.tolist()}
    return out


def _book_detail(run_dir: Path) -> dict:
    """Exposure through time and the latest holdings of a multi-day book."""
    out: dict = {}
    if (run_dir / "daily.parquet").exists():
        columns = ["date", "equity", "long_value", "short_value", "n_long", "n_short"]
        daily = pq.read_table(
            run_dir / "daily.parquet", columns=[*columns, "pnl", "pnl_2x"]
        ).to_pydict()
        index = _thin(len(daily["date"]))
        net, net_2x = np.cumsum(daily["pnl"]), np.cumsum(daily["pnl_2x"])
        out["equity"] = {
            "date": [str(daily["date"][i]) for i in index],
            "cum_net": [float(net[i]) for i in index],
            "cum_net_2x": [float(net_2x[i]) for i in index],
        }
        out["fills"] = _rows(run_dir / "fills.parquet")
        out["exposure"] = {
            k: [str(daily[k][i]) if k == "date" else daily[k][i] for i in index] for k in columns
        }
    if (run_dir / "positions.parquet").exists():
        positions = pq.read_table(run_dir / "positions.parquet").to_pylist()
        if positions:
            last = max(p["date"] for p in positions)
            held = sorted(
                (p for p in positions if p["date"] == last), key=lambda p: -abs(p["weight"])
            )
            out["positions"] = {
                "date": str(last),
                "rows": [{k: v for k, v in p.items() if k != "date"} for p in held[:60]],
                "count": len(held),
            }
    return out


def _daily_net(run_dir: Path) -> tuple[list, np.ndarray] | None:
    path = run_dir / "equity.parquet"
    if path.exists():
        table = pq.read_table(path, columns=["date", "net"]).to_pydict()
        return table["date"], np.array(table["net"], dtype=float)
    book = run_dir / "daily.parquet"  # a book run from before it wrote equity.parquet
    if book.exists():
        table = pq.read_table(book, columns=["date", "pnl"]).to_pydict()
        return table["date"], np.array(table["pnl"], dtype=float)
    return None


def families(runs_dir: Path) -> list[dict]:
    """Trial counts per family, and what they do to the best result."""
    manifests = registry.read_manifests(runs_dir)
    out = []
    for family in sorted({m.get("family") or m["strategy"] for m in manifests}):
        members = [m for m in manifests if (m.get("family") or m["strategy"]) == family]
        counted = [m for m in members if registry.counts_as_trial(m)]
        prior = max((int(m.get("prior_trials", 0)) for m in members), default=0)
        trials = len(counted) + prior
        row = {
            "family": family, "runs": len(members), "counted": len(counted),
            "scratch": sum(1 for m in members if m["scratch"]),
            "abandoned": sum(1 for m in members if m.get("status") == "abandoned"),
            "prior_trials": prior, "trials": trials,
            "by_agent": {}, "overfitting": None,
        }  # fmt: skip
        for m in counted:
            row["by_agent"][m["agent"]] = row["by_agent"].get(m["agent"], 0) + 1
        series = {}
        for m in counted:
            if m.get("kind", "backtest") in ("backtest", "book") and m["status"] == "complete":
                daily = _daily_net(runs_dir / m["run_id"])
                if daily is not None and len(daily[1]) > 20:
                    series[m["run_id"]] = daily
        if series:
            sharpes = {k: stats.sharpe(v[1]) for k, v in series.items()}
            best = max(sharpes, key=sharpes.get)
            variance = float(np.var(list(sharpes.values()), ddof=1)) if len(sharpes) > 1 else 0.0
            over = {
                "backtests": len(series), "best_run": best,
                "best_sharpe_annual": sharpes[best] * np.sqrt(252),
                "trial_sharpe_variance": variance,
                "expected_max_sharpe_annual": stats.expected_max_sharpe(trials, variance)
                * np.sqrt(252),
                "deflated_sharpe": stats.deflated_sharpe(
                    series[best][1], trials=trials, trial_sharpe_variance=variance
                ),
                "probabilistic_sharpe": stats.probabilistic_sharpe(series[best][1]),
                "pbo": None,
                "sharpes": {k: v * np.sqrt(252) for k, v in sharpes.items()},
            }  # fmt: skip
            same = [v for v in series.values() if v[0] == series[best][0]]
            if len(same) >= 2 and len(series[best][0]) >= 24:
                over["pbo"] = stats.pbo(np.column_stack([v[1] for v in same]), blocks=8)
                over["pbo"]["trials_compared"] = len(same)
            row["overfitting"] = over
        out.append(row)
    return json.loads(json.dumps(out, default=float))
