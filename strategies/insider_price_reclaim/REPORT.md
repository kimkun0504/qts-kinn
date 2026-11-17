# Insider purchase price reclaim

## Verdict

Park. The study measured 36 events on 36 dates against the
preregistered minimum of 150 events on 90 dates. The 2013–2016
block produced 13 events against a minimum of 40. Gross return
to the close averaged +0.06% against a +3% hurdle. The
day-clustered gross interval crossed zero. Mean returns after
costs were negative in both development windows. No portfolio or
validation run was warranted under the preregistered sequence.

## Run

- `20261117T140552Z_gpt_insider_price_reclaim_d71c49eb`, development event study, 2003-09-10 through
  2016-12-30. Hypothesis commit `716cbc2`, clean run commit
  `ebac6cd`, data build `447e58e098`.
- Form 4 input `fe7c80978b`, version `form4-1`.
  The installed input ends on 2023-09-29. It covers the registered
  development dates from its 2006 start. October and early November
  2023 filings would be needed for full validation.
- One new trial in `intraday_rebound`. The shared count at
  reporting is 93, including 9
  declared earlier looks.
- Kinn recorded 36 successful lookahead replays. The
  measured events span 34 distinct security
  identifiers, with at most 2
  events per identifier.

| Development window | Events | Sessions with events | Gross mean | Net mean at 1× | Net mean at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 36 | 36 | +0.06% | −0.39% | −0.70% |
| 2013–2016 | 13 | 13 | −0.09% | −0.58% | −0.89% |
| Next-minute entries only | 35 | 35 | +0.07% | −0.39% | −0.69% |
| 2013–2016, next-minute entries only | 12 | 12 | −0.08% | −0.58% | −0.90% |

The event study measures the first observed bar after a signal.
It counted one entry two minutes after the decision. The
registered order would have expired before that print. The
next-minute subset also misses the sample, return and confidence
gates. Its 95% day-clustered gross interval was
−1.25% to +1.50%.

| Full development | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| 95% day-clustered interval for mean net | −1.65% to +1.00% | −1.98% to +0.71% |
| Daily P&L t-statistic | −0.57 | −0.99 |
| Worst end-of-day drawdown | −$643 | −$787 |
| Total modeled net P&L | −$281 | −$500 |

The full-period 95% day-clustered interval for gross mean return
was −1.16% to +1.44%. The study approximates both marketable legs using
the entry bar, with official close used for gross exit valuation
when available. Both cost cases use the same IBKR Pro Tiered
fees. Daily P&L includes all 3,352
sessions and sums the independent event outcomes at the study's
target sizes. About 58%
of those sizes exceeded 5% of their entry bar's volume. These
risk figures describe the event series. Actual position
sizing, portfolio limits and auction fills would require a
portfolio run.

## Development by year

| Year | Events | Net mean at 1× | Net mean at 2× | Net P&L at 1× | Net P&L at 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | — | — |
| 2004 | 0 | — | — | — | — |
| 2005 | 0 | — | — | — | — |
| 2006 | 1 | −0.76% | −1.49% | −$15 | −$30 |
| 2007 | 7 | +1.54% | +1.36% | +$216 | +$191 |
| 2008 | 8 | −0.51% | −0.80% | −$82 | −$129 |
| 2009 | 2 | −3.17% | −3.35% | −$126 | −$133 |
| 2010 | 1 | +1.52% | +1.25% | +$30 | +$25 |
| 2011 | 4 | −1.94% | −2.43% | −$155 | −$194 |
| 2012 | 0 | — | — | — | — |
| 2013 | 1 | −1.10% | −1.32% | −$22 | −$26 |
| 2014 | 6 | −0.51% | −0.82% | −$61 | −$98 |
| 2015 | 3 | +1.41% | +1.16% | +$84 | +$69 |
| 2016 | 3 | −2.51% | −2.92% | −$151 | −$175 |

## Limits

The reported dollars per share can mix purchases from different
dates or terms and can be depressed by shares on unpriced lines.
The stock could recover for reasons unrelated to the filing.
Kinn's stock identity field identifies a security. A separate
issuer-level concentration estimate would require identity data
in the study output. The test supports parking this rule. The
2017–2023 validation window and the sealed holdout remain untouched
by this trial.

Tests cover filing availability, selection of the price reference,
the washout and recovery sequence, prefix replay, next-minute
expiry and same-session auction exit.
