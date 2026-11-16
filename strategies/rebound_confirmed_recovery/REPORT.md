# Rebound after a confirmed recovery

**Final verdict: park.** The confirmed entry improved base-cost mean return in development
to +1.69% versus +1.34% for Claude's fixed passive benchmark. It fell behind at 2× slippage
and missed the Sharpe gate, ending the experiment before validation.

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

## Development portfolio decision

**Decision: park.** This entry beat the `x_o4` mean at base costs on the same development
sessions and data build, then fell behind at 2× slippage. The 2× Sharpe also fell below the
minimum. These were required development bars. No validation run was opened.

| Development metric | Confirmed recovery | Claude's `x_o4` |
|---|---:|---:|
| Trades / traded sessions | 952 / 654 | 3,200 / 1,603 |
| Mean executed position | $1,376 | $1,834 |
| Mean gross return per trade | +2.73% | +1.70% |
| Mean net per trade, 1× | **+1.69%** | +1.34% |
| Mean net per trade, 2× | +1.13% | **+1.24%** |
| Net dollar P&L, 1× / 2× | +$19,993 / +$13,435 | +$68,085 / +$62,128 |
| Daily t-statistic, 1× / 2× | 2.29 / 1.55 | 4.97 / 4.55 |
| Daily annualised Sharpe, 1× / 2× | 0.63 / 0.42 | 1.36 / 1.25 |
| Worst end-of-day drawdown, 1× / 2× | −$2,444 / −$3,197 | −$5,561 / −$6,659 |

Fixed comparisons use the exact stored means. The 1× difference was +0.35 percentage
points and the 2× difference was −0.11 points. The sample, regime and drawdown bars
all passed. The two development halves earned +$10,283 and +$3,152 at 2×. The maximum
allowed 2× drawdown was $10,000 and the annualised 2× Sharpe floor was 1.

Run `20261116T013621Z_gpt_rebound_confirmed_recovery_2b36bc0c` used clean commit
`1e8424f0` and build `6453bd3ec8`. The benchmark was
`20261115T232205Z_claude_rebound_limit_84ff9c3d`. Both runs used the same calendar,
account settings, cost calibration, and data build. The study and portfolio backtest
charged two trials to `intraday_rebound`, bringing the shared count to 64 at reporting.
The 2017–2023 validation and the holdout were left untouched for this strategy.

### Annual development portfolio results

| Year | Trades | Net/trade 1× | Net/trade 2× | Net P&L at 1× | Net P&L at 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 16 | +0.02% | −0.70% | +$12 | −$142 |
| 2004 | 51 | +1.79% | +1.22% | +$2,073 | +$1,679 |
| 2005 | 45 | −2.67% | −3.25% | −$1,864 | −$2,228 |
| 2006 | 44 | +0.67% | +0.12% | −$483 | −$853 |
| 2007 | 69 | +1.56% | +0.97% | +$1,981 | +$1,454 |
| 2008 | 286 | +3.47% | +2.95% | +$12,946 | +$11,409 |
| 2009 | 121 | +0.76% | +0.17% | −$324 | −$1,035 |
| 2010 | 37 | +2.62% | +2.03% | +$701 | +$407 |
| 2011 | 53 | −0.46% | −1.07% | +$201 | −$225 |
| 2012 | 36 | +1.45% | +0.89% | +$623 | +$366 |
| 2013 | 23 | +2.64% | +2.09% | +$1,375 | +$1,162 |
| 2014 | 43 | +2.24% | +1.69% | +$1,361 | +$1,068 |
| 2015 | 65 | −0.46% | −1.02% | −$1,181 | −$1,721 |
| 2016 | 63 | +2.57% | +2.01% | +$2,571 | +$2,095 |

## What the portfolio run changed

- The engine left 48 signals unfilled and declined 85 for capital. The 952 trades all
  exited in the closing auction. Mean actual notional was below the $2,000 target, as
  expected from participation. The weighted round-trip cost at 1× was 81 bps versus
  34 bps for the benchmark. Slippage was 50 bps versus 10 bps, helping explain why the
  gross return advantage narrowed at base costs and reversed at 2×.
- The May 6, 2010 Flash Crash accounted for 74 measured events and $15,231 of hypothetical
  2× P&L in the study. With the account and execution rules, it produced 10 trades and
  +$1,549 at 2×. Prices and executable size were unusually uncertain that day.
  [SEC and CFTC findings on the May 6 market events](https://www.sec.gov/files/marketevents-report.pdf)
- In the portfolio, 2008 produced about 85% of the total development net
  P&L at 2×. The largest single session contributed +$3,828 at 2×. Removing that date
  descriptively put the 1× mean at +1.49%. These observations did not change selection.
- The benchmark's later tick check supported its own passive fills. This run uses
  minute opens for market entries and the official closing price for the auction.
  These fills would require their own quote and trade audit. Evidence that marketable
  quotes and size survive across regimes, plus a materially stronger 2× Sharpe, would
  change the verdict.

## Volume and momentum follow-up

### Development event study

**Decision: develop the filtered variant.** The [addendum to the hypothesis](HYPOTHESIS.md)
was committed at `678c168` before the new run. All study gates passed. There were 613 events
across 457 sessions. The gross mean was +3.13%, with a day-clustered 95% interval of
+1.22% to +5.05%. Net of 2× slippage, the 2003–2009 and 2010–2016 means were +1.02% and
+1.55%. One entry occurred after expiry. The next-bar-only subset of 612 events returned
+3.12% gross (95% interval +1.22% to +5.04%), +2.02% net at 1× and +1.23% at 2×.
It remained positive at 2× in both halves (+1.02% and +1.53%).

Run `20261116T020656Z_gpt_rebound_confirmed_recovery_eebfba4c` used clean commit
`fe5e511a`, build `6453bd3ec8` and 2003-09-10 to 2016-12-30.
Replay passed on all 457 signal sessions. The original study is the comparison below.

| Development study metric | Original | Volume + momentum |
|---|---:|---:|
| Events | 1,085 | 613 |
| Gross mean to close | +3.59% | +3.13% |
| Mean net per event at 1× | +2.02% | +2.03% |
| Mean net per event at 2× | +0.88% | +1.24% |
| Mean round-trip cost at 1× | 1.57% | 1.10% |
| Orders above next-bar capacity | 49% | 19% |

| Filtered study outcome | 1× slippage | 2× slippage |
|---|---:|---:|
| 95% day-clustered interval, net to close | +0.12% to +3.95% | −0.66% to +3.17% |
| Summed event P&L | +$24,784 | +$15,134 |
| Daily event P&L t-statistic | 1.78 | 1.15 |
| Worst end-of-day drawdown of summed event P&L | −$4,276 | −$5,622 |

The study takes hypothetical $2,000 orders independently. Dollar P&L follows the same
unconstrained method as the original study. Turnover and capacity use trade bars.
The decline in the capacity-limited share supports the proxy at the event level.
The study stage does not establish realized size or costs for a portfolio.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 8 | +3.61% | +2.73% | +$569 | +$429 |
| 2004 | 36 | +2.64% | +1.71% | +$1,896 | +$1,232 |
| 2005 | 35 | −3.62% | −4.47% | −$2,527 | −$3,116 |
| 2006 | 29 | −2.71% | −3.38% | −$1,567 | −$1,954 |
| 2007 | 45 | +2.63% | +1.65% | +$2,369 | +$1,488 |
| 2008 | 143 | +4.74% | +4.12% | +$13,514 | +$11,761 |
| 2009 | 59 | −1.31% | −2.24% | −$1,544 | −$2,641 |
| 2010 | 61 | +7.89% | +6.88% | +$9,591 | +$8,362 |
| 2011 | 35 | +0.20% | −0.57% | +$138 | −$401 |
| 2012 | 24 | +1.05% | +0.39% | +$499 | +$182 |
| 2013 | 20 | +3.15% | +2.27% | +$1,254 | +$905 |
| 2014 | 29 | +1.45% | +0.81% | +$832 | +$466 |
| 2015 | 48 | −2.37% | −3.11% | −$2,269 | −$2,983 |
| 2016 | 41 | +2.48% | +1.72% | +$2,028 | +$1,404 |

### Development portfolio result

**Decision: park the filtered variant.** The joint filter improved mean net per trade
at both cost levels and cleared the 2× return of `x_o4` (+1.24%) on the same development
dates. The full gate missed on 2× annualised daily Sharpe (0.45 against a requirement
above 1). The sample and drawdown bars passed. Both halves were profitable at 2×
(+$11,077 and +$2,320). Validation and the sealed holdout remain unopened for this variant.

| Development portfolio metric | Original confirmed entry | Volume + momentum |
|---|---:|---:|
| Trades / active sessions | 952 / 654 | 579 / 457 |
| Mean filled notional on $2,000 target | $1,376 | $1,811 |
| Mean gross per trade | +2.73% | +2.50% |
| Weighted round-trip cost at 1× | 81 bps | 71 bps |
| Mean net per trade at 1× | +1.69% | **+1.75%** |
| Mean net per trade at 2× | +1.13% | **+1.28%** |
| Total net at 1× / 2× | +$19,993 / +$13,435 | +$18,097 / +$13,397 |
| Daily P&L t-statistic at 1× / 2× | 2.29 / 1.55 | 2.19 / 1.63 |
| Daily annualised Sharpe at 1× / 2× | 0.63 / 0.42 | 0.60 / 0.45 |
| Worst end-of-day drawdown at 1× / 2× | −$2,444 / −$3,197 | −$3,135 / −$3,682 |

The full run `20261116T020902Z_gpt_rebound_confirmed_recovery_255634a3` used clean commit
`0ceaa476`, build `6453bd3ec8` and the same 3,352 development sessions and risk settings
as the original. There were 613 signals, 33 capital rejections, one unfilled order and
579 closing-auction exits. The engine's one-bar expiry applied. The two new runs bring
the shared `intraday_rebound` trial count from 65 to 67 at reporting.

| Year | Trades | Net/trade 1× | Net/trade 2× | Net P&L 1× | Net P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 8 | +3.97% | +3.43% | +$637 | +$554 |
| 2004 | 36 | +3.07% | +2.53% | +$2,189 | +$1,870 |
| 2005 | 35 | −3.25% | −3.74% | −$1,739 | −$2,032 |
| 2006 | 29 | −2.43% | −2.86% | −$1,349 | −$1,594 |
| 2007 | 45 | +3.02% | +2.47% | +$2,541 | +$2,154 |
| 2008 | 143 | +4.98% | +4.58% | +$13,074 | +$12,038 |
| 2009 | 59 | −0.88% | −1.41% | −$1,420 | −$1,914 |
| 2010 | 28 | +2.56% | +2.04% | +$579 | +$334 |
| 2011 | 35 | +0.55% | +0.09% | +$224 | −$39 |
| 2012 | 24 | +1.32% | +0.89% | +$560 | +$362 |
| 2013 | 20 | +3.55% | +3.03% | +$1,724 | +$1,542 |
| 2014 | 29 | +1.72% | +1.30% | +$926 | +$688 |
| 2015 | 47 | −2.19% | −2.66% | −$2,204 | −$2,575 |
| 2016 | 41 | +2.82% | +2.35% | +$2,355 | +$2,009 |

The joint filter kept 613 of the original study's stock-days and selected a later
confirmation on 46 of them. The result estimates the combined effect of both conditions
and the timing change.

In the full run 2008 supplied $12,038, approximately 90% of total 2× profit. The remaining
years netted $1,359 at 2×. On the same fills, the annualised daily Sharpe of gross P&L was
0.84, below 1 even before commissions, fees, and slippage. Improving execution helps the
trade-level result. A better risk-adjusted strategy would need a more consistent source of
returns across sessions.

## Limit retest at the confirmed low

**Decision: park.** The same recovery signal with a resting bid at the already observed
local low produced 211 portfolio fills on 187 dates. Mean net was **−0.37% at 1× and
−0.47% at 2×**, down from +1.75% and +1.28% in the saved market-entry portfolio. The 50
fills in 2013–2016 averaged −1.21% and −1.31%. Counts cleared the sample bars. Return
and Sharpe failed, so the newer validation window stays unopened.

Run `20261116T061722Z_gpt_rebound_confirmed_recovery_8bd1d311` used clean commit
`2c606cfb`, preregistration `aafc5ed`, build `447e58e098` and 2003-09-10 through
2016-12-30. This was one added trial in `intraday_rebound`. There were 599 signals,
362 unfilled orders, 26 capital rejections, and 211 exits at the auction. Mean filled
size was $1,960. All 445 run-time replay checks passed.

| Development portfolio | 1× slippage | 2× slippage |
|---|---:|---:|
| Net per completed trade | −0.37% | −0.47% |
| Conditional mean winner | +10.14% | +10.03% |
| Conditional mean loser | −12.49% | −12.58% |
| Loss rate | 46.45% | 46.45% |
| Total net | −$1,304 | −$1,717 |
| Daily P&L t-statistic | −0.27 | −0.36 |
| Annualised daily Sharpe | −0.07 | −0.10 |
| Worst end-of-day drawdown | −$4,706 | −$4,915 |

The mean gross was already −0.11% per trade. The cheaper bid selected a group with
worse subsequent price movement. This is consistent with a retest selecting renewed
selling pressure, although the minute bars do not identify the cause of order flow.
The positive average winner conceals larger losing trades. The 3% target uses
all completed trades.

| Year | Trades | Net/trade 1× | Net/trade 2× | Net P&L 1× | Net P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 2 | +5.36% | +5.25% | +$214 | +$210 |
| 2004 | 20 | +3.01% | +2.91% | +$1,198 | +$1,156 |
| 2005 | 13 | −6.42% | −6.51% | −$1,613 | −$1,636 |
| 2006 | 11 | −0.50% | −0.60% | −$39 | −$60 |
| 2007 | 11 | +0.66% | +0.56% | +$114 | +$92 |
| 2008 | 53 | +2.48% | +2.38% | +$2,917 | +$2,810 |
| 2009 | 17 | −5.31% | −5.41% | −$1,865 | −$1,896 |
| 2010 | 13 | −2.51% | −2.61% | −$653 | −$679 |
| 2011 | 11 | −4.38% | −4.48% | −$958 | −$979 |
| 2012 | 10 | +3.30% | +3.19% | +$595 | +$576 |
| 2013 | 5 | +7.26% | +7.15% | +$722 | +$712 |
| 2014 | 16 | +2.97% | +2.87% | +$947 | +$914 |
| 2015 | 16 | −7.33% | −7.43% | −$2,337 | −$2,367 |
| 2016 | 13 | −2.09% | −2.19% | −$546 | −$572 |
