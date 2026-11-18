# Read-across: the peers of a company that jumped gain too little to trade

**Verdict: closed.** 18 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 18 trials. The holdout is untouched.

When a company jumps 15% or more on results and holds it (the earnings rule's signal without
its size cap), buy the companies in the same industry that have not reported yet, at the next
open. 23,416 such peers in the search years. Code: `research/claude/read_across.py`.

| 2010–2017 | Trades | 5 sessions | 10 sessions | 15 sessions | Over the average stock, 15 sessions |
|---|---|---|---|---|---|
| Peers of $50M–$300M | 5,566 | −0.80% | −0.51% | −0.72% | −0.06% (t 0.34) |
| Peers of $300M–$2B | 11,209 | −0.29% | +0.01% | +0.14% | +0.50% (t 2.02) |
| Peers of $2B+ | 6,641 | +0.05% | +0.21% | +0.47% | +0.76% (t 2.51) |

After costs, except the last column (before costs, against the average stock on the same
days). Taking only peers that had not yet moved changed nothing.

- **Large peers do follow**, by 0.6% to 0.8% over the average stock in three weeks. That is
  the known industry effect; it is real and too small to trade after costs.
- **Small peers do not follow at all**, which is where the earnings rule itself works. The
  slow belief is about the company that reported, and does not spread to its neighbours.

## Reproduce

```
cd research/claude
uv run python read_across.py table
uv run python read_across.py search
```
