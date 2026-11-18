# Filing-aware dislocation reversal

## Development study decision

Develop to the registered portfolio check. The study passed every
preregistered gate. It recorded 257 events on 178 dates, including
45 events in 2013–2016. Mean two-hour gross return exceeded +3%
overall and in the later block. Mean stressed return was positive
in both windows and the full-period lower gross confidence bound
was positive. All entries were on the next clock minute.
This decision authorizes the registered development portfolio
check. That run will determine whether the strategy meets the
portfolio return, sample and risk gates.

The filing screen had a small effect on the overall average and
removed profitable events. Its later development mean was lower
than the stored unfiltered study. Passing the event gate does
not establish that the screen improved the signal.

## Study and comparison

- Run `20261118T011256Z_gpt_filing_aware_dislocation_2df4fa72`, event study on 2003-09-10 through
  2016-12-30. Hypothesis commit `2fc79ef`, clean run commit
  `8ea6ead`, data build `447e58e098`.
- Form 8-K input `2578b76aa1`, version
  `form8k-1`. Kinn exposes filings strictly before
  the entry session. Current-session news remains unobserved.
- One counted `intraday_rebound` study, bringing the shared
  family total to 104 including nine earlier
  declared looks. The saved baseline was
  `20261116T212516Z_gpt_relative_dislocation_reversal_eb5399da`.
- Every retained event matched that baseline exactly on security,
  date, decision minute, entry minute, shares, entry price,
  costs and two-hour return. The peer basket remains unchanged.
  Kinn passed 178 lookahead replays.

| Two-hour event outcome | Events | Active dates | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unfiltered, full development | 291 | 199 | +4.33% | +3.62% | +3.16% |
| Retained, full development | 257 | 178 | +4.36% | +3.65% | +3.19% |
| Removed, full development | 34 | 33 | +4.11% | +3.36% | +2.91% |
| Unfiltered, 2013–2016 | 51 | 46 | +3.36% | +2.81% | +2.49% |
| Retained, 2013–2016 | 45 | 41 | +3.07% | +2.52% | +2.19% |
| Removed, 2013–2016 | 6 | 6 | +5.55% | +5.03% | +4.68% |

| Filtered full-period study | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| 95% day-clustered interval for mean net | +1.67% to +5.53% | +1.21% to +5.05% |
| Daily P&L t-statistic | 3.34 | 3.00 |
| Worst end-of-day drawdown | −$1,522 | −$1,709 |
| Total modeled net P&L | +$18,724 | +$16,360 |

The gross interval was +2.37% to +6.30%. Dollar statistics sum
independent target orders over all 3,352 development sessions,
including zero-event days. About
2% of targets exceeded
5% of their entry-bar volume. Capital and exit execution will
be checked by the registered portfolio run. Study costs use
entry-bar conditions for both marketable legs, whereas the
portfolio models each fill and uses the actual exit bar.
Both cost cases retain IBKR Pro Tiered fees.

## Annual study results at two hours

| Year | Events | Net mean at 1× | Net mean at 2× | Net P&L at 1× | Net P&L at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 1 | +31.49% | +31.38% | +$622 | +$619 |
| 2004 | 4 | +8.69% | +8.40% | +$694 | +$671 |
| 2005 | 4 | −6.56% | −6.83% | −$525 | −$546 |
| 2006 | 9 | +3.68% | +3.39% | +$659 | +$607 |
| 2007 | 21 | +4.87% | +4.46% | +$2,037 | +$1,865 |
| 2008 | 133 | +4.56% | +3.98% | +$12,090 | +$10,553 |
| 2009 | 18 | +0.56% | +0.24% | +$203 | +$88 |
| 2010 | 3 | +2.81% | +2.60% | +$164 | +$152 |
| 2011 | 11 | −4.64% | −4.92% | −$1,020 | −$1,081 |
| 2012 | 8 | +9.59% | +9.11% | +$1,532 | +$1,455 |
| 2013 | 8 | +4.47% | +4.12% | +$718 | +$662 |
| 2014 | 13 | +2.46% | +2.14% | +$642 | +$557 |
| 2015 | 16 | +4.32% | +4.02% | +$1,379 | +$1,282 |
| 2016 | 8 | −2.96% | −3.29% | −$471 | −$525 |

## Tests and limits

The definition and runtime checks cover exact price endpoints,
synchronous peers, size groups, report date and identity,
filing visibility, the full benchmark including excluded peers,
prefix replay, next-minute expiry, the two-hour exit and auction
fallback. Strategy tests, the Form 8-K input tests, repository
rules, lookahead canaries, Ruff and the import contracts passed.

An available filing can be routine. A security without a newly
available typed filing can still have important current news.
This screen measures a filing label under the platform's
availability rule. The family has already read the validation
years for other definitions. Any later qualifying test will
use the frozen registration and must acknowledge that reuse.
The holdout stays sealed.
