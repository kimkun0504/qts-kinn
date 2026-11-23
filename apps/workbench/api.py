"""Read the run store for the Workbench. Pure functions over ``runs/<run_id>/`` files.

The Workbench reads only what runs wrote, in their versioned schemas. It never imports strategy
code and never touches market data.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import yaml

from kinn.lab import store as lab_store
from kinn.registry import runs as registry
from kinn.validation import stats, targets

KNOWN_SCHEMAS = {"manifest": {"manifest-1"}, "metrics": {"metrics-1"}, "study": {"study-1"}}
MAX_POINTS = 700
OUT_OF_SAMPLE = ("validation", "holdout")  # the periods a run is judged against the targets on


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


def _phase(manifest: dict) -> str | None:
    """Development, validation or full sample, from the run's period."""
    try:
        period = manifest["period"]
        return targets.phase(date.fromisoformat(period["start"]), date.fromisoformat(period["end"]))
    except (KeyError, TypeError, ValueError):
        return None


def _fill_checks(runs_dir: Path, manifests: list[dict]) -> dict[str, dict]:
    """For each run a finished fill check covers: the latest check and whether it passed."""
    found: dict[str, dict] = {}
    for manifest in manifests:  # oldest first, so a later check replaces an earlier one
        if manifest.get("kind") != "fill_check" or manifest["status"] != "complete":
            continue
        if manifest["scratch"]:
            continue
        result = _load(runs_dir / manifest["run_id"] / "fill_check.json") or {}
        passed = bool(result.get("verdict", {}).get("passed"))
        for source in manifest.get("resolved_config", {}).get("source_runs", {}):
            found[source] = {"run_id": manifest["run_id"], "passed": passed}
    return found


def _targets(metrics: dict, fill_check: dict | None) -> dict:
    """The owner's four targets for one out-of-sample backtest."""
    items = targets.check(metrics)
    fills = (
        "not checked" if fill_check is None else "confirmed" if fill_check["passed"] else "failed"
    )
    met = sum(item["met"] for item in items) + (fills == "confirmed")
    return {
        "items": items, "fills": fills,
        "fills_run": fill_check["run_id"] if fill_check else None,
        "met": met, "of": len(items) + 1, "all_met": met == len(items) + 1,
    }  # fmt: skip


def list_runs(runs_dir: Path) -> list[dict]:
    """One row per run, newest first, with headline numbers and its parameters."""
    rows = []
    manifests = registry.read_manifests(runs_dir)
    fill_checks = _fill_checks(runs_dir, manifests)
    for manifest in manifests:
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
            "phase": _phase(manifest), "targets": None, "sharpe_2x": None, "drawdown_2x": None,
            "total_net_2x": None, "fill_check_passed": None,
        }  # fmt: skip
        if kind == "fill_check":
            check = _load(run_dir / "fill_check.json") or {}
            verdict = check.get("verdict", {})
            row.update(
                trades=check.get("all_traded", {}).get("orders"), net_1x=None,
                net_2x=verdict.get("validation_net_per_trade_2x"), gross=None, sharpe=None,
                total_net=None, t_stat_2x=None,
                fill_check_passed=verdict.get("passed") if check else None, phase="full",
            )  # fmt: skip
        elif kind == "event_study":
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
                t_stat_2x=two.get("t_stat_daily"), sharpe_2x=two.get("sharpe"),
                drawdown_2x=two.get("max_drawdown"), total_net_2x=two.get("total_net"),
            )  # fmt: skip
            # Targets are judged out of sample only: a development result is a search result.
            if two and manifest["status"] == "complete" and row["phase"] in OUT_OF_SAMPLE:
                row["targets"] = _targets(m, fill_checks.get(manifest["run_id"]))
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
    if manifest.get("kind") == "fill_check":
        out["fill_check"] = _load(run_dir / "fill_check.json")
        return out
    out["metrics"] = _load(run_dir / "metrics.json")
    out["phase"] = _phase(manifest)
    if (
        manifest.get("kind", "backtest") == "backtest"
        and out["metrics"]
        and manifest["status"] == "complete"
        and out["phase"] in OUT_OF_SAMPLE
    ):
        checks = _fill_checks(runs_dir, registry.read_manifests(runs_dir))
        out["targets"] = _targets(out["metrics"], checks.get(run_id))
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


LAB_PREFIX = "lab:"


def _lab_daily(lab_dir: Path, run_id: str) -> tuple[list, np.ndarray] | None:
    """A Lab run's book profit by session: its full daily file, or the drawn curve of a run
    made before it wrote one."""
    try:
        run_dir = lab_store.run_dir_of(lab_dir, run_id)
    except lab_store.LabError:
        return None
    if (run_dir / "book.parquet").exists():
        table = pq.read_table(run_dir / "book.parquet", columns=["date", "pnl"]).to_pydict()
        return table["date"], np.array(table["pnl"], dtype=float)
    curve = _load(run_dir / "equity.json")
    if not curve or not curve.get("dates"):
        return None
    profit = np.array([v if v is not None else np.nan for v in curve["profit"]], dtype=float)
    profit = np.nan_to_num(profit, nan=0.0)
    return curve["dates"], np.diff(np.concatenate([[0.0], profit]))


def _lab_label(lab_dir: Path, run_id: str) -> dict:
    run_dir = lab_store.run_dir_of(lab_dir, run_id)
    manifest = _load(run_dir / "manifest.json") or {}
    summary = _load(run_dir / "summary.json") or {}
    return {"algorithm": manifest.get("algorithm"), "period": summary.get("period_label"),
            "daily": (run_dir / "book.parquet").exists()}  # fmt: skip


MAX_COMPARED = 4
WEEK = 5  # sessions


def _stats(pnl: np.ndarray) -> dict:
    cum = np.cumsum(pnl)
    peak = np.maximum.accumulate(np.concatenate([[0.0], cum]))[1:]
    spread = float(np.std(pnl, ddof=1)) if len(pnl) > 1 else 0.0
    return {
        "total": float(cum[-1]) if len(cum) else 0.0,
        "sharpe": float(np.mean(pnl) / spread * np.sqrt(252)) if spread > 0 else None,
        "worst_drawdown": float((cum - peak).min()) if len(cum) else 0.0,
    }


def compare(runs_dir: Path, ids: list[str], lab_dir: Path | None = None) -> dict:
    """Backtests and Lab runs (``lab:<run id>``) side by side on one calendar: each run's
    cumulative net profit over every session any of them covers, how their weekly profit moves
    together over the sessions all of them cover, and what they make together at their own
    sizes."""
    found: list[tuple[str, dict[str, float]]] = []
    labels: dict[str, dict] = {}
    for run_id in ids[:MAX_COMPARED]:
        if run_id.startswith(LAB_PREFIX):
            daily = _lab_daily(lab_dir, run_id[len(LAB_PREFIX) :]) if lab_dir else None
            if daily:
                labels[run_id] = _lab_label(lab_dir, run_id[len(LAB_PREFIX) :])
        else:
            run_dir = runs_dir / run_id
            if not run_id or run_dir.resolve().parent != runs_dir.resolve():
                continue
            daily = _daily_net(run_dir)
        if daily:
            dates, net = daily
            found.append((run_id, {str(d)[:10]: float(v) for d, v in zip(dates, net, strict=True)}))
    if not found:
        return {"runs": [], "dates": [], "curves": [], "together": None, "overlap": None}
    dates = sorted(set().union(*(set(by) for _, by in found)))
    pnl = np.array([[by.get(d, 0.0) for d in dates] for _, by in found])
    index = _thin(len(dates))
    curves = np.cumsum(pnl, axis=1)
    out: dict = {
        "runs": [
            {"run_id": run_id, "start": min(by), "end": max(by), "lab": labels.get(run_id)}
            for run_id, by in found
        ],  # fmt: skip
        "dates": [dates[i] for i in index],
        "curves": [[round(float(v), 2) for v in curve[index]] for curve in curves],
        "together": [round(float(v), 2) for v in curves.sum(axis=0)[index]],
        "overlap": None,
    }
    start, end = max(r["start"] for r in out["runs"]), min(r["end"] for r in out["runs"])
    shared = [i for i, d in enumerate(dates) if start <= d <= end]
    if len(found) < 2 or len(shared) < 2 * WEEK:
        return out
    common = pnl[:, shared]
    weeks = len(shared) // WEEK
    weekly = common[:, len(shared) - weeks * WEEK :].reshape(len(found), weeks, WEEK).sum(axis=2)
    with np.errstate(invalid="ignore", divide="ignore"):
        matrix = np.corrcoef(weekly)
    out["overlap"] = {
        "start": start, "end": end, "sessions": len(shared), "weeks": weeks,
        "correlation": [[None if not np.isfinite(v) else round(float(v), 3) for v in row]
                        for row in np.atleast_2d(matrix)],
        "alone": [_stats(row) for row in common],
        "together": _stats(common.sum(axis=0)),
    }  # fmt: skip
    return out


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


def strategies(runs_dir: Path, strategies_dir: Path) -> list[dict]:
    """One row per strategy: what its ``strategy.yaml`` says (status, owner, candidate config)
    and how its candidate did out of sample. Reads the yaml files only, never strategy code."""
    rows = [r for r in list_runs(runs_dir) if r["status"] == "complete" and not r["scratch"]]
    declared = {}
    for path in sorted(strategies_dir.glob("*/strategy.yaml")):
        if not path.parent.name.startswith("_"):
            try:
                declared[path.parent.name] = yaml.safe_load(path.read_text()) or {}
            except yaml.YAMLError:
                declared[path.parent.name] = {}
    out = []
    for name in sorted(set(declared) | {r["strategy"] for r in rows}):
        meta = declared.get(name, {})
        mine = [r for r in rows if r["strategy"] == name]
        config = meta.get("candidate")
        candidate = next((r for r in mine if config and r["config"] == config), None)
        validated = [r for r in mine if r["kind"] == "backtest" and r["phase"] in OUT_OF_SAMPLE]
        status = str(meta.get("status") or "unknown")
        out.append({
            "strategy": name, "status": status, "state": "candidate" if candidate else status,
            "owner": meta.get("owner"), "family": meta.get("family") or name, "runs": len(mine),
            "candidate_config": config, "candidate_run": candidate,
            "validation_run": candidate or (validated[0] if validated else None),
            "ready_for_paper": bool(candidate and (candidate["targets"] or {}).get("all_met")),
        })  # fmt: skip
    order = {"candidate": 0, "developing": 1}
    out.sort(key=lambda r: (order.get(r["state"], 2), r["strategy"]))
    return json.loads(json.dumps(out, default=float))
