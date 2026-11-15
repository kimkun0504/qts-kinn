"""Run folders and the registry.

Each run is a folder ``<runs>/<run_id>/`` whose ``manifest.json`` is the source of truth. The
DuckDB index is only a cache rebuilt from the manifests, so two agents writing runs at the same
time cannot corrupt shared state. Trial counts cover every non-scratch run in a family, by any
agent, plus the prior looks a strategy declares.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import duckdb

MANIFEST_SCHEMA = "manifest-1"
TRADES_SCHEMA = "trades-1"
EQUITY_SCHEMA = "equity-1"
METRICS_SCHEMA = "metrics-1"


class DirtyTreeError(RuntimeError):
    """The code has uncommitted changes and the run was not tagged --scratch."""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def git_state(repo: Path) -> dict:
    return {
        "commit": _git(repo, "rev-parse", "HEAD"),
        "branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(_git(repo, "status", "--porcelain")),
    }


def config_hash(payload: dict) -> str:
    text = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(text.encode()).hexdigest()[:8]


def new_run_id(agent: str, strategy: str, short_hash: str, now: datetime | None = None) -> str:
    stamp = (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}_{agent}_{strategy}_{short_hash}"


def check_clean(state: dict, *, scratch: bool) -> None:
    if state["dirty"] and not scratch:
        raise DirtyTreeError(
            "the working tree has uncommitted changes. Commit first, or tag the run --scratch "
            "(scratch runs are excluded from reports and trial counts)."
        )


def write_json(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    os.replace(tmp, path)


def read_manifests(runs_dir: Path) -> list[dict]:
    manifests = []
    for path in sorted(runs_dir.glob("*/manifest.json")):
        try:
            manifests.append(json.loads(path.read_text()))
        except json.JSONDecodeError:
            continue  # a run being written right now
    return manifests


def rebuild_index(runs_dir: Path) -> Path:
    """Rebuild ``index.duckdb`` from the manifests and metrics files. Safe to run any time."""
    rows = []
    for manifest in read_manifests(runs_dir):
        metrics_path = runs_dir / manifest["run_id"] / "metrics.json"
        metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}
        one = metrics.get("slippage_1x", {})
        two = metrics.get("slippage_2x", {})
        rows.append(
            (
                manifest["run_id"], manifest["strategy"], manifest.get("family"),
                manifest["config"], manifest["config_hash"], manifest["agent"],
                manifest["git"]["branch"], manifest["git"]["commit"], manifest["git"]["dirty"],
                manifest["scratch"], manifest["status"], manifest["data_build_id"],
                manifest["started_at"], manifest.get("finished_at"),
                metrics.get("trades"), one.get("mean_return"), two.get("mean_return"),
                one.get("sharpe"), one.get("total_net"),
            )
        )  # fmt: skip
    path = runs_dir / "index.duckdb"
    tmp = runs_dir / f"index.{os.getpid()}.tmp"
    if tmp.exists():
        tmp.unlink()
    con = duckdb.connect(str(tmp))
    con.execute(
        """create table runs (run_id varchar, strategy varchar, family varchar, config varchar,
           config_hash varchar, agent varchar, branch varchar, git_commit varchar, dirty boolean,
           scratch boolean, status varchar, data_build_id varchar, started_at varchar,
           finished_at varchar, trades bigint, mean_return_1x double, mean_return_2x double,
           sharpe_1x double, total_net_1x double)"""
    )
    if rows:
        con.executemany("insert into runs values (" + ",".join("?" * 19) + ")", rows)
    con.close()
    os.replace(tmp, path)
    return path


def counts_as_trial(manifest: dict) -> bool:
    """Scratch runs and runs abandoned before producing any result are not trials."""
    return not manifest["scratch"] and manifest.get("status") != "abandoned"


def trial_count(runs_dir: Path, family: str, *, prior_trials: int = 0) -> int:
    """Trials to charge a family: every counted run by anyone, plus declared prior looks."""
    own = sum(
        1 for m in read_manifests(runs_dir) if m.get("family") == family and counts_as_trial(m)
    )
    return own + prior_trials


def abandon(runs_dir: Path, run_id: str, reason: str) -> None:
    """Mark an unfinished run as abandoned so it is not charged as a trial.

    Only a run that never produced results can be abandoned: once metrics or a study exist,
    someone may have looked, and the run stays counted for good.
    """
    run_dir = runs_dir / run_id
    manifest = json.loads((run_dir / "manifest.json").read_text())
    produced = [
        n
        for n in ("metrics.json", "study.json", "tick_study.json", "trades.parquet")
        if (run_dir / n).exists()
    ]
    if manifest["status"] == "complete" or produced:
        raise ValueError(f"{run_id} has results ({produced or 'complete'}); it stays a trial")
    manifest.update(
        status="abandoned",
        abandoned_reason=reason,
        abandoned_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
    write_json(run_dir / "manifest.json", manifest)
