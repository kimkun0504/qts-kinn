"""Preview, not the registered check: the ladder's rung fills against the ticks already
downloaded for x_o4's order windows (same event windows; about 94% of the ladder's events).
Same definitions as kinn.fill_check. Starts no run."""

from __future__ import annotations

import glob
import json

import pyarrow.parquet as pq

from kinn import fill_check
from kinn.core.settings import load_settings
from kinn.costs import model as cost_model

RUNS = {"development": "3d866b2f", "validation": "437947d4"}


def main() -> None:
    s = load_settings()
    raw = s.raw_dir / "massive" / "quotes_sample" / "fillcheck_x_o4"
    costs = cost_model.load("ibkr_pro_tiered")
    ineligible, source = fill_check.ineligible_conditions(raw)
    print("conditions:", source)
    for label, tail in RUNS.items():
        (run_dir,) = glob.glob(f"{s.runs_dir}/*_claude_rebound_limit_{tail}")
        close_minute = None
        manifest = json.load(open(f"{run_dir}/manifest.json"))
        rest = manifest["resolved_config"]["params"]["rest_minutes"]
        rows = []
        for t in pq.read_table(f"{run_dir}/trades.parquet").to_pylist():
            order = {
                "day": t["day"], "symbol": t["symbol"], "signal_minute": t["signal_minute"],
                "live_from": t["signal_minute"] + 1, "last_entry": t["signal_minute"] + rest,
                "limit_price": t["entry_price"],
            }  # fmt: skip
            ticks = fill_check.order_ticks(order, raw, ineligible, costs.tick)
            rows.append({**t, **ticks, "bar_quantity": t["quantity"], "close": t["exit_price"],
                         "limit_price": t["entry_price"], "sim_net": t["net"],
                         "sim_net_2x": t["net_2x"], "sim_notional": t["notional"]})  # fmt: skip
        del close_minute
        for tag in ("all", "o4", "o6", "o8"):
            part = [r for r in rows if tag == "all" or r["tag"] == tag]
            x = fill_check.summarize_traded(part, costs)
            cut = x["tick_rule_5s"]
            print(
                f"{label} {tag}: rung trades {x['orders']}, with ticks {x['covered']} "
                f"({100 * x['coverage']:.0f}%), confirmed {100 * x['confirmed']:.1f}%, in full "
                f"size {100 * x['in_full_size']:.1f}%, median multiple "
                f"{x['through_volume_multiple_median']:.0f}x, simulated net/trade 2x "
                f"{100 * x['simulated']['net_per_trade_2x']:+.2f}%, real "
                f"{100 * cut['net_per_trade_2x']:+.2f}%, kept "
                f"{100 * cut['share_of_simulated_net_2x']:.0f}%, 30 s: "
                f"{100 * x['tick_rule_30s']['net_per_trade_2x']:+.2f}% kept "
                f"{100 * x['tick_rule_30s']['share_of_simulated_net_2x']:.0f}%"
            )


if __name__ == "__main__":
    main()
