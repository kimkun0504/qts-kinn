# Month-end rebalancing: the right sign, too small to trade

**Verdict: closed.** 4 cells on 2010 to 2017; one met the bar and failed both tests. 6
trials. The holdout is untouched.

Each month, R is SPY's return minus TLT's (adjusted closes) from the previous month's last
close to three sessions before this month's last. Code: `research/claude/rebalance_flows.py`.

| After costs (0.06% a spread), a month | 2010–2017 | 2005–2009 | 2018–2022 |
|---|---|---|---|
| Last three sessions, own the side that lost the month (every month) | +0.40% (t 1.65) | not run | not run |
| … only when R is beyond ±3% | +0.61% (t 1.66) | not run | not run |
| **First two sessions of the next month, own the side that won** (every month) | **+0.72% (t 3.06, 7 of 8)** | +0.41% (t 1.11, 3 of 5) | +0.26% (t 0.90, 4 of 5) |
| … only when R is beyond ±3% | +0.77% (t 2.27) | not run | not run |

- **The pressure is there, with the sign the rebalancing story gives:** the side that won the
  month does worse in its last days and better in the first days of the next.
- **It is not steady enough to trade.** The first-days cell made money in both test periods,
  but on 60 months each the t is about 1, and 2019 lost 1.1% a month.
- One trade a month of half a percent or less is also a poor use of the account beside the
  earnings rule.

## Reproduce

```
cd research/claude
uv run python rebalance_flows.py funds
uv run python rebalance_flows.py measure search early late
```
