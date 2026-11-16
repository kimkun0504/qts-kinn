"""Swing runs: an earnings-drift rule on daily bars, run as a book of fixed-size positions.

The rule (strategies/earnings_drift): a company in a market-value band reports earnings; if by
the close of the session after the 8-K its two-day return and volume clear the thresholds, the
book buys at the next open and sells at the close ``hold`` sessions after the signal day. A
position needs a free slot at the open; when several signals arrive together the one with the
most volume against normal goes first.

Every read goes through :class:`~kinn.data.store.DataStore`, so the same code runs on the
research build and, with ``unseal=True`` and the owner's token, on the unsealed build. A trade
is booked on its exit day. Slippage at 1x is an allowance for joining the opening and closing
auctions (``costs.allowance_bps`` in the config); 2x doubles it. The result with the quoted
spread crossed instead is reported beside them.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from kinn.core.settings import Settings, load_settings
from kinn.core.types import Trade
from kinn.costs import model as cost_model
from kinn.costs.model import CostModel
from kinn.data.store import DataStore
from kinn.registry import runs as registry
from kinn.reporting import metrics as metrics_module
from kinn.reporting import tearsheet

REPO_ROOT = Path(__file__).resolve().parents[2]
OPEN_MINUTE, CLOSE_MINUTE = 570, 960
# A stock back from a halt longer than this has no "two-day return": its last close is stale.
MAX_GAP_DAYS = 7
PANEL_COLUMNS = (
    "date, permaticker, symbol, category, open, low, close, prev_close, prev_date, "
    "dollar_volume, adv20_prev, marketcap_prev"
)
TRADE_FIELDS = [f for f in Trade.__dataclass_fields__]
# The tear sheet's counts (shared with intraday runs), then this module's own.
COUNT_KEYS = (
    "signals",
    "rejected_capital",  # no free slot at the open
    "rejected_size",  # one share costs more than a position
    "unfilled",
    "lookahead_checks",
    "rejected_risk",
    "paused_sessions",
    "open_at_end",  # the data ends before the hold does
    "forced_exits",  # the stock stopped trading during the hold
)


@dataclass(frozen=True)
class Rule:
    jump: float  # two-day return by the signal day's close
    volume: float  # the larger of the two days' dollar volume, as a multiple of normal
    cap_min: float
    cap_max: float
    hold: int  # sessions from the signal day to the exit
    min_close: float = 1.0
    min_adv: float = 250_000.0


@dataclass(frozen=True)
class Signal:
    day: date
    permaticker: int
    symbol: str
    volume: float
    adv: float
    dates: tuple[date, ...]  # the sessions held, entry day first
    returns: tuple[float, ...]  # log return of each: open to close, then close to close
    entry_price: float
    complete: bool  # every session of the hold exists
    forced: bool  # the stock stopped trading before the hold ended


def strategies_dir() -> Path:
    return Path(os.environ.get("KINN_STRATEGIES_DIR") or REPO_ROOT / "strategies")


def load_config(name: str, config: str) -> tuple[dict, dict]:
    folder = strategies_dir() / name
    meta = yaml.safe_load((folder / "strategy.yaml").read_text())
    cfg = yaml.safe_load((folder / "configs" / f"{config}.yaml").read_text()) or {}
    return meta, cfg


def find_signals(
    panel: pa.Table, events: pa.Table, rule: Rule, start: date, end: date, last_session: date
) -> list[Signal]:
    """Signals read at a close in [start, end], each with the sessions it would be held.

    ``panel`` must reach back two sessions before ``start`` and forward past the holds.
    ``last_session`` is the last session the data has: a hold cut short there is incomplete,
    one cut short earlier belongs to a stock that stopped trading.
    """
    con = duckdb.connect()
    con.register("panel", panel)
    con.register("events", events)
    rows = con.execute(
        f"""with p as (
                select *, ln(close / prev_close) as lr,
                       dollar_volume / nullif(adv20_prev, 0) as dvr,
                       row_number() over (partition by permaticker order by date) as rn
                from panel
                where prev_close > 0 and close > 0 and low > 0 and open > 0
                  and category like '%Common Stock%'),
            q as (select *, lag(lr) over w as lr_prev, lag(dvr) over w as dvr_prev
                  from p window w as (partition by permaticker order by date)),
            e as (select distinct permaticker, date from events
                  where regexp_matches('|' || eventcodes || '|', '[|]22[|]')),
            s as (select q.permaticker, q.symbol, q.date as day, q.rn, q.adv20_prev as adv,
                         greatest(q.dvr, q.dvr_prev) as volume
                  from q
                  where q.date between ? and ? and q.close >= ? and q.adv20_prev >= ?
                    and date_diff('day', q.prev_date, q.date) <= {MAX_GAP_DAYS}
                    and q.marketcap_prev >= ? and q.marketcap_prev < ?
                    and exp(q.lr + q.lr_prev) - 1 >= ? and greatest(q.dvr, q.dvr_prev) >= ?
                    and exists (select 1 from e where e.permaticker = q.permaticker
                                and e.date >= q.prev_date and e.date < q.date))
            select s.day, s.permaticker, s.symbol, s.volume, s.adv, p.date, p.open,
                   case when p.rn = s.rn + 1 then ln(p.close / p.open) else p.lr end as r
            from s join p on p.permaticker = s.permaticker
                         and p.rn between s.rn + 1 and s.rn + {int(rule.hold)}
            order by s.day, s.symbol, p.date""",
        [start, end, rule.min_close, rule.min_adv, rule.cap_min, rule.cap_max, rule.jump,
         rule.volume],
    ).fetchall()  # fmt: skip
    grouped: dict[tuple, list] = {}
    for day, permaticker, symbol, volume, adv, session, opened, r in rows:
        grouped.setdefault((day, permaticker, symbol, volume, adv), []).append((session, opened, r))
    found = []
    for (day, permaticker, symbol, volume, adv), path in grouped.items():
        complete = len(path) == rule.hold
        found.append(
            Signal(
                day=day,
                permaticker=int(permaticker),
                symbol=symbol,
                volume=float(volume),
                adv=float(adv),
                dates=tuple(p[0] for p in path),
                returns=tuple(float(p[2]) for p in path),
                entry_price=float(path[0][1]),
                complete=complete,
                forced=not complete and path[-1][0] < last_session,
            )  # fmt: skip
        )
    return found


def allowance(table: list[list[float]], adv: float) -> float:
    """The auction allowance a side, as a fraction, for a stock's normal dollar volume."""
    return next(bps for floor, bps in table if adv >= floor) / 1e4


def simulate(
    signals: list[Signal], *, account: float, slots: int, costs: CostModel,
    allowance_bps: list[list[float]], spread_bps: list[list[float]],
) -> tuple[list[Trade], dict[str, int], dict]:  # fmt: skip
    """Run the book. Returns the trades taken, counts, and extra figures for the report."""
    size = account / slots
    counts = dict.fromkeys(COUNT_KEYS, 0)
    counts["signals"] = len(signals)
    by_entry: dict[date, list[Signal]] = {}
    for s in signals:
        if not s.complete and not s.forced:
            counts["open_at_end"] += 1  # the data ends before the hold does: not a trade
            continue
        by_entry.setdefault(s.dates[0], []).append(s)
    open_until: list[date] = []
    trades: list[Trade] = []
    marked: dict[date, float] = {}
    crossed, auction_returns = [], []
    for day in sorted(by_entry):
        open_until = [last for last in open_until if last >= day]
        for s in sorted(by_entry[day], key=lambda s: (-s.volume, s.symbol)):
            quantity = int(size // s.entry_price)
            if len(open_until) >= slots or quantity <= 0:
                counts["rejected_capital" if quantity > 0 else "rejected_size"] += 1
                continue
            open_until.append(s.dates[-1])
            notional = quantity * s.entry_price
            growth = math.exp(sum(s.returns))
            exit_value = notional * growth
            buy = costs.order_fees(side="buy", value=notional, marketable=0, passive=0,
                                   auction=quantity)  # fmt: skip
            sell = costs.order_fees(side="sell", value=exit_value, marketable=0, passive=0,
                                    auction=quantity)  # fmt: skip
            a = allowance(allowance_bps, s.adv)
            slippage = a * notional + (costs.forced_exit_bps / 1e4 if s.forced else a) * exit_value
            gross = exit_value - notional
            commission, fees = buy[0] + sell[0], buy[1] + sell[1]
            net = gross - commission - fees - slippage
            counts["forced_exits"] += int(s.forced)
            trades.append(
                Trade(
                    day=s.dates[-1],
                    symbol=s.symbol,
                    permaticker=s.permaticker,
                    quantity=quantity,
                    signal_minute=CLOSE_MINUTE,
                    entry_minute=OPEN_MINUTE,
                    entry_price=s.entry_price,
                    exit_minute=CLOSE_MINUTE,
                    exit_price=s.entry_price * growth,
                    exit_reason="forced" if s.forced else "time",
                    notional=notional,
                    gross=gross,
                    commission=commission,
                    fees=fees,
                    slippage=slippage,
                    net=net,
                    net_2x=net - slippage,
                    tag=f"signal {s.day.isoformat()}",
                )  # fmt: skip
            )
            auction_returns.append(net / notional)
            spread = allowance(spread_bps, s.adv)
            crossed.append(
                (gross - commission - fees - spread * (notional + exit_value)) / notional
            )
            # Marked to market at each close, with each side's costs on the day it is paid.
            value = notional
            marked[s.dates[0]] = marked.get(s.dates[0], 0.0) - a * notional - buy[0] - buy[1]
            for session, r in zip(s.dates, s.returns, strict=True):
                moved = value * (math.exp(r) - 1)
                marked[session] = marked.get(session, 0.0) + moved
                value += moved
            marked[s.dates[-1]] -= slippage - a * notional + sell[0] + sell[1]
    extra = {"spread_crossed_mean_return": float(np.mean(crossed)) if crossed else None}
    if len(marked) > 1:
        days = sorted(marked)
        pnl = np.array([marked[d] for d in days])
        curve = np.cumsum(pnl)
        extra["marked_to_market"] = {
            "total_net": float(curve[-1]),
            "max_drawdown": float((curve - np.maximum.accumulate(np.maximum(curve, 0))).min()),
            "sessions_with_positions": len(days),
        }
    return trades, counts, extra


def run(
    name: str,
    config: str,
    *,
    settings: Settings | None = None,
    scratch: bool = False,
    unseal: bool = False,
    agent: str | None = None,
    repo: Path = REPO_ROOT,
) -> Path:
    """One swing run, start to finish. Refuses uncommitted code unless ``scratch``.

    ``unseal=True`` runs on the owner's unsealed build: the one run on the holdout. It needs
    the owner's token, and every read of a holdout date is logged.
    """
    settings = settings or load_settings()
    meta, cfg = load_config(name, config)
    git = registry.git_state(repo)
    registry.check_clean(git, scratch=scratch)
    store = DataStore(settings, unseal=unseal)
    start = date.fromisoformat(str(cfg["period"]["start"]))
    end = date.fromisoformat(str(cfg["period"]["end"]))
    sessions = store.sessions(start, end)  # raises if the period reaches the holdout
    rule = Rule(**{k: float(v) if k != "hold" else int(v) for k, v in cfg["rule"].items()})
    costs = cost_model.load(meta["cost_calibration"])
    agent = agent or os.environ.get("KINN_AGENT", "human")
    short = registry.config_hash(
        {"config": cfg, "commit": git["commit"], "build": store.build_id, "kind": "swing"}
    )
    run_id = registry.new_run_id(agent, name, short)
    run_dir = settings.runs_dir / run_id
    run_dir.mkdir(parents=True)
    manifest = {
        "schema": registry.MANIFEST_SCHEMA, "run_id": run_id, "kind": "swing", "strategy": name,
        "family": meta.get("family", name), "prior_trials": int(meta.get("prior_trials", 0)),
        "config": config, "config_hash": short, "resolved_config": cfg,
        "cost_calibration": meta["cost_calibration"], "git": git, "scratch": scratch,
        "agent": agent, "data_build_id": store.build_id, "bars_id": store.info["bars_id"],
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "sessions": [d.isoformat() for d in sessions],
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"), "finished_at": None,
        "status": "running", "schemas": {"metrics": registry.METRICS_SCHEMA},
    }  # fmt: skip
    if unseal:
        manifest["unsealed"] = True
    registry.write_json(run_dir / "manifest.json", manifest)

    signals: list[Signal] = []
    for year in range(start.year, end.year + 1):  # a year at a time, to bound memory
        first, last = max(start, date(year, 1, 1)), min(end, date(year, 12, 31))
        if first > last:
            continue
        ahead = min(end, last + timedelta(days=5 * rule.hold + 30))
        panel = store.panel(first - timedelta(days=14), ahead, columns=PANEL_COLUMNS)
        events = store.events(first - timedelta(days=14), last)
        signals += find_signals(panel, events, rule, first, last, sessions[-1])
    trades, counts, extra = simulate(
        signals, account=float(cfg["book"]["account"]), slots=int(cfg["book"]["slots"]),
        costs=costs, allowance_bps=cfg["costs"]["allowance_bps"],
        spread_bps=cfg["costs"]["spread_bps"],
    )  # fmt: skip
    trades.sort(key=lambda t: (t.day, t.symbol))
    pq.write_table(
        pa.table({f: [getattr(t, f) for t in trades] for f in TRADE_FIELDS}),
        run_dir / "trades.parquet",
    )
    pq.write_table(
        pa.table(metrics_module.daily_table(trades, sessions)), run_dir / "equity.parquet"
    )
    summary = metrics_module.summarize(
        trades, sessions, equity=float(cfg["book"]["account"]), counts=counts
    )
    summary.update(schema=registry.METRICS_SCHEMA, swing=extra)
    registry.write_json(run_dir / "metrics.json", summary)
    manifest["status"] = "complete"
    manifest["finished_at"] = datetime.now(UTC).isoformat(timespec="seconds")
    registry.write_json(run_dir / "manifest.json", manifest)
    tearsheet.write(run_dir)
    return run_dir


def headline(run_dir: Path) -> str:
    m = json.loads((run_dir / "metrics.json").read_text())
    one, two = m["slippage_1x"], m["slippage_2x"]
    crossed = m["swing"]["spread_crossed_mean_return"]

    def pct(v):
        return "n/a" if v is None else f"{100 * v:.2f}%"

    return (
        f"{m['trades']} trades ({m['counts']['signals']} signals, "
        f"{m['counts']['rejected_capital']} without a free slot, "
        f"{m['counts']['open_at_end']} still open at the end). A trade: auction allowance "
        f"{pct(one['mean_return'])}, allowance doubled {pct(two['mean_return'])}, spread "
        f"crossed {pct(crossed)}. Total ${one['total_net']:,.0f} "
        f"(doubled ${two['total_net']:,.0f})."
    )
