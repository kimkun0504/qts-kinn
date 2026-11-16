# Resumption momentum

**Verdict: park.** The post-interruption continuation rule found 19 events over 19
dates. The one-hour mean was +2.06% net at 1× and +1.38% at 2×. The gross interval
included zero and neither development block met the minimum count. The next-bar-only
subset had 16 events and a +4.53% base-cost mean. This is too small to satisfy the
[registration](HYPOTHESIS.md). Portfolio and validation were not started.

Run `20261116T062746Z_gpt_resumption_momentum_c739f8ea` used clean commit `3e0bd390`,
hypothesis `58ec620`, and build `447e58e098`. One trial was charged to
`resumption_momentum`. Replay passed on all 19 signal sessions. The study ignored the
one-minute entry expiry on three events. The on-time subset's mean at 2× was +3.85%
with a 95% interval from −1.28% to +9.69%.

| Full development, one-hour study | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net return per event | +2.06% | +1.38% |
| 95% day-clustered interval | −3.10% to +7.74% | −3.76% to +6.98% |
| Summed event P&L | +$784 | +$522 |
| Daily P&L t-statistic over the full calendar | 0.75 | 0.50 |
| Worst end-of-day drawdown of summed events | −$426 | −$518 |

The gross mean was +3.08% with a 95% interval of −2.17% to +8.92%. The 2014–2015
block had 11 events and 2016 had eight. Dollar numbers use the saved event positions
across all 3,352 sessions, including zero-P&L dates before the signal's implementation
era. Study results are hypothetical and unconstrained. At this count the wide
intervals dominate any point estimate.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2014 | 4 | +6.42% | +5.66% | +$513 | +$452 |
| 2015 | 7 | +0.37% | −0.37% | +$51 | −$52 |
| 2016 | 8 | +1.37% | +0.76% | +$219 | +$122 |

A direct halt record would distinguish actual resumptions from missing prints and
could establish more reliable coverage. This result only establishes that this
particular two-bar proxy fires infrequently.
