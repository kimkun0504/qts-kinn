# Active-stock trading-gap recovery

## Verdict: park

The one frozen development definition produced no signals or events.
It fails every sample gate. There is no empirical return estimate,
and no evidence for a +3% mean trade. No portfolio or validation
run was authorized by the preregistered decision rule or performed.

The definition combined dense rising pre-gap trading, an absent
interval, a discounted reopening and initial recovery. Together
these conditions were too restrictive to yield a testable sample
on the permitted development period. No threshold is loosened
after observing this result.

## Run and attribution

- Run: `20261118T160358Z_gpt_active_gap_recovery_b8c628e9`,
  completed Kinn event study, 2003-09-10 through 2016-12-30.
- Hypothesis commit: `76a0292`; clean run commit: `b233b3b`.
  Agent `gpt`, branch `agent/gpt/active_gap_recovery`.
- Data build `447e58e098`, minute bars `65fa113929`;
  `ibkr_pro_tiered`, $20,000 account and $2,000 target.
- Family `intraday_rebound`: one additional trial, bringing
  the current total to 110 (101 counted run manifests plus nine
  earlier declared looks). Seventeen abandoned manifests remain
  preserved and are excluded by the registry's counting rule.
  The family began the original brief with 48 trials.

All numbers below are derived from this run's `manifest.json`,
`study.json` and empty `events.parquet`. No fresh price-data
query or scratch result supplies a metric.

## Frozen gates and results

| Requirement | Observed | Decision |
| --- | ---: | --- |
| At least 150 full-period events | 0 | Fail |
| At least 90 active dates | 0 | Fail |
| At least 40 events in 2013–2016 | 0 | Fail |
| Mean gross >= +3%, full and later block | Not estimable | No support |
| Positive stressed net, full and later block | Not estimable | No support |
| Positive full gross day-cluster lower bound | Not estimable | No support |

There are no completed events at either cost setting. Mean return,
conditional mean winner/loser, daily P&L t-statistic, confidence
interval and worst drawdown are not estimable. A zero-event dollar
series is not presented as a zero-risk strategy.

The study recorded zero lookahead replay checks because there were
no signals. Synthetic tests separately exercised every clock prefix
around qualifying events, a deliberately cheating future-price
filter, future-price/count perturbations, missing-minute boundaries,
distinct-company coverage and first qualifying event selection.
The focused strategy and repository checks passed, as did lint,
formatting and import contracts.

## By development year

| Year | Events | Net mean, 1× | Net mean, 2× | Event P&L, 1× / 2× |
| --- | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | $0 / $0 |
| 2004 | 0 | — | — | $0 / $0 |
| 2005 | 0 | — | — | $0 / $0 |
| 2006 | 0 | — | — | $0 / $0 |
| 2007 | 0 | — | — | $0 / $0 |
| 2008 | 0 | — | — | $0 / $0 |
| 2009 | 0 | — | — | $0 / $0 |
| 2010 | 0 | — | — | $0 / $0 |
| 2011 | 0 | — | — | $0 / $0 |
| 2012 | 0 | — | — | $0 / $0 |
| 2013 | 0 | — | — | $0 / $0 |
| 2014 | 0 | — | — | $0 / $0 |
| 2015 | 0 | — | — | $0 / $0 |
| 2016 | 0 | — | — | $0 / $0 |

## Data and execution limits

The bars have no halt status. An individual stock's missing bars
could be missing data, inactivity or an interruption; other-company
observations cannot distinguish these. This study establishes no
frequency of actual halts and no return after an actual halt.

The normal event-study model ignores entry expiry, per-bar
participation and account conflicts, estimates both cost legs
from the entry bar, and uses a horizon close instead of the
portfolio's timed exit open. No event existed on which to compare
those assumptions. Reopening spreads and depth remain unobserved.

Local source inspection showed that the existing SEC-time research
uses acceptance timestamps; a preceding press release remains
untimed. This candidate does not load filing-time files or news.
No new input, ingestion, build or platform change was made.

This is adaptive research after prior family outcomes and the
documented documentation-sample exposure. It does not restore
globally pristine validation. No validation or sealed-holdout
market data was loaded by this run. The rule stays parked.
