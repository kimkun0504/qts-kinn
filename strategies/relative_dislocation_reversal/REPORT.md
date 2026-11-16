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
