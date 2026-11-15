"""Event study: what happens after a strategy's signals, by minutes held.

Each signal is treated as an event. The entry is the engine's own rule for a market order (the
open of the first regular-session bar after the signal bar). Forward returns are measured from
that entry to each horizon, capped at the official close, gross and net of the platform cost
model for a fixed-dollar position. Nothing is optimised here.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pyarrow as pa

from kinn.core.types import Signal
from kinn.costs.model import CostModel
from kinn.engine.intraday.data import SymbolDay
from kinn.validation.stats import bootstrap_mean_ci

HORIZONS = (1, 2, 3, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240)
RETURN_COLUMNS = [f"r_{h}" for h in HORIZONS] + ["r_close"]
SCHEMA = pa.schema(
    [("day", pa.date32()), ("symbol", pa.string()), ("permaticker", pa.int64()),
     ("signal_minute", pa.int32()), ("entry_minute", pa.int32()), ("entry_price", pa.float64()),
     ("prev_close", pa.float64()), ("adv20_prev", pa.float64()),
     ("marketcap_prev", pa.float64()), ("entry_bar_volume", pa.int64()),
     ("shares", pa.int32()), ("fees", pa.float64()), ("slippage", pa.float64())]
    + [(c, pa.float64()) for c in RETURN_COLUMNS]
)  # fmt: skip


def measure(
    day: date,
    sd: SymbolDay,
    signal: Signal,
    *,
    open_minute: int,
    close_minute: int,
    official_close: float | None,
    costs: CostModel,
    position_dollars: float,
    no_entry_before_close: int = 10,
) -> dict | None:
    """One event's row, or None if no entry was possible."""
    start = max(signal.minute + 1, open_minute)
    i = int(np.searchsorted(sd.minute, start, side="left"))
    end = int(np.searchsorted(sd.minute, close_minute, side="left"))
    if i >= end or sd.minute[i] > close_minute - no_entry_before_close - 1:
        return None
    entry_minute, entry = int(sd.minute[i]), float(sd.open[i])
    shares = int(position_dollars / entry)
    if shares <= 0 or entry <= 0:
        return None
    last = float(sd.close[end - 1])
    final = official_close if official_close is not None else last
    row = {
        "day": day, "symbol": sd.symbol, "permaticker": sd.permaticker,
        "signal_minute": signal.minute, "entry_minute": entry_minute, "entry_price": entry,
        "prev_close": sd.prior.get("prev_close"), "adv20_prev": sd.prior.get("adv20_prev"),
        "marketcap_prev": sd.prior.get("marketcap_prev"), "entry_bar_volume": int(sd.volume[i]),
        "shares": shares,
    }  # fmt: skip
    for horizon in HORIZONS:
        target = entry_minute + horizon - 1  # the bar that ends `horizon` minutes after entry
        if target >= close_minute - 1:
            price = final
        else:
            j = int(np.searchsorted(sd.minute, target, side="right")) - 1
            price = float(sd.close[max(j, i)])
        row[f"r_{horizon}"] = price / entry - 1
    row["r_close"] = final / entry - 1
    # Round-trip cost of a market order in and a market order out, as fractions of notional.
    value = shares * entry
    adv = sd.prior.get("adv20_prev")
    one_way = costs.marketable_slippage(
        price=entry, shares=shares, adv=adv, bar_high=float(sd.high[i]),
        bar_low=float(sd.low[i]), bar_volume=int(sd.volume[i]),
    )  # fmt: skip
    commission = fees = 0.0
    for side in ("buy", "sell"):
        c, f = costs.order_fees(side=side, value=value, marketable=shares, passive=0, auction=0)
        commission, fees = commission + c, fees + f
    row["fees"] = (commission + fees) / value
    row["slippage"] = 2 * one_way / value
    return row


def _stats(values: np.ndarray, days: np.ndarray) -> dict:
    if len(values) == 0:
        return {"n": 0, "mean": None, "low": None, "high": None}
    if len(np.unique(days)) < 2:
        return {"n": len(values), "mean": float(values.mean()), "low": None, "high": None}
    low, high = bootstrap_mean_ci(values, groups=days, draws=2000)
    return {"n": len(values), "mean": float(values.mean()), "low": low, "high": high}


def _three(table: dict[str, np.ndarray], column: str, mask: np.ndarray) -> dict:
    gross = table[column][mask]
    cost1 = (table["fees"] + table["slippage"])[mask]
    cost2 = (table["fees"] + 2 * table["slippage"])[mask]
    days = table["day"][mask]
    return {
        "gross": _stats(gross, days),
        "net_1x": _stats(gross - cost1, days),
        "net_2x": _stats(gross - cost2, days),
    }


def summarize(events: pa.Table) -> dict:
    """Curves and pre-declared splits from the events table."""
    table = {name: np.asarray(events[name].to_pylist()) for name in events.column_names}
    n = events.num_rows
    everything = np.ones(n, dtype=bool)
    out: dict = {"events": n, "horizons": list(HORIZONS)}
    if n == 0:
        return out
    years = np.array([d.year for d in table["day"]])
    adv = table["adv20_prev"].astype(float)
    minute = table["signal_minute"]
    out["sessions_with_events"] = len(np.unique(table["day"]))
    out["curve"] = {c: _three(table, c, everything) for c in RETURN_COLUMNS}
    out["mean_cost"] = {
        "fees": float(table["fees"].mean()),
        "slippage_1x": float(table["slippage"].mean()),
        "median_round_trip_1x": float(np.median(table["fees"] + table["slippage"])),
    }
    out["median_entry_price"] = float(np.median(table["entry_price"]))
    out["median_adv"] = float(np.median(adv))
    out["capacity_limited_share"] = float(
        (table["shares"] > 0.05 * table["entry_bar_volume"]).mean()
    )
    splits = {
        "by_period": {"2003–2016": years <= 2016, "2017–2023": years >= 2017,
                      "2020–2023": years >= 2020},
        "by_liquidity": {"ADV under $1M": adv < 1e6, "ADV $1–10M": (adv >= 1e6) & (adv < 1e7),
                         "ADV $10M and over": adv >= 1e7},
        "by_time": {"before 11:00": minute < 660, "11:00–13:00": (minute >= 660) & (minute < 780),
                    "after 13:00": minute >= 780},
        "by_year": {str(y): years == y for y in sorted(set(years.tolist()))},
    }  # fmt: skip
    for name, groups in splits.items():
        out[name] = {
            label: {"r_close": _three(table, "r_close", mask), "r_60": _three(table, "r_60", mask)}
            for label, mask in groups.items()
        }
    return out
