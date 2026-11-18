# Opening discount to an active premarket reference

**Verdict: park.** The frozen rule generated no qualifying
signals and no filled events in the development period. There
is no mean return, daily P&L t-statistic, drawdown or conditional
win/loss estimate at either cost setting. It fails the minimum
sample gates and cannot advance to a portfolio or validation run.
No thresholds or holding periods were changed after this result.

Run `20261118T140603Z_gpt_auction_gap_repair_d1e5628c` covered 2003-09-10 through
2016-12-30 on build `447e58e098`, from clean
commit `f5224f28`. Hypothesis commit `2434f8f`
preceded implementation and every empirical run. This is one
charged `intraday_rebound` trial; the current shared count is
107, including nine earlier declared looks. The family began
this program with 48 trials. Related research is acknowledged
in HYPOTHESIS.md and supplies no fresh evidence for this rule.

## Results against the frozen bars

| Measurement | Base slippage | Doubled slippage |
|---|---:|---:|
| Signals | 0 | 0 |
| Filled events / completed trades | 0 / 0 | 0 / 0 |
| Mean gross / net return | N/A | N/A |
| Daily P&L t-statistic | N/A | N/A |
| Worst drawdown | N/A | N/A |
| Mean winner / mean loser | N/A | N/A |

The registration required 150 completed events on 90 dates
and 40 events in 2013–2016, +3% mean gross and positive stressed
net in both windows, with a positive full-sample lower gross
confidence bound. Neither window contained a signal. The
stored outputs do not say which individual filter prevented
eligibility; no extra market-data query was used to infer that.
A zero-event series offers no risk or return estimate.

## Annual development results

| Year | Signals | Filled events | Net/event 1× | Net/event 2× |
|---|---:|---:|---:|---:|
| 2003 | 0 | 0 | N/A | N/A |
| 2004 | 0 | 0 | N/A | N/A |
| 2005 | 0 | 0 | N/A | N/A |
| 2006 | 0 | 0 | N/A | N/A |
| 2007 | 0 | 0 | N/A | N/A |
| 2008 | 0 | 0 | N/A | N/A |
| 2009 | 0 | 0 | N/A | N/A |
| 2010 | 0 | 0 | N/A | N/A |
| 2011 | 0 | 0 | N/A | N/A |
| 2012 | 0 | 0 | N/A | N/A |
| 2013 | 0 | 0 | N/A | N/A |
| 2014 | 0 | 0 | N/A | N/A |
| 2015 | 0 | 0 | N/A | N/A |
| 2016 | 0 | 0 | N/A | N/A |

All annual t-statistics and drawdowns are unavailable. These
counts come from the run's stored part counts, `study.json`
and empty `events.parquet`. No return has been imputed.

## Implementation and interpretation

The share-volume-weighted median, lower-half convention,
reference freshness and turnover gates, inclusive price
boundaries, early-close exclusion, prefix replay and isolated
CLI load passed synthetic tests. Execution tests confirmed
next-minute capped entry and a matching study/portfolio timed
exit policy. Repository rules, execution regressions, Ruff and
import contracts passed. No empirical prefix replay was triggered
because the strategy emitted no signal.

The candidate entered only at 09:31 and intended liquidation
at 10:01, with $2,000 targets on a $20,000 account. It used the
capped profile at ordinary `ibkr_pro_tiered` baseline slippage,
with doubled slippage required to remain inside the same caps.
Any unresolved or after-hours exit would have failed advancement.
There were no positions, unfilled orders or unresolved shares.

The opening minute's low was never assumed attainable. The
premarket reference summarizes minute closes weighted by bar
share volume and does not establish fair value or executable
quotes. The execution model estimates spread and impact from
minute aggregates. The full execution bar's range and volume
also affect cap-related fill inference, so signal replay alone
cannot verify the realism of an opening fill. Quotes and depth
remain unverified. No raw writes, rebuilds, downloads, validation
market data or sealed dates were used.

This trial establishes that the exact definition is too sparse
in the registered development data. It does not demonstrate a
profitable opening-repair effect or rule out all such effects.
