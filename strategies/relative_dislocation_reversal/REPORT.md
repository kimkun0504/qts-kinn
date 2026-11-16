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
