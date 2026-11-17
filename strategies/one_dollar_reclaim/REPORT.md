# One-dollar reclaim

## Verdict

Park. The primary $1.00 reference produced 75 events on 72 dates
against a minimum of 150 events on 90 dates. Its 2013–2016
block produced 25 events, below 40. Mean gross return was +1.21%
overall and +2.64% in 2013–2016, below the +3% hurdle. Both
windows lost at doubled slippage and the full-period gross
confidence interval crossed zero. The primary failed the
development gates.

The registered $1.20 comparison produced 73 events with a
negative gross mean. The definitions selected different stocks
and dates, with no overlapping security-days and eight shared
dates. Their price and liquidity exposures can differ, so the
return difference cannot identify a causal dollar-level effect.

## Runs

- Primary `20261117T193819Z_gpt_one_dollar_reclaim_ce3fd011`, config `development`.
- Comparison `20261117T193851Z_gpt_one_dollar_reclaim_6af7b00e`, config `development_comparison`.
- Both studies used 2003-09-10 through 2016-12-30, build
  `447e58e098`, and clean commit `c060213`. Hypothesis
  commit `0d97a0d` preceded both. Implementation was resumed
  from its unrun drafts after the VWAP studies had finished,
  using the original definition and gates.
- These add two counted `intraday_rebound` trials. The
  shared family count at reporting is 103,
  including nine earlier declared looks. The primary and
  comparison each passed 72 lookahead replays.

## Development to the close

| Group and window | Events | Active dates | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| $1.00, full development | 75 | 72 | +1.21% | −1.63% | −3.12% |
| $1.00, 2013–2016 | 25 | 23 | +2.64% | −0.13% | −1.56% |
| $1.20, full development | 73 | 72 | −0.98% | −3.74% | −5.38% |
| $1.20, 2013–2016 | 20 | 19 | −4.01% | −6.43% | −7.73% |

| Full-period 95% day-clustered interval | $1.00 | $1.20 |
| --- | ---: | ---: |
| Gross mean | −1.13% to +3.86% | −3.33% to +1.67% |
| Net mean at 1× | −3.96% to +1.01% | −6.05% to −1.10% |
| Net mean at 2× | −5.48% to −0.49% | −7.72% to −2.73% |

Average round-trip costs at 1× were
+2.84% for the primary and
+2.76% for the comparison.
Per-share commissions and fees become a large fraction of value
at these price levels. Both cases use IBKR Pro Tiered fees.
The stress case doubles modeled slippage on the same events.

## Order expiry

The event study counts the first observed bar after a decision.
It counted two primary and two comparison entries after the
order would have expired. The next-minute subset also fails.

| Entries within expiry | Events | Active dates | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| $1.00, full development | 73 | 70 | +1.16% | −1.67% | −3.16% |
| $1.00, 2013–2016 | 24 | 22 | +2.66% | −0.09% | −1.50% |
| $1.20, full development | 71 | 70 | −0.98% | −3.76% | −5.42% |
| $1.20, 2013–2016 | 20 | 19 | −4.01% | −6.43% | −7.73% |

## Independent event P&L

| Group and cost | Daily P&L t-statistic | Worst end-of-day drawdown | Total modeled net P&L |
| --- | ---: | ---: | ---: |
| $1.00, 1× | −1.20 | −$2,594 | −$2,444 |
| $1.00, 2× | −2.21 | −$4,686 | −$4,686 |
| $1.20, 1× | −2.83 | −$6,310 | −$5,456 |
| $1.20, 2× | −3.88 | −$8,413 | −$7,850 |

These dollar series sum independent $2,000-target hypothetical
positions across all 3,352 development sessions, including
zero-event dates. About
57% of primary target sizes
and 64% of comparison
target sizes exceeded 5% of entry-bar volume. Portfolio fills
would be subject to account and participation constraints.
The study measures gross return to the official close where
available and estimates both marketable cost legs from the
entry bar. The registered portfolio would exit in the closing
auction.

## Annual development results

| Year | $1.00 events | $1.00 net at 1× | $1.00 net at 2× | $1.20 events | $1.20 net at 1× | $1.20 net at 2× |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | 2 | +1.57% | −0.79% |
| 2004 | 1 | −1.65% | −2.95% | 1 | +1.89% | −0.02% |
| 2005 | 3 | −2.19% | −3.43% | 2 | −2.06% | −3.46% |
| 2006 | 1 | +1.25% | −0.12% | 0 | — | — |
| 2007 | 1 | −7.70% | −9.10% | 1 | −8.08% | −9.89% |
| 2008 | 13 | −2.22% | −4.20% | 19 | −3.67% | −5.49% |
| 2009 | 20 | −1.19% | −2.61% | 21 | −0.72% | −2.38% |
| 2010 | 3 | −7.52% | −8.95% | 2 | −5.29% | −7.40% |
| 2011 | 6 | −6.02% | −7.32% | 4 | −10.54% | −12.43% |
| 2012 | 2 | +3.51% | +2.35% | 1 | +0.38% | −0.66% |
| 2013 | 2 | +35.33% | +33.88% | 3 | −7.40% | −8.67% |
| 2014 | 6 | −8.52% | −9.87% | 1 | −4.21% | −5.67% |
| 2015 | 6 | −1.40% | −2.68% | 2 | −9.54% | −10.59% |
| 2016 | 11 | −1.31% | −2.85% | 14 | −5.93% | −7.27% |

The primary's two 2013 events averaged
+35.33% net at base costs.
Excluding that year as a descriptive concentration check,
the remaining 73
events averaged −2.64% at base costs.
This check does not change the preregistered decision.

## Checks and limits

Strategy tests cover absolute price thresholds, the recent
intraday break, the actual preceding clock minute, first signal,
prefix replay, next-minute expiry, same-day auction exit and
the proportional comparison. Strategy tests, lookahead canaries,
repository rules, Ruff and the import contracts passed.

The bars cannot establish clustered orders, exchange-specific
compliance or the motivations behind the crossing. The results
support parking this definition. Portfolio testing and validation
were skipped, and the holdout stayed sealed.
