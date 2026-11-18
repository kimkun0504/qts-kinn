"""strategies/leads_2023/HYPOTHESIS.md: each of four leads read once on 2023 (to 13 October).

    cd research/claude
    uv run python leads_2023.py
"""

from __future__ import annotations

import numpy as np

import after_hours as ah
import after_hours_score as ahs
import closing_bids as cb
import night_bids as nb
import rebalance_flows as rf


def clean(d, keep, column):
    return keep & ~np.isnan(d[column].astype(float))


def main() -> None:
    d = ah.load_short()
    keep = ah.pick(d, "after", "mid", "down15", "check", ah.SHORT_REACTIONS)
    for exit_ in ("open", "close"):
        k = clean(d, keep, f"g_{exit_}")
        print(ah.show(f"1. short mid down15 {exit_} 2023", ah.measure(d, k, exit_)) + f"  {ah.tail(d, k, exit_)}")
    d = ahs.load_limits()
    keep = clean(d, ahs.limit_cell(d, "large", "up5", "check") & d["filled"], "g_fifteen")
    print(ahs.show("2. limit large up5 fifteen 2023", ahs.measure(d, keep, "fifteen")))
    d = cb.load(2)
    keep = clean(d, nb.pick(d, "large", "check"), "g_open")
    print(cb.show("3. closing bids 2% large 2023", cb.measure(d, keep, "open")))
    rows = [r for r in rf.trades() if r[0].year == 2023]
    net = np.array([-np.sign(r[1]) * r[3] for r in rows]) - rf.COST  # own the winner: r[3] is bonds minus stocks
    print(f"4. rebalance first days 2023: {len(net)} months  net {100 * net.mean():.2f}%  "
          f"by month {' '.join(f'{100 * v:.2f}' for v in net)}")


if __name__ == "__main__":
    main()
