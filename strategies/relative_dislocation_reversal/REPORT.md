# Relative dislocation reversal

**Verdict: park.** The development study found 470 events on 356 dates, with mean net
returns to the close of **+2.39% at 1× and +1.65% at 2×**. The 120 events in 2013–2016
averaged **−0.40% and −1.06%**, respectively. The later block's gross mean was +0.63%,
below the required +3%. The sample and full-period gross gates passed. The recent
development gate in the [preregistration](HYPOTHESIS.md) failed, ending the experiment
before the portfolio and validation runs.

Run `20261116T061343Z_gpt_relative_dislocation_reversal_cbe31371` used clean commit
`af06c51e`, preregistration `304a6f4` and build `447e58e098` over 2003-09-10 through
2016-12-30. It added one trial to `intraday_rebound`. All 470 study entries were on
time and replay passed on the 356 signal sessions.

| Close outcome | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net return per event | +2.39% | +1.65% |
| 95% day-clustered interval | +0.28% to +4.65% | −0.44% to +3.83% |
| Summed event P&L | +$22,398 | +$15,515 |
| Daily event P&L t-statistic | 2.08 | 1.50 |
| Worst end-of-day drawdown of summed events | −$3,037 | −$6,198 |

The full-period gross mean was +3.47% (95% interval +1.34% to +5.78%). Dollar P&L sums
the saved event notionals and net returns by session across 3,352 development dates.
Overlapping events in this study do not share the portfolio's capital or participation
constraints. About 10% exceeded 5% next-bar volume at target size.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 6 | +7.63% | +7.15% | +$913 | +$856 |
| 2004 | 19 | +0.94% | +0.22% | +$356 | +$83 |
| 2005 | 12 | −2.17% | −2.77% | −$517 | −$661 |
| 2006 | 17 | −2.17% | −2.71% | −$734 | −$916 |
| 2007 | 33 | +4.87% | +4.16% | +$3,208 | +$2,738 |
| 2008 | 163 | +6.72% | +5.83% | +$21,877 | +$18,974 |
| 2009 | 29 | −0.82% | −1.50% | −$474 | −$867 |
| 2010 | 17 | −1.80% | −2.53% | −$615 | −$864 |
| 2011 | 35 | −1.30% | −1.88% | −$912 | −$1,316 |
| 2012 | 19 | +0.64% | +0.06% | +$244 | +$22 |
| 2013 | 21 | +2.63% | +2.06% | +$1,107 | +$866 |
| 2014 | 22 | −2.26% | −2.81% | −$989 | −$1,229 |
| 2015 | 41 | +0.47% | −0.23% | +$381 | −$188 |
| 2016 | 36 | −2.01% | −2.75% | −$1,447 | −$1,984 |

The positive pooled result was concentrated in 2008. That year's event P&L at 2×
exceeded the sum for the entire study. The trade-intensity selector and synchronous
reference were insufficient to give positive late-development returns. A credible
improvement would have to demonstrate repeatable edge in later development and meet
the separate recent validation requirement.

## Absolute-liquidity cohort

**Close-exit verdict: park.** The full study had 301 events on 199 dates and gained
+3.94% at 1× and +3.48% at 2× through the close. The 51 events on 46 dates in 2013–2016
earned +2.15% and +1.82%. Their +2.72% gross mean missed the original +3% recent
screen. The full-period and sample gates passed. This close-exit definition stopped
at the study stage.

Run `20261116T062029Z_gpt_relative_dislocation_reversal_56620f46` used clean commit
`d426877e`, preregistration `2cec783`, build `447e58e098` and 2003-09-10 through
2016-12-30. It added one charged `intraday_rebound` trial. All study entries were
within expiry. All 199 replay checks passed. The estimated share above the
entry-bar capacity cap fell from about 10% to 2%, compared with the original cohort.

| Close outcome | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net return per event | +3.94% | +3.48% |
| 95% session-clustered interval | +1.29% to +6.84% | +0.83% to +6.39% |
| Summed event P&L | +$23,633 | +$20,854 |
| Daily event P&L t-statistic | 2.60 | 2.33 |
| Worst drawdown of summed events | −$2,645 | −$2,962 |

Dollar results use the independent event sizing in the saved study and all 3,352
sessions. This series ignores the account budget. The sample did not establish
tradable capacity or portfolio risk. Study prices use the market-entry proxy and
approximate exit costs from the entry bar. The 2× result remained dominated by 2008.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +35.08% | +34.98% | +$692 | +$690 |
| 2004 | 6 | +6.93% | +6.70% | +$829 | +$802 |
| 2005 | 4 | −6.39% | −6.66% | −$509 | −$530 |
| 2006 | 10 | −1.33% | −1.61% | −$264 | −$320 |
| 2007 | 24 | +5.12% | +4.62% | +$2,451 | +$2,210 |
| 2008 | 157 | +6.18% | +5.62% | +$19,367 | +$17,606 |
| 2009 | 22 | −0.16% | −0.51% | −$68 | −$221 |
| 2010 | 4 | +1.64% | +1.45% | +$127 | +$111 |
| 2011 | 14 | −4.43% | −4.74% | −$1,242 | −$1,328 |
| 2012 | 8 | +0.36% | −0.12% | +$60 | −$17 |
| 2013 | 9 | +2.08% | +1.75% | +$378 | +$318 |
| 2014 | 14 | +3.20% | +2.86% | +$895 | +$800 |
| 2015 | 19 | +4.79% | +4.49% | +$1,807 | +$1,695 |
| 2016 | 9 | −4.96% | −5.37% | −$890 | −$963 |

## Fixed one-hour exit

### Study decision

**Decision: develop the one-hour exit.** The frozen horizon choice in commit
`1980491` applies `r_60` from the saved liquid-cohort study
`20261116T062029Z_gpt_relative_dislocation_reversal_56620f46`. The event count,
dates and eligibility are identical. The 301 events on 199 dates had +3.89%
mean gross (day-clustered 95% interval +2.42% to +5.28%). The 51 events on 46
dates in 2013–2016 had +4.48% gross, +3.91% at 1× and +3.58% at 2×. The study
gates passed and all entries were on time.

| One-hour study, full development | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | +3.17% | +2.71% |
| 95% day-clustered interval | +1.73% to +4.58% | +1.25% to +4.11% |
| Summed event P&L | +$19,022 | +$16,243 |
| Daily event P&L t-statistic | 3.94 | 3.47 |
| Worst end-of-day drawdown of summed events | −$1,481 | −$1,568 |

The dollar series is the same unconstrained event estimator at the one-hour
horizon. The study estimates both sides' costs from the entry bar. The portfolio
test prices its timed sale separately and models its volume and market open.
The horizon choice was informed by the development curve.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +23.51% | +23.40% | +$464 | +$462 |
| 2004 | 6 | +5.44% | +5.21% | +$652 | +$624 |
| 2005 | 4 | +0.08% | −0.19% | +$3 | −$18 |
| 2006 | 10 | +5.87% | +5.59% | +$1,171 | +$1,115 |
| 2007 | 24 | +3.28% | +2.77% | +$1,566 | +$1,325 |
| 2008 | 157 | +2.92% | +2.35% | +$9,128 | +$7,367 |
| 2009 | 22 | +1.47% | +1.12% | +$646 | +$493 |
| 2010 | 4 | +5.45% | +5.26% | +$431 | +$415 |
| 2011 | 14 | −0.95% | −1.25% | −$267 | −$353 |
| 2012 | 8 | +7.78% | +7.30% | +$1,245 | +$1,169 |
| 2013 | 9 | +6.50% | +6.17% | +$1,168 | +$1,108 |
| 2014 | 14 | +5.38% | +5.04% | +$1,506 | +$1,411 |
| 2015 | 19 | +5.48% | +5.18% | +$2,073 | +$1,961 |
| 2016 | 9 | −4.27% | −4.67% | −$763 | −$836 |

### One-hour portfolio result

**Decision: park.** The portfolio earned **+3.33% net per trade at 1× and +2.93% at
2×**. The 51 trades on 46 dates in 2013–2016 returned +4.16% and +3.85%. Counts,
returns and drawdown passed their development bars. Annualised daily Sharpe at 2×
was 0.91, below the preregistered requirement above 1. No validation run was
started, so the +3% research objective and recent 2022+ hurdle remain unverified.

Run `20261116T062349Z_gpt_relative_dislocation_reversal_034697eb` used clean commit
`2cde0e33`, build `447e58e098` and 2003-09-10 through 2016-12-30. It added one
trial to `intraday_rebound`. Of 301 signals, eight were refused for capital, with
293 completed trades on 199 sessions. There were 291 clock exits and two auction
exits. The mean filled notional was $1,982 against a $2,000 target.

| Development portfolio | 1× slippage | 2× slippage |
|---|---:|---:|
| Net per completed trade | +3.33% | +2.93% |
| Mean winner | +10.82% | +10.54% |
| Mean loser | −9.89% | −10.10% |
| Loss rate | 36.18% | 36.86% |
| Total net | +$19,296 | +$17,041 |
| Daily P&L t-statistic | 3.68 | 3.32 |
| Annualised daily Sharpe | 1.01 | 0.91 |
| Worst end-of-day drawdown | −$1,473 | −$1,550 |

The all-trade gross mean was +3.97%. 2008 supplied about 46% of the net at 2×.
A descriptive read of entry and exit minutes found only five days with more than
three simultaneous holdings. A simple change to the position count would leave
most sessions unchanged. Live market quotes, actual exit liquidity and generalisation
to the later validation years remain unmeasured. Evidence of stronger daily
consistency across different dates would change the verdict.

| Year | Trades | Net/trade 1× | Net/trade 2× | Net P&L 1× | Net P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +23.61% | +23.46% | +$466 | +$463 |
| 2004 | 6 | +5.52% | +5.31% | +$659 | +$635 |
| 2005 | 4 | −0.01% | −0.26% | −$2 | −$22 |
| 2006 | 10 | +6.03% | +5.79% | +$1,207 | +$1,159 |
| 2007 | 24 | +3.30% | +2.87% | +$1,584 | +$1,378 |
| 2008 | 149 | +3.12% | +2.66% | +$9,110 | +$7,780 |
| 2009 | 22 | +1.65% | +1.32% | +$727 | +$584 |
| 2010 | 4 | +5.43% | +5.27% | +$434 | +$421 |
| 2011 | 14 | −0.90% | −1.17% | −$253 | −$329 |
| 2012 | 8 | +6.97% | +6.48% | +$1,118 | +$1,040 |
| 2013 | 9 | +6.59% | +6.30% | +$1,182 | +$1,130 |
| 2014 | 14 | +5.57% | +5.23% | +$1,561 | +$1,465 |
| 2015 | 19 | +5.78% | +5.51% | +$2,184 | +$2,085 |
| 2016 | 9 | −3.88% | −4.25% | −$682 | −$747 |

## Two-position cap

**Decision: park.** The cap raised the mean net per trade to **+3.41% at 1× and
+3.03% at 2×** on 260 completed trades. At 2× the Sharpe fell to 0.89 and
drawdown increased. The required Sharpe above 1 still failed, so this
specification stopped in development.

| Development metric | Ten slots | Two slots |
|---|---:|---:|
| Trades / active dates | 293 / 199 | 260 / 199 |
| Gross mean per trade | +3.97% | +4.04% |
| Net/trade at 1× | +3.33% | +3.41% |
| Net/trade at 2× | +2.93% | +3.03% |
| Total net at 1× / 2× | +$19,296 / +$17,041 | +$17,679 / +$15,739 |
| Daily P&L t-statistic at 1× / 2× | 3.68 / 3.32 | 3.60 / 3.25 |
| Annualised daily Sharpe at 1× / 2× | 1.01 / 0.91 | 0.99 / 0.89 |
| Worst end-of-day drawdown at 1× / 2× | −$1,473 / −$1,550 | −$2,280 / −$2,435 |

The 51 trades on 46 dates in 2013–2016 were identical in aggregate to the ten-slot
version, averaging +4.16% at 1× and +3.85% at 2×. The sample, return and drawdown
bars passed. At 1× mean winners and losers were +10.78% and −9.83%, with a 35.77%
loss rate. At 2× those were +10.54%, −10.02%, and 36.54%. The headline averages
include both wins and losses.

Run `20261116T155133Z_gpt_relative_dislocation_reversal_c00d4db2` used hypothesis
commit `aba37a9`, clean run commit `e1a1ee96`, build `447e58e098` and the fixed
2003–2016 dates. All 199 run-time replay checks passed. The cap removed 33
completed trades, 32 from 2008 and one from 2007, while the count of dates was
unchanged. It reduced total net and increased drawdown. This added one
`intraday_rebound` development trial. There was no validation or holdout run.

| Year | Trades | Net/trade 1× | Net/trade 2× | Net P&L 1× | Net P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +23.61% | +23.46% | +$466 | +$463 |
| 2004 | 6 | +5.52% | +5.31% | +$659 | +$635 |
| 2005 | 4 | −0.01% | −0.26% | −$2 | −$22 |
| 2006 | 10 | +6.03% | +5.79% | +$1,207 | +$1,159 |
| 2007 | 23 | +3.40% | +2.97% | +$1,564 | +$1,366 |
| 2008 | 117 | +3.22% | +2.78% | +$7,513 | +$6,490 |
| 2009 | 22 | +1.65% | +1.32% | +$727 | +$584 |
| 2010 | 4 | +5.43% | +5.27% | +$434 | +$421 |
| 2011 | 14 | −0.90% | −1.17% | −$253 | −$329 |
| 2012 | 8 | +6.97% | +6.48% | +$1,118 | +$1,040 |
| 2013 | 9 | +6.59% | +6.30% | +$1,182 | +$1,130 |
| 2014 | 14 | +5.57% | +5.23% | +$1,561 | +$1,465 |
| 2015 | 19 | +5.78% | +5.51% | +$2,184 | +$2,085 |
| 2016 | 9 | −3.88% | −4.25% | −$682 | −$747 |

The retry found a higher mean within the same historical sample. A candidate
that earns across more independent dates is needed to improve confidence in
the daily return series. The later 2022–2023 pre-seal gate has yet to be tested
for this signal.

## Peer-relative recovery confirmation

**Study decision: develop.** The preregistered one-hour horizon passed the full
and recent development gates. Run `20261116T164207Z_gpt_relative_dislocation_reversal_a740b270`
used the 2003-09-10 to 2016-12-30 period, commit `80213993` and build `447e58e098`.
Hypothesis commit `213b438` came before the run. The study returned 295 events on 199
sessions, all within intended expiry, and all 199 replay checks passed.

The full sample averaged +4.01% gross with a day-clustered 95% interval of +2.50%
to +5.41%. The 2013–2016 block had 50 events on 46 sessions, averaging +4.43% gross
and +3.86% and +3.53% net at 1× and 2×. The original one-hour study had 301 events
and +3.17% and +2.71% net overall. A session may change if the first acceptable
confirmation moves. These are development estimates.

| One-hour study | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | +3.28% | +2.82% |
| 95% day-clustered interval | +1.80% to +4.68% | +1.35% to +4.23% |
| Summed event P&L | +$19,315 | +$16,569 |
| Daily event P&L t-statistic | 4.01 | 3.56 |
| Worst drawdown of summed events | −$1,413 | −$1,490 |

The dollar series uses the saved hypothetical events across all 3,352 development
sessions. The study prices both marketable sides using inputs from the entry bar.
Portfolio restrictions and actual exit-bar participation apply in the next test.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +23.51% | +23.40% | +$464 | +$462 |
| 2004 | 6 | +5.44% | +5.21% | +$652 | +$624 |
| 2005 | 4 | +0.08% | −0.19% | +$3 | −$18 |
| 2006 | 10 | +5.87% | +5.59% | +$1,171 | +$1,115 |
| 2007 | 24 | +3.28% | +2.77% | +$1,566 | +$1,325 |
| 2008 | 152 | +3.15% | +2.58% | +$9,547 | +$7,816 |
| 2009 | 22 | +1.47% | +1.12% | +$646 | +$493 |
| 2010 | 4 | +5.45% | +5.26% | +$431 | +$415 |
| 2011 | 14 | −0.95% | −1.25% | −$267 | −$353 |
| 2012 | 8 | +7.78% | +7.30% | +$1,245 | +$1,169 |
| 2013 | 9 | +6.50% | +6.17% | +$1,168 | +$1,108 |
| 2014 | 14 | +5.38% | +5.04% | +$1,506 | +$1,411 |
| 2015 | 18 | +5.43% | +5.12% | +$1,946 | +$1,837 |
| 2016 | 9 | −4.27% | −4.67% | −$763 | −$836 |

### Peer-relative portfolio result

**Decision: park.** The stronger confirmation averaged **+3.42% net per trade at
1× and +3.03% at 2×** in development. The 50 trades on 46 dates in 2013–2016
earned +4.04% and +3.73%. The sample, return and drawdown bars passed.
Annualised daily Sharpe at 2× was **0.93**, below the preregistered
requirement above 1. Validation was not started.

| Development portfolio | Absolute recovery | Peer-relative confirmation |
|---|---:|---:|
| Trades / active dates | 293 / 199 | 288 / 199 |
| Gross mean per trade | +3.97% | +4.08% |
| Net/trade at 1× | +3.33% | +3.42% |
| Net/trade at 2× | +2.93% | +3.03% |
| Net dollars at 1× / 2× | +$19,296 / +$17,041 | +$19,526 / +$17,298 |
| Daily P&L t-statistic at 1× / 2× | 3.68 / 3.32 | 3.74 / 3.38 |
| Annualised daily Sharpe at 1× / 2× | 1.01 / 0.91 | 1.02 / 0.93 |
| Worst drawdown at 1× / 2× | −$1,473 / −$1,550 | −$1,408 / −$1,474 |

The market-relative rule excluded six stock-days from the original study and
delayed three of the retained signals. The outcome is a small change on nearly
the same calendar and does not provide an independent return estimate. In the
portfolio, 295 signals produced 288 trades with seven capital rejections.
The mean executed notional was $1,982. At base costs the conditional mean
winner was +10.81% and the mean loser was −10.05%, with a 35.42% loss rate.

The portfolio run `20261116T164343Z_gpt_relative_dislocation_reversal_87bd5ae1`
used clean commit `16698363` and build `447e58e098`. The study and portfolio run
added two trials to `intraday_rebound`. All 199 signal-session replay checks
passed. The 2022–2023 validation block and the sealed holdout stayed closed.

| Year | Trades | Net/trade 1× | Net/trade 2× | Net P&L 1× | Net P&L 2× |
|---|---:|---:|---:|---:|
| 2003 | 1 | +23.61% | +23.46% | +$466 | +$463 |
| 2004 | 6 | +5.52% | +5.31% | +$659 | +$635 |
| 2005 | 4 | −0.01% | −0.26% | −$2 | −$22 |
| 2006 | 10 | +6.03% | +5.79% | +$1,207 | +$1,159 |
| 2007 | 24 | +3.30% | +2.87% | +$1,584 | +$1,378 |
| 2008 | 145 | +3.35% | +2.89% | +$9,541 | +$8,235 |
| 2009 | 22 | +1.65% | +1.32% | +$727 | +$584 |
| 2010 | 4 | +5.43% | +5.27% | +$434 | +$421 |
| 2011 | 14 | −0.90% | −1.17% | −$253 | −$329 |
| 2012 | 8 | +6.97% | +6.48% | +$1,118 | +$1,040 |
| 2013 | 9 | +6.59% | +6.30% | +$1,182 | +$1,130 |
| 2014 | 14 | +5.57% | +5.23% | +$1,561 | +$1,465 |
| 2015 | 18 | +5.53% | +5.26% | +$1,983 | +$1,887 |
| 2016 | 9 | −3.88% | −4.25% | −$682 | −$747 |

## Quiet baseline before the dislocation

**Decision: park.** The one-hour study averaged **+5.26% net at 1×** and **+4.88%
at 2×** across 106 events on 89 sessions. The gross mean was +5.87%, with a
day-clustered 95% interval of +3.11% to +8.76%. In 2013–2016, the 24 events
averaged +4.30% gross, +3.88% at 1× and +3.61% at 2×. This missed all three
sample minima (150 events, 90 sessions and 40 events in 2013–2016). The
portfolio and validation runs were skipped under the preregistered rules.

Run `20261116T164732Z_gpt_relative_dislocation_reversal_7bceca33` used clean
commit `7f1b6442`, data build `447e58e098` and development dates 2003-09-10
through 2016-12-30. Preregistration commit `9eb39c8` preceded the run. This
adds one trial to `intraday_rebound`. All entry timestamps are one clock
minute after the signal, and all 89 signal-session lookahead replays passed.
The strategy tests also check that the baseline rejects thin observations
and a wide range. Validation and the sealed holdout stayed closed.

| One-hour study | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | +5.26% | +4.88% |
| 95% day-clustered interval | +2.55% to +8.13% | +2.18% to +7.73% |
| Summed event P&L | +$11,114 | +$10,296 |
| Daily event P&L t-statistic | 3.34 | 3.14 |
| Worst drawdown of summed events | −$869 | −$964 |

Event P&L sums the saved hypothetical notionals and applies the stored fee
and slippage estimates. Daily statistics include all 3,352 development
sessions. The original liquid one-hour study had 301 events. The tighter
rule's mean comes from a smaller selected sample, with 44 of 106 events
from 2008. The gain per event does not establish dependable returns across
regimes. Actual quote depth and tradability around sudden breaks remain
unverified.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +23.51% | +23.40% | +$464 | +$462 |
| 2004 | 5 | +7.19% | +6.95% | +$718 | +$693 |
| 2005 | 2 | +9.04% | +8.85% | +$358 | +$351 |
| 2006 | 2 | +13.06% | +12.91% | +$520 | +$514 |
| 2007 | 8 | +10.62% | +10.23% | +$1,693 | +$1,631 |
| 2008 | 44 | +6.10% | +5.55% | +$5,353 | +$4,864 |
| 2009 | 6 | −4.61% | −4.85% | −$549 | −$579 |
| 2010 | 3 | +3.07% | +2.87% | +$180 | +$168 |
| 2011 | 7 | −0.76% | −0.99% | −$108 | −$139 |
| 2012 | 4 | +7.88% | +7.54% | +$628 | +$601 |
| 2013 | 5 | +7.08% | +6.75% | +$706 | +$673 |
| 2014 | 6 | +5.74% | +5.49% | +$685 | +$655 |
| 2015 | 8 | +6.50% | +6.29% | +$1,036 | +$1,003 |
| 2016 | 5 | −5.76% | −6.06% | −$571 | −$601 |

## Two-hour peer-relative exit

**Study decision: develop.** The two-hour horizon passed the preregistered
event gates in the existing peer-relative study
`20261116T164207Z_gpt_relative_dislocation_reversal_a740b270`, registered for
this decision in commit `92021b2`. All 295 entries followed the signal by
one clock minute, across 199 sessions, and all 199 replay checks passed.
The gross mean was +4.39% with a day-clustered 95% interval of +2.69%
to +6.14%. In 2013–2016, 50 events across 46 sessions averaged +4.01%
gross, +3.44% net at base costs and +3.11% at doubled slippage.

| Two-hour study | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | +3.67% | +3.21% |
| 95% day-clustered interval | +2.00% to +5.37% | +1.54% to +4.90% |
| Summed event P&L | +$21,597 | +$18,851 |
| Daily event P&L t-statistic | 3.70 | 3.34 |
| Worst drawdown of summed events | −$1,639 | −$1,937 |

This is one additional horizon look using a saved run and all 3,352 development
sessions. The two-hour return uses the study endpoint close and stored entry-side
cost inputs. The portfolio applies the exit rule, exit-side costs and capacity.
The horizon was chosen after reviewing the full development curve, so the
two-hour result shares the first test's data and selection history.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +31.49% | +31.38% | +$622 | +$619 |
| 2004 | 6 | +5.78% | +5.55% | +$692 | +$664 |
| 2005 | 4 | −6.56% | −6.83% | −$525 | −$546 |
| 2006 | 10 | +4.67% | +4.39% | +$930 | +$875 |
| 2007 | 24 | +4.04% | +3.54% | +$1,932 | +$1,691 |
| 2008 | 152 | +4.29% | +3.72% | +$13,013 | +$11,282 |
| 2009 | 22 | +0.57% | +0.22% | +$250 | +$97 |
| 2010 | 4 | +3.71% | +3.51% | +$292 | +$276 |
| 2011 | 14 | −2.05% | −2.36% | −$575 | −$661 |
| 2012 | 8 | +9.59% | +9.11% | +$1,532 | +$1,455 |
| 2013 | 9 | +5.10% | +4.77% | +$919 | +$860 |
| 2014 | 14 | +4.48% | +4.14% | +$1,253 | +$1,157 |
| 2015 | 18 | +4.27% | +3.97% | +$1,528 | +$1,420 |
| 2016 | 9 | −1.48% | −1.88% | −$265 | −$338 |

### Two-hour portfolio result

**Decision: park.** The two-hour exit raised the development mean to **+3.72%
net per trade at 1× and +3.34% at 2×**. At 2×, annualised daily Sharpe was
**0.94**, below the preregistered requirement above 1. The sample, return
and drawdown bars passed. The 50 trades on 46 dates in 2013–2016 averaged
+3.48% and +3.18% net at 1× and 2×. Validation was skipped.

| Development portfolio | One-hour exit | Two-hour exit |
|---|---:|---:|
| Trades / active dates | 288 / 199 | 288 / 199 |
| Gross mean per trade | +4.08% | +4.37% |
| Net/trade at 1× | +3.42% | +3.72% |
| Net/trade at 2× | +3.03% | +3.34% |
| Net dollars at 1× / 2× | +$19,526 / +$17,298 | +$21,292 / +$19,120 |
| Daily P&L t-statistic at 1× / 2× | 3.74 / 3.38 | 3.72 / 3.42 |
| Annualised daily Sharpe at 1× / 2× | 1.02 / 0.93 | 1.02 / 0.94 |
| Worst drawdown at 1× / 2× | −$1,408 / −$1,474 | −$1,561 / −$1,826 |

Trade dates, symbols, entry times and starting notionals matched the one-hour
portfolio exactly. Both runs rejected seven entries for capital and averaged
$1,982 in filled notional. The longer hold had 266 timed exits and 22 auction
exits. In 51 timed exits the final fill came after the scheduled minute.
Kinn models marketable fills from minute bars with a participation cap. The
actual price and liquidity on both sides remain unverified.

At base costs, 183 winners averaged +11.59% and 105 losers averaged −9.98%.
At 2×, 178 winners averaged +11.52% and 110 losers averaged −9.90%. This
change improved the trade mean on the same entries and increased worst
drawdown. It left the stressed risk result below the gate.

Run `20261116T211344Z_gpt_relative_dislocation_reversal_6ccbf180` used clean
commit `7f37041d`, data build `447e58e098` and development dates 2003-09-10
through 2016-12-30. All 288 entries were on the next clock minute, and all 199
signal-session replay checks passed. The portfolio is one additional counted
`intraday_rebound` run. Both the validation period and the sealed holdout
stayed unopened for this variant.

| Year | Trades | Net/trade 1× | Net/trade 2× | Net P&L 1× | Net P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +31.46% | +31.33% | +$621 | +$618 |
| 2004 | 6 | +5.78% | +5.58% | +$690 | +$666 |
| 2005 | 4 | −6.52% | −6.76% | −$519 | −$538 |
| 2006 | 10 | +4.64% | +4.40% | +$928 | +$880 |
| 2007 | 24 | +4.09% | +3.68% | +$1,959 | +$1,766 |
| 2008 | 145 | +4.29% | +3.84% | +$12,331 | +$11,053 |
| 2009 | 22 | +0.69% | +0.37% | +$306 | +$165 |
| 2010 | 4 | +3.78% | +3.62% | +$302 | +$290 |
| 2011 | 14 | −2.04% | −2.32% | −$577 | −$653 |
| 2012 | 8 | +11.25% | +10.77% | +$1,800 | +$1,724 |
| 2013 | 9 | +5.11% | +4.82% | +$919 | +$866 |
| 2014 | 14 | +4.50% | +4.17% | +$1,260 | +$1,168 |
| 2015 | 18 | +4.38% | +4.11% | +$1,569 | +$1,474 |
| 2016 | 9 | −1.53% | −1.89% | −$297 | −$361 |

## Ten-point dislocation after a quiet baseline

**Decision: park.** The one-hour event study earned **+2.80% net at 1× and
+2.45% at 2×** over 214 events on 177 dates. The 47 events on 45 dates in
2013–2016 averaged +1.21% gross, +0.68% at 1× and +0.37% at 2×. The later
development block missed the +3% gross gate. The full-sample return and
sample gates passed. The portfolio and validation phases were skipped.

Compared with the 12-point quiet baseline, the new cutoff added 88 dates
and 108 stock-days, retained all original stock-days, and moved the
signal minute on seven retained stock-days. The 95 events on dates the
prior rule did not trade earned +0.38% net at 1× and +0.07% at 2×, as a
descriptive comparison. The broader rule roughly doubled the calendar
coverage and diluted the return.

| One-hour development study | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | +2.80% | +2.45% |
| 95% day-clustered interval | +1.04% to +4.40% | +0.69% to +4.03% |
| Summed event P&L | +$11,959 | +$10,454 |
| Daily event P&L t-statistic | 3.12 | 2.77 |
| Worst drawdown of summed events | −$1,250 | −$1,455 |

Gross mean was +3.37% with a day-clustered 95% interval of +1.61% to +4.99%.
The daily dollar metrics sum the hypothetical exposures across all 3,352
development sessions. The study models both sides from entry-bar inputs.
The marketable prices, quoted depth and sale proceeds remain unverified.

Run `20261116T212112Z_gpt_relative_dislocation_reversal_513e460f` used clean
commit `ab05f4a6`, build `447e58e098` and the 2003-09-10 through 2016-12-30
period. Preregistration `da3bbee` followed the 12-point study and preceded
this run. It is one additional counted `intraday_rebound` trial. Every entry
was one clock minute after the signal, and all 177 session replay checks
passed. This data-informed change does not supply independent evidence.
Validation and the sealed holdout stayed unopened.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 3 | +6.83% | +6.71% | +$404 | +$397 |
| 2004 | 9 | +4.90% | +4.70% | +$879 | +$842 |
| 2005 | 4 | +9.40% | +9.03% | +$748 | +$719 |
| 2006 | 7 | +4.71% | +4.50% | +$655 | +$626 |
| 2007 | 17 | +6.88% | +6.56% | +$2,333 | +$2,225 |
| 2008 | 88 | +3.50% | +3.04% | +$6,151 | +$5,342 |
| 2009 | 11 | −2.48% | −2.78% | −$541 | −$607 |
| 2010 | 7 | +5.78% | +5.57% | +$800 | +$771 |
| 2011 | 12 | −3.98% | −4.20% | −$955 | −$1,007 |
| 2012 | 9 | +4.73% | +4.48% | +$849 | +$804 |
| 2013 | 6 | +5.31% | +5.00% | +$636 | +$598 |
| 2014 | 16 | −0.64% | −1.02% | −$209 | −$330 |
| 2015 | 13 | +4.21% | +3.91% | +$1,090 | +$1,012 |
| 2016 | 12 | −3.69% | −3.93% | −$881 | −$938 |

## Size-group benchmark

**Study decision: develop.** The event study passed the original two-hour
gates with 291 events across 199 dates. It averaged +4.33% gross, with a
day-clustered 95% interval of +2.49% to +6.08%. The 2013–2016 block had 51
events on 46 dates, averaging +3.36% gross, +2.81% net at base costs and
+2.49% at doubled slippage. All entries followed the signal by one clock
minute and all 199 replay checks passed.

| Two-hour development study | 1× slippage | 2× slippage |
|---|---:|---:|
| Mean net per event | +3.62% | +3.16% |
| 95% day-clustered interval | +1.78% to +5.33% | +1.35% to +4.84% |
| Summed event P&L | +$20,998 | +$18,328 |
| Daily event P&L t-statistic | 3.58 | 3.23 |
| Worst drawdown of summed events | −$1,493 | −$1,758 |

The size-group reference added five dates to the large-cap study and gave
up five. It added seven stock-days, omitted eleven and shifted the entry on
four retained stock-days. The large-cap study's two-hour mean was +3.67%
at base costs and +3.21% at doubled slippage. The two definitions use
nearly the same development data and this comparison is descriptive.

Run `20261116T212516Z_gpt_relative_dislocation_reversal_eb5399da` used
commit `bc853ae5`, data build `447e58e098` and the development period
2003-09-10 to 2016-12-30. Registration `f060464` preceded the run. The
study is an additional counted `intraday_rebound` trial. The study prices
both sides from the entry bar and sums hypothetical orders across all
3,352 development sessions. The qualifying portfolio run will apply
its actual exit rule, buying power and bar participation.

| Year | Events | Net/event 1× | Net/event 2× | Event P&L 1× | Event P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +31.49% | +31.38% | +$622 | +$619 |
| 2004 | 5 | +8.38% | +8.14% | +$835 | +$811 |
| 2005 | 4 | −6.56% | −6.83% | −$525 | −$546 |
| 2006 | 10 | +4.67% | +4.39% | +$930 | +$875 |
| 2007 | 24 | +5.23% | +4.73% | +$2,503 | +$2,265 |
| 2008 | 150 | +4.15% | +3.59% | +$12,433 | +$10,751 |
| 2009 | 20 | +0.22% | −0.13% | +$89 | −$49 |
| 2010 | 4 | +3.71% | +3.51% | +$292 | +$276 |
| 2011 | 14 | −2.05% | −2.36% | −$575 | −$661 |
| 2012 | 8 | +9.59% | +9.11% | +$1,532 | +$1,455 |
| 2013 | 9 | +5.10% | +4.77% | +$919 | +$860 |
| 2014 | 13 | +2.46% | +2.14% | +$642 | +$557 |
| 2015 | 19 | +4.42% | +4.12% | +$1,670 | +$1,558 |
| 2016 | 10 | −1.85% | −2.23% | −$368 | −$443 |

### Size-group portfolio result

**Decision: park.** The two-hour size-group portfolio earned **+3.73%
net per trade at 1× and +3.36% at 2×**. At 2× the annualised daily
Sharpe was **0.93**, below the preregistered bar above 1. It met the
sample, return and drawdown bars. The 51 trades on 46 dates in
2013–2016 averaged +2.85% at base costs and +2.56% at doubled slippage.
Validation was skipped.

| Two-hour development portfolio | Large-cap reference | Size-group reference |
|---|---:|---:|
| Trades / active dates | 288 / 199 | 286 / 199 |
| Gross mean per trade | +4.37% | +4.36% |
| Net/trade at 1× | +3.72% | +3.73% |
| Net/trade at 2× | +3.34% | +3.36% |
| Net dollars at 1× / 2× | +$21,292 / +$19,120 | +$21,199 / +$19,083 |
| Daily P&L t-statistic at 1× / 2× | 3.72 / 3.42 | 3.69 / 3.40 |
| Annualised daily Sharpe at 1× / 2× | 1.02 / 0.94 | 1.01 / 0.93 |
| Worst drawdown at 1× / 2× | −$1,561 / −$1,826 | −$1,443 / −$1,664 |

The subgroup reference reduced drawdown and slightly reduced total net
P&L and stressed Sharpe. Both portfolios still had 145 trades in 2008.
The matched benchmark changed a small share of the trade flow and did
not address the calendar concentration. The cost and timing results rely
on minute-bar fills. They do not verify live executable size or price.

At base costs, 184 winners averaged +11.30% and 102 losers averaged
−9.91%. At 2×, 179 winners averaged +11.23% and 107 losers
averaged −9.81%. The 291 signals produced 286 fills with five capital
rejections and a mean executed notional of $1,982. There were 264
timed exits and 22 auction exits.

Run `20261116T212704Z_gpt_relative_dislocation_reversal_e44b9cb3`
used clean commit `5a2f695b` and build `447e58e098` from
2003-09-10 through 2016-12-30. All 286 entries followed the signal
by one clock minute and all 199 replay checks passed. The study and
backtest add two counted `intraday_rebound` trials. This variant did
not use validation or sealed holdout data.

| Year | Trades | Net/trade 1× | Net/trade 2× | Net P&L 1× | Net P&L 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 1 | +31.46% | +31.33% | +$621 | +$618 |
| 2004 | 5 | +8.42% | +8.22% | +$839 | +$818 |
| 2005 | 4 | −6.52% | −6.76% | −$519 | −$538 |
| 2006 | 10 | +4.64% | +4.40% | +$928 | +$880 |
| 2007 | 24 | +5.28% | +4.89% | +$2,532 | +$2,343 |
| 2008 | 145 | +4.27% | +3.82% | +$12,257 | +$11,009 |
| 2009 | 20 | +0.33% | +0.02% | +$134 | +$9 |
| 2010 | 4 | +3.78% | +3.62% | +$302 | +$290 |
| 2011 | 14 | −2.04% | −2.32% | −$577 | −$653 |
| 2012 | 8 | +11.25% | +10.77% | +$1,800 | +$1,724 |
| 2013 | 9 | +5.11% | +4.82% | +$919 | +$866 |
| 2014 | 13 | +2.50% | +2.19% | +$654 | +$573 |
| 2015 | 19 | +4.52% | +4.26% | +$1,708 | +$1,609 |
| 2016 | 10 | −1.89% | −2.23% | −$399 | −$465 |
