# Timed after-hours earnings discovery

## Verdict: park

The one frozen development rule failed the sample and return gates.
It produced 17 signals and 12 completed modeled events on 11 dates,
with −2.25% mean net at the after-hours base costs and
−2.81% at doubled slippage. No portfolio or validation run
was performed, and no signal or gate was tuned after the result.

The scoped timestamped input and its native replay/pinning support
are implemented and tested. Their implementation is useful
infrastructure, not evidence that this trading rule works.

## Run, costs and input provenance

- Run `20261118T222842Z_gpt_timed_earnings_discovery_8bc948c5`: completed Kinn event study,
  2003-09-10 through 2016-12-30.
- Hypothesis commit `f14f6fd`; prepared rule `7ec5686`;
  owner authorization recorded in `0a63cc1`; clean
  implementation/run commit `6678eb6`.
- Agent `gpt`, branch `agent/gpt/timed_earnings_discovery`,
  data build `447e58e098`.
- Pinned input `adba6fd432`, version `form8k-timed-1`,
  990,464 retained original 8-K records through 2023-11-08.
  The run manifest records an observed source archive envelope
  of 2003-02-04 through 2023-11-08; the earliest retained
  mapped filing is 2003-10-20. These are input coverage
  facts, not evidence of complete historical issuer coverage.
- Family `intraday_momentum`: one new trial, total
  176, including 174 earlier declared looks and
  the existing premarket study.
- Account/buying power $20,000; $2,000 target, ten reservations,
  5% participation, `ibkr_pro_tiered`.
- **After-hours base** uses 2× the regular marketable-slippage
  fallback. **Doubled-slippage stress** uses 4× that regular
  fallback. Fees stay the same. Both use the same inferred
  capped opening fills, feasible in the model at both costs.

## Frozen gates

| Requirement | Observed | Decision |
| --- | --- | --- |
| 150 completed events on 90 dates overall | 12 on 11 dates | Fail |
| 40 events in 2013–2016 | 5 on 5 dates | Fail |
| Gross mean >= +3% in both blocks | −1.59% full; −0.34% later | Fail |
| Positive stressed mean net in both blocks | −2.81% full; −1.36% later | Fail |
| Positive full gross day-cluster lower bound | −3.80% | Fail |
| Zero unresolved positions and no regular-hours exit | Both met in the model | Pass |

Five signals never filled. The modeled completed-event fraction
was 70.6%; this is not an observed broker fill rate.
Every filled entry occurred in its sole permitted next clock minute.
There were zero modeled unresolved positions and zero regular-session
exits. The longest modeled hold was 33 minutes, with the
registered timed liquidation allowed to retry after its deadline.
The run recorded 16 signal-day replay checks.

## Completed-event diagnostics

| Window | Events | Active dates | Gross mean | Net, base | Net, doubled slippage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 12 | 11 | −1.59% | −2.25% | −2.81% |
| 2013–2016 | 5 | 5 | −0.34% | −0.89% | −1.36% |

| Full development | After-hours base | Doubled slippage |
| --- | ---: | ---: |
| Total modeled event P&L | −$519 | −$650 |
| Daily P&L t-statistic | -1.48 | -1.72 |
| Worst end-of-day drawdown | −$532 | −$650 |
| 95% day-clustered interval for mean net | −4.47% to +0.17% | −5.08% to −0.42% |
| Winners | 4 | 3 |
| Mean winner | +1.82% | +1.69% |
| Losers | 8 | 9 |
| Mean loser | −4.28% | −4.30% |

The full gross day-clustered interval is −3.80%
to +0.83%. Mean actual modeled event notional
was $1,953. Mean round-trip fees were
+0.09% of notional and after-hours base slippage
+0.56%. The sample is small and its interval
does not repair the failed sample gates.

Daily P&L sums each completed event's actual modeled net dollars
over all trading sessions in the run manifest, including zero-event
dates. Drawdown is cumulative dollar P&L below its prior peak,
including the initial zero. The study applies the extended fill,
expiry, participation and liquidation model per event. It does
not apply concurrent account-capital conflicts. These are
independent-event diagnostics, not a tested account portfolio.

## Development results by year

| Year | Completed events | Net mean, base | Net mean, doubled slippage | Event P&L, base | Event P&L, doubled slippage |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | $0 | $0 |
| 2004 | 0 | — | — | $0 | $0 |
| 2005 | 1 | −3.21% | −3.66% | −$63 | −$72 |
| 2006 | 4 | −5.57% | −6.18% | −$428 | −$475 |
| 2007 | 0 | — | — | $0 | $0 |
| 2008 | 0 | — | — | $0 | $0 |
| 2009 | 2 | +1.50% | +0.76% | $59 | $30 |
| 2010 | 0 | — | — | $0 | $0 |
| 2011 | 0 | — | — | $0 | $0 |
| 2012 | 0 | — | — | $0 | $0 |
| 2013 | 2 | −2.56% | −3.04% | −$99 | −$118 |
| 2014 | 0 | — | — | $0 | $0 |
| 2015 | 2 | +0.84% | +0.29% | $33 | $12 |
| 2016 | 1 | −1.01% | −1.30% | −$20 | −$26 |

## Availability and bias checks

The owner authorized only the scoped new input and derived build.
No bar or panel was rebuilt, nothing was downloaded or written
to raw, and no sealed directory was accessed. All empirical
strategy metrics above derive from this run's manifest,
study summary and r_30 event rows. No validation market dates
were loaded by the study.

The builder reads the existing SEC archive and identity fields,
rejects timestamps without explicit offsets, and rejects both
post-seal filing and post-seal local acceptance dates. Each
accession retains its own items. Ambiguous CIK/security mappings
and conflicting accessions are excluded; older item formats
are rejected rather than guessed into modern earnings codes.
These exclusions reduce coverage. The observed source date
envelope does not prove completeness for any issuer.

At bar-prefix replay the native view hides filings until their
registered usable minute. Tests cover UTC offsets/DST and seconds,
the one-complete-minute delay, native view truncation, separate
accession items, conflicting/unknown identities, misbuilt future
timestamps, point-in-time traded symbols, input id/hash pinning,
resume and spawned workers. Sweeps now also pin input ids and
refuse mixed input sets. Existing date-only input semantics
remain intact. The full test suite, lint, formatting and import
contracts passed before the research run.

## Material execution and interpretation limits

SEC acceptance is public-by time for the filing. An earlier press
release may already have moved the stock. This study does not
measure the first earnings publication or an earnings surprise.

Minute bars contain no observed quotes, depth or order latency.
In `minute_open_proxy-1`, the execution bar's later range and
volume can change whether an opening fill is accepted under a
cap. That is a selection assumption as well as cost uncertainty.
The manifest records it; successful signal replay does not
certify those fills. There is no quote/trade verification here.

The hypothesis was registered after prior adaptive research
and the documented documentation-sample exposure. Later-period
results for other rules remain known; a new frozen rule does
not restore globally pristine validation. This failed rule
receives no later-period retry and stays parked.
