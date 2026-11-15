"""A study on the quote sample, recorded in the run store so it counts as a trial.

Used for questions the minute simulator cannot answer (was a resting order filled?). The
definition lives in the strategy's HYPOTHESIS.md; this module only measures it.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from kinn.core.settings import Settings
from kinn.costs import model as cost_model
from kinn.data import quotes
from kinn.registry import runs as registry
from kinn.run import REPO_ROOT, strategies_dir
from kinn.validation.stats import bootstrap_mean_ci


def _stat(values: np.ndarray, days: np.ndarray) -> dict:
    if len(values) == 0:
        return {"n": 0, "mean": None, "low": None, "high": None}
    if len(np.unique(days)) < 3:
        return {"n": len(values), "mean": float(values.mean()), "low": None, "high": None}
    low, high = bootstrap_mean_ci(values, groups=days, draws=4000)
    return {"n": len(values), "mean": float(values.mean()), "low": low, "high": high}


def passive_entry(
    settings: Settings, *, strategy: str, source_run: str, position_dollars: float = 500.0,
    scratch: bool = False, agent: str | None = None, repo: Path = REPO_ROOT,
) -> Path:  # fmt: skip
    """Measure the passive-entry hypothesis on the quote sample of ``source_run``."""
    meta = yaml.safe_load((strategies_dir() / strategy / "strategy.yaml").read_text())
    costs = cost_model.load(meta["cost_calibration"])
    git = registry.git_state(repo)
    registry.check_clean(git, scratch=scratch)
    plan_dir = settings.data_dir / "quotes_sample" / source_run
    raw_dir = settings.raw_dir / "massive" / "quotes_sample" / source_run
    windows = quotes.read_windows(plan_dir / "windows.csv")
    orders = quotes.passive_orders(windows, raw_dir)
    events = pq.read_table(
        settings.runs_dir / source_run / "events.parquet",
        columns=["day", "symbol", "entry_price", "r_close"],
    ).to_pylist()
    close = {(e["day"], e["symbol"]): e["entry_price"] * (1 + e["r_close"]) for e in events}

    for o in orders:
        final = close[(o["day"], o["symbol"])]
        o["close"] = final
        for name, price, passive in (("passive", o["bid"], True), ("market", o["ask"], False)):
            shares = int(position_dollars / price)
            if shares <= 0:
                o[f"net_{name}"] = None
                continue
            value_in, value_out = shares * price, shares * final
            c_in, f_in = costs.order_fees(
                side="buy", value=value_in, marketable=0 if passive else shares,
                passive=shares if passive else 0, auction=0,
            )  # fmt: skip
            c_out, f_out = costs.order_fees(
                side="sell", value=value_out, marketable=0, passive=0, auction=shares
            )
            slip = costs.auction_slippage(price=final, shares=shares)
            o[f"net_{name}"] = (
                value_out - value_in - c_in - f_in - c_out - f_out - slip
            ) / value_in
            o[f"gross_{name}"] = final / price - 1

    def summary(subset: list[dict]) -> dict:
        subset = [o for o in subset if o["net_passive"] is not None]
        days = np.array([o["day"].toordinal() for o in subset])
        out = {"orders": len(subset)}
        for rule in ("strict", "lenient"):
            filled = np.array([o[f"filled_{rule}"] for o in subset], dtype=bool)
            net = np.array([o["net_passive"] for o in subset], dtype=float)
            out[rule] = {
                "fill_rate": float(filled.mean()) if len(subset) else None,
                "net_per_fill": _stat(net[filled], days[filled]),
                "net_per_order": _stat(np.where(filled, net, 0.0), days),
                "gross_per_fill": float(np.mean([o["gross_passive"] for o, f in
                                                 zip(subset, filled, strict=True) if f]))
                if filled.any() else None,
                "net_unfilled_if_bought_at_bid": float(net[~filled].mean())
                if (~filled).any() else None,
            }  # fmt: skip
        market = np.array([o["net_market"] for o in subset], dtype=float)
        out["market_at_ask"] = _stat(market, days)
        return out

    result = {"schema": "tick-study-1", "definition": "passive_entry", "all": summary(orders),
              "by_bucket": {b[0]: summary([o for o in orders if o["bucket"] == b[0]])
                            for b in quotes.BUCKETS},
              "by_period": {p[0]: summary([o for o in orders if o["period"] == p[0]])
                            for p in quotes.PERIODS},
              "windows": len(windows), "with_quotes_and_trades": len(orders)}  # fmt: skip

    agent = agent or os.environ.get("KINN_AGENT", "human")
    short = registry.config_hash({"meta": meta, "source": source_run, "commit": git["commit"]})
    run_id = registry.new_run_id(agent, strategy, short)
    run_dir = settings.runs_dir / run_id
    run_dir.mkdir(parents=True)
    now = datetime.now(UTC).isoformat(timespec="seconds")
    days = sorted(o["day"] for o in orders)
    manifest = {
        "schema": registry.MANIFEST_SCHEMA, "run_id": run_id, "kind": "tick_study",
        "strategy": strategy, "family": meta.get("family", strategy),
        "prior_trials": int(meta.get("prior_trials", 0)), "config": "passive_entry",
        "config_hash": short,
        "resolved_config": {"source_run": source_run, "position_dollars": position_dollars,
                            "rest_minutes": quotes.MINUTES_AFTER_ENTRY},
        "cost_calibration": meta["cost_calibration"], "git": git, "scratch": scratch,
        "agent": agent, "data_build_id": "quote-sample:" + source_run,
        "period": {"start": str(days[0]), "end": str(days[-1])},
        "started_at": now, "finished_at": now, "status": "complete",
    }  # fmt: skip
    registry.write_json(run_dir / "manifest.json", manifest)
    registry.write_json(run_dir / "tick_study.json", result)
    pq.write_table(pa.Table.from_pylist(orders), run_dir / "orders.parquet")
    (run_dir / "tick_study.md").write_text(render(result, run_id))
    return run_dir


def _p(v) -> str:
    return "–" if v is None else f"{100 * v:+.2f}%".replace("-", "−")


def _ci(s: dict) -> str:
    if s["mean"] is None:
        return "–"
    return (
        _p(s["mean"])
        if s["low"] is None
        else f"{_p(s['mean'])} ({_p(s['low'])} to {_p(s['high'])})"
    )


def render(result: dict, run_id: str) -> str:
    head = (
        "| | Orders | Fill rate | Net per fill (95% interval) | Net per order placed | "
        "If the unfilled had been bought at the bid | Market order at the ask |\n"
        "|---|---|---|---|---|---|---|"
    )

    def row(label: str, s: dict, rule: str) -> str:
        r = s[rule]
        rate = "–" if r["fill_rate"] is None else f"{100 * r['fill_rate']:.0f}%"
        return (
            f"| {label} | {s['orders']} | {rate} ({r['net_per_fill']['n']}) | "
            f"{_ci(r['net_per_fill'])} | {_ci(r['net_per_order'])} | "
            f"{_p(r['net_unfilled_if_bought_at_bid'])} | {_ci(s['market_at_ask'])} |"
        )

    lines = [
        "# Passive entry on the quote sample",
        "",
        f"`{run_id}`. {result['windows']} events; "
        f"{result['with_quotes_and_trades']} with a quote before the entry.",
        "",
    ]
    for rule, title in (
        ("strict", "Strict fill rule: a trade strictly below the limit"),
        ("lenient", "Lenient fill rule: a trade at or below the limit"),
    ):
        lines += [f"## {title}", "", head, row("All", result["all"], rule)]
        lines += [row(k, s, rule) for k, s in result["by_bucket"].items()]
        lines += [row(k, s, rule) for k, s in result["by_period"].items()]
        lines.append("")
    return "\n".join(lines)
