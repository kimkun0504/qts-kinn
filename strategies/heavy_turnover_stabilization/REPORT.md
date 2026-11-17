# Heavy-turnover stabilization

## Verdict

Park. The strategy cleared the sample gates and the lower gross
confidence bound was positive. At the registered one-hour
horizon, mean gross return was +1.23% overall and −0.84% in
2013–2016, below the +3% minimum in both windows. The later
window also lost money at doubled slippage. According to the
preregistered rule, development stopped at the event study.

## Run

- `20261117T141057Z_gpt_heavy_turnover_stabilization_10b96f32` on 2003-09-10 through 2016-12-30.
  Hypothesis commit `8d012c5`, clean run commit `4a6b029`,
  data build `447e58e098`.
- One new trial in `intraday_rebound`. The shared family count
  rose to 94, including 9
  declared earlier looks.
- All 249 entries were on the next clock minute.
  Kinn passed 204 lookahead replays. The sample contains
  224 distinct security identifiers.

| Study window at 60 minutes | Events | Sessions with events | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 249 | 204 | +1.23% | +0.71% | +0.36% |
| 2013–2016 | 56 | 53 | −0.84% | −1.34% | −1.66% |

| Full development | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| 95% day-clustered interval for mean net | −0.34% to +1.66% | −0.69% to +1.32% |
| Daily P&L t-statistic | 1.36 | 0.70 |
| Worst end-of-day drawdown | −$1,731 | −$2,060 |
| Total modeled net P&L | +$3,517 | +$1,802 |

The 95% day-clustered interval for mean gross return was
+0.18% to +2.18%. The two cost cases use the same IBKR Pro Tiered
fees. The study marks the exit to the last observed bar close
within 60 clock minutes or to the official close if the horizon
reaches it. It estimates both
marketable legs from the entry bar. The hypothetical dollar series
sums independent simulated entries, with zero-event sessions
included across all 3,352 sessions.
About 6% of the
target order sizes exceeded 5% of entry-bar volume. The study
dollar series does not impose portfolio capacity or use the
portfolio engine's actual exit fill rules.

## Development by year at the registered horizon

| Year | Events | Net mean at 1× | Net mean at 2× | Net P&L at 1× | Net P&L at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 3 | −3.84% | −4.17% | −$229 | −$249 |
| 2004 | 11 | +1.14% | +0.80% | +$252 | +$177 |
| 2005 | 9 | +1.28% | +0.86% | +$230 | +$154 |
| 2006 | 3 | −1.10% | −1.49% | −$66 | −$89 |
| 2007 | 15 | +2.65% | +2.32% | +$794 | +$695 |
| 2008 | 88 | +1.64% | +1.30% | +$2,875 | +$2,276 |
| 2009 | 29 | +0.49% | +0.14% | +$286 | +$81 |
| 2010 | 1 | +0.78% | +0.51% | +$16 | +$10 |
| 2011 | 18 | +1.10% | +0.73% | +$396 | +$260 |
| 2012 | 16 | +1.40% | +1.05% | +$447 | +$336 |
| 2013 | 6 | +2.07% | +1.77% | +$247 | +$212 |
| 2014 | 17 | −2.68% | −2.97% | −$899 | −$997 |
| 2015 | 18 | +0.20% | −0.13% | +$72 | −$46 |
| 2016 | 15 | −3.02% | −3.40% | −$904 | −$1,017 |

## Interpretation

At doubled slippage, 2008 alone contributed
+$2,276 compared with
+$1,802 in the full study.
Excluding 2008 as a descriptive check, the stressed mean was
−0.15% across 161
events. Minute closes and volumes cannot identify who initiated
trades, so the study tests a bar pattern and cannot establish
that buyers absorbed selling pressure.

Tests cover contiguous completed bars, the two turnover
conditions, prefix replay, next-minute expiry and the one-hour
same-session exit. Kinn ran development only. The holdout
stayed sealed.
