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
