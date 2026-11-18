# Closing unwind and impact decay

**Verdict: park.** The frozen rule produced 1 signal and
0 filled events in development. The entry did not execute
within its registered lifetime and capped-price contract. There
is no measured mean return, daily P&L t-statistic, drawdown,
mean winner or mean loser at either cost setting. The sample
gates fail. No development portfolio or validation run is allowed
by the registration, and neither was run.

Run `20261118T135113Z_gpt_close_unwind_impact_decay_a11cb669` used 2003-09-10 through
2016-12-30, data build `447e58e098` and clean
commit `7bb539e9`. The hypothesis was committed
at `e3463b5` before implementation or empirical testing. The
owner-authorized execution clarification was committed at
`14bfa93` before the run. This is one new charged trial in
`intraday_rebound`, bringing the shared family count to 106,
including nine declared earlier looks. The family began this
research with 48 trials. Claude's related after-hours research
is acknowledged in the hypothesis and is not a result for this
candidate.

## Results against the frozen bars

| Development measurement | 1× extended baseline | 2× extended slippage |
|---|---:|---:|
| Filled events / completed trades | 0 / 0 | 0 / 0 |
| Mean gross / net return | N/A | N/A |
| Daily event P&L t-statistic | N/A | N/A |
| Worst drawdown | N/A | N/A |
| Mean winner / mean loser | N/A | N/A |

The gate required 150 events on 90 dates, including 40 events
in 2013–2016. There were no filled events in either development
window. The positive-mean and confidence-bound requirements
therefore cannot pass. No positions remained unresolved because
there were no entries. A prefix replay passed for the signal
session. The stored month-level counts place the single signal
in 2009-05. The run store does not retain an unfilled order's
minute or rejection reason, so the output cannot distinguish a
missing eligible bar from a cap or capacity rejection. No new
market-data query was used to infer that reason.

## Annual development results

| Year | Signals | Unfilled | Filled events | Net/event 1× | Net/event 2× |
|---|---:|---:|---:|---:|---:|
| 2003 | 0 | 0 | 0 | N/A | N/A |
| 2004 | 0 | 0 | 0 | N/A | N/A |
| 2005 | 0 | 0 | 0 | N/A | N/A |
| 2006 | 0 | 0 | 0 | N/A | N/A |
| 2007 | 0 | 0 | 0 | N/A | N/A |
| 2008 | 0 | 0 | 0 | N/A | N/A |
| 2009 | 1 | 1 | 0 | N/A | N/A |
| 2010 | 0 | 0 | 0 | N/A | N/A |
| 2011 | 0 | 0 | 0 | N/A | N/A |
| 2012 | 0 | 0 | 0 | N/A | N/A |
| 2013 | 0 | 0 | 0 | N/A | N/A |
| 2014 | 0 | 0 | 0 | N/A | N/A |
| 2015 | 0 | 0 | 0 | N/A | N/A |
| 2016 | 0 | 0 | 0 | N/A | N/A |

Every annual mean, t-statistic and drawdown is unavailable.
A zero-event series supplies no estimate of strategy risk or
return. All counts above come from the run's stored part files,
`study.json` and `events.parquet`. These are event-study results;
an executable account portfolio was not measured.

## Execution and limitations

The opt-in `extended_v1` implementation is owner-authorized and
recorded in OWNERS.md. It uses the existing minute build and
preserves the regular-session defaults. The entry target is
$2,000 on a $20,000 account, with ten reservations or positions
and a five-percent bar participation cap. Buy orders expire
after their one eligible clock minute. Liquidation starts at
fifteen minutes and retries capped sell limits. Each filled
replacement pays its own commission minimum. No regular-session
auction price can settle an after-hours position.

The extended baseline doubles `ibkr_pro_tiered` spread and
impact estimates; the reported stress doubles that baseline
again. Both modeled execution prices must fit their caps.
Unresolved shares stay visible and invalidate advancement.
The full minute's volume and range approximate execution;
there are no quotes or depth observations establishing an
attainable opening fill. The formula measures down-closing
turnover, not identified sellers or signed order flow.

The repository suite, focused execution tests, Ruff and import
contracts passed. Synthetic integration tests cover complete
and unresolved positions in both study and portfolio modes,
including expiry, gaps, partial fills, retries, capital and
commission accounting. The first CLI launch failed during a
helper import before creating a run; an isolated-load test now
covers that path and the candidate is self-contained in
`strategy.py`. No empirical result was obtained from that
failed launch. A subsequent reporting-only correction makes
empty studies show their signal funnel and avoids advertising
unmeasured horizons. The original run outputs are retained.

The current sealed period and the owner's motivating live
example were not inspected. There was no data rebuild or raw
write. This trial provides evidence that this exact rule is
too sparse to evaluate in the registered development data.
It establishes no conclusion about all after-hours strategies.
