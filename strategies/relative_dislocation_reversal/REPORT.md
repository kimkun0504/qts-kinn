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
