# Intraday volume surge

**Verdict: park.** Buying an extreme regular-session rise after turnover reached its usual
full-day level earned **−1.18% at 1× slippage and −1.65% at 2×** per event through the close.
The sample gate passed with 571 events on 472 sessions. The 2× confidence interval was
entirely negative, and 2× net averaged −2.20% in 2003–2009 and −1.20% in 2010–2016.
The [preregistered](HYPOTHESIS.md) gate required a mean of at least +1.00% at 2×, a positive
lower confidence bound and positive results in both halves. The portfolio backtest and
validation remain unopened.

Run `20261116T012352Z_gpt_intraday_volume_surge_9a2e5bc8` used the 2003-09-10 to
2016-12-30 development period, build `6453bd3ec8` and clean commit `f2cc6b40`. The
hypothesis was committed at `9aaf78c` before the run. This is one charged trial in the
`intraday_volume_surge` family. The Workbench shows the study and session-clustered intervals.
Replay passed on all 472 signal sessions.

## Development results

| Close outcome | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net return per event | −1.18% | −1.65% |
| 95% day-clustered interval | −2.01% to −0.33% | −2.47% to −0.79% |
| Summed event P&L | −$13,474 | −$18,786 |
| Daily event P&L t-statistic | −2.70 | −3.73 |
| Worst end-of-day drawdown of summed event P&L | −$13,517 | −$18,786 |

The mean was −0.54% gross through the close and the mean 1× round-trip cost was 0.64%.
The net result was negative at every horizon printed by the same study. The preregistered
close horizon determined the verdict. The largest positive session, 2015-11-24, contributed
+$2,092 at 2× on one event. With that session removed, the mean was −1.84% at 2×.

Dollar statistics multiply the stored net return by the trade's hypothetical whole-share
notional at the $2,000 target and sum by date. The daily series includes all 3,352 development
sessions. Overlapping events ignore the $20,000 account budget and participation constraints.
These drawdowns describe the unconstrained event series. Simulated portfolio trades and
account drawdown remain unmeasured.

## Annual development results

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 3 | −3.61% | −3.91% | −$215 | −$234 |
| 2004 | 29 | −2.64% | −3.13% | −$1,529 | −$1,811 |
| 2005 | 20 | +2.91% | +2.42% | +$1,157 | +$962 |
| 2006 | 15 | −0.93% | −1.48% | −$276 | −$442 |
| 2007 | 28 | −2.75% | −3.22% | −$1,538 | −$1,797 |
| 2008 | 90 | −2.13% | −2.62% | −$3,826 | −$4,702 |
| 2009 | 73 | −1.80% | −2.27% | −$2,628 | −$3,300 |
| 2010 | 19 | −0.36% | −0.83% | −$133 | −$313 |
| 2011 | 32 | −1.16% | −1.59% | −$740 | −$1,012 |
| 2012 | 20 | −1.95% | −2.41% | −$779 | −$963 |
| 2013 | 38 | +0.04% | −0.44% | +$35 | −$327 |
| 2014 | 46 | +0.61% | +0.19% | +$554 | +$166 |
| 2015 | 70 | +0.83% | +0.35% | +$1,162 | +$489 |
| 2016 | 88 | −2.69% | −3.14% | −$4,717 | −$5,502 |

## Execution and interpretation

All study entries fell within the signal's intended expiry window. About 19% exceeded
the portfolio engine's entry-bar participation ceiling at the target size. Costs use
entry-bar data for both sides and real market fills remain unverified. The upper end of
the gross 95% interval was +0.31%, well below the target before any execution costs.
The hypothesis would be more credible with direct evidence of persistent buy pressure
after the signal, such as independently time-stamped order imbalance.
