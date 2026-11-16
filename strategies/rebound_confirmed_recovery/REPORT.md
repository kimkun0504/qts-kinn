# Rebound after a confirmed recovery

## Development event study

**Decision: develop.** All event-study gates in the [preregistration](HYPOTHESIS.md) passed.
Across 1,085 events on 677 sessions, the average through the close was +3.59% gross,
+2.02% net at 1× and +0.88% at 2×. The 95% day-clustered gross interval was +2.08% to
+5.29%. The 2× means were +0.59% in 2003–2009 and +1.38% in 2010–2016.

The study admitted 57 late entries. The preregistered next-bar check kept 1,028 events
on 654 sessions. It returned +3.49% gross (95% interval +1.80% to +5.16%), +1.96% at 1×
and +0.84% at 2×. Both halves remained positive at 2× (+0.51% and +1.40%).

Run `20261116T013411Z_gpt_rebound_confirmed_recovery_bb6cddbe` on 2003-09-10 through
2016-12-30 used clean commit `32d18f13` and build `6453bd3ec8`. Hypothesis commit
`77d9e62` predates the run. Replay passed on all 677 signal sessions. This decision was
committed before starting the portfolio backtest.

| Close outcome | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net return per event | +2.02% | +0.88% |
| 95% day-clustered interval | +0.56% to +3.67% | −0.53% to +2.43% |
| Summed event P&L | +$43,736 | +$18,985 |
| Daily event P&L t-statistic | +2.05 | +1.00 |
| Worst end-of-day drawdown of summed event P&L | −$3,303 | −$7,761 |

The dollar statistics use event prices, returns and whole-share quantities from the
saved run across all 3,352 development sessions. They sum overlapping events without
applying the $20,000 account budget or the per-bar volume cap. About 49% of study events
exceeded 5% of their entry bar's volume at the $2,000 target. The mean round-trip cost
was 1.57% at 1×, estimated from the entry bar for both sides. These are event estimates.
The portfolio engine applies expiry, auction costs, buying power and participation.

### Annual development event results

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 17 | −0.35% | −1.74% | −$126 | −$599 |
| 2004 | 53 | +1.78% | +0.75% | +$1,834 | +$749 |
| 2005 | 48 | −2.71% | −3.79% | −$2,590 | −$3,627 |
| 2006 | 44 | +0.16% | −0.86% | +$147 | −$752 |
| 2007 | 71 | +1.08% | −0.08% | +$1,526 | −$115 |
| 2008 | 325 | +3.36% | +2.29% | +$21,818 | +$14,830 |
| 2009 | 128 | +0.27% | −0.95% | +$680 | −$2,424 |
| 2010 | 104 | +7.99% | +6.40% | +$16,581 | +$13,283 |
| 2011 | 54 | −0.93% | −2.08% | −$1,003 | −$2,246 |
| 2012 | 38 | +1.08% | −0.05% | +$816 | −$47 |
| 2013 | 23 | +2.28% | +1.34% | +$1,045 | +$611 |
| 2014 | 46 | +1.35% | +0.26% | +$1,230 | +$232 |
| 2015 | 67 | −0.91% | −1.90% | −$1,214 | −$2,539 |
| 2016 | 67 | +2.24% | +1.22% | +$2,994 | +$1,630 |
