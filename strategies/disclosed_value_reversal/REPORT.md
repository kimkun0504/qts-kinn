# Intraday reversal with a recently disclosed insider purchase

## Verdict: park

The primary produced 72 development events on 66 dates,
averaging +1.59% net at base costs and +1.01%
at doubled slippage at the registered r_120 horizon. Its later
development block had 17 events, with +1.40% base and
+0.94% stressed. It fails the required sample counts and
the +3% gross-mean gates in both windows. No portfolio or validation
run was made.

The selector improves the descriptive mean over its same-event control
in both windows. That is a narrower finding than an eligible alpha:
the sample is too small and the registered payoff too low. No dollar
floor, lookback, liquidity subgroup, holding horizon or date was changed
to rescue it. The control cannot replace the primary.

## Registered runs and sources

| Variant | Run ID | Events | Dates | Signal-day replays |
| --- | --- | ---: | ---: | ---: |
| Primary | `20261119T220741Z_gpt_disclosed_value_reversal_5b20f5b2` | 72 | 66 | 66 |
| Control | `20261119T221034Z_gpt_disclosed_value_reversal_20c0c123` | 1786 | 970 | 970 |

Hypothesis commit `58cfda5` preceded both studies. They used clean
implementation commit `fa9c9e25`, agent gpt, build `447e58e098`,
2003-09-10..2016-12-30, `ibkr_pro_tiered`, $20,000 account and $2,000
target. Both manifests are complete and nonscratch and pin Form 4 input
`fe7c80978b` / `form4-1`. Its source ends on 2023-09-29.
Both variants deliberately begin eligible signals on 2006-02-01 after
a complete twenty-session archive window; earlier dates are not a
claim of observed absence of purchases.

Two empirical trials raise `intraday_rebound` from 116 to 118,
including nine pre-registry looks. Related insider swing, opening
confirmation, disclosed-price reclaim and reversal work remain prior
research. This is not an independent first look.

## Preset gate assessment and matching

Every primary event exactly matches a control event on company/date,
signal minute, entry minute, shares, price, fees, slippage and r_120.
The completed-run audit matched all 72 rows before the final gate assessment. The pre-open filing
selector leaves all otherwise eligible peers in the price reference
and cannot select a more favorable later signal.

| Primary gate | Observation | Decision |
| --- | --- | --- |
| 150 events on 90 dates | 72 on 66 | Fail |
| 40 events in 2013–2016 | 17 | Fail |
| Gross mean >= +3%, full and later | +2.42% / +2.05% | Fail |
| Positive stressed mean, both windows | +1.01% / +0.94% | Pass |
| Positive full 95% gross lower bound | +0.43% | Pass |
| Stressed mean above control, both windows | Higher in both | Pass |

The positive criteria do not override the failed ones. Confidence
intervals are ordinary descriptive estimates and do not adjust for
the extensive adaptive family search.

## Registered r_120 diagnostics

| Window | Events | Dates | Gross mean | Mean net 1× | Mean net 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary full | 72 | 66 | +2.42% | +1.59% | +1.01% |
| Primary 2013–2016 | 17 | 17 | +2.05% | +1.40% | +0.94% |
| Control full | 1786 | 970 | +1.62% | +0.70% | +0.07% |
| Control 2013–2016 | 483 | 329 | +0.72% | −0.12% | −0.68% |

| Full development | Primary 1× | Primary 2× | Control 1× | Control 2× |
| --- | ---: | ---: | ---: | ---: |
| Sum of event P&L | $2,281 | $1,453 | $24,862 | $2,357 |
| Daily P&L t-statistic | 1.53 | 0.98 | 2.37 | 0.23 |
| Worst end-of-day drawdown | −$868 | −$1,021 | −$3,916 | −$11,853 |
| Winners | 45 | 44 | 998 | 926 |
| Mean winner | +6.41% | +5.99% | +7.01% | +6.93% |
| Losers | 27 | 28 | 788 | 860 |
| Mean loser | −6.45% | −6.81% | −7.30% | −7.32% |

Primary gross whole-day 95% bootstrap interval: +0.43%
to +4.41%; control: +1.04% to +2.18%.
Use the native 2,000 resamples and seed zero. The later primary's
seventeen dates remain inadequate for the required gate.

The primary has no late entries. Control has 6 overall and
3 in 2013–2016. The on-time control has
1780 events at +0.71% base and
+0.08% stressed; later it has
480 at −0.13% and
−0.69%. The primary still fails its sample and gross-return
gates in the required on-time sensitivity; both incremental
stressed-mean comparisons still pass.

19 primary target orders exceed 5% of entry-bar volume,
including 3 later; the control has
275, including 59 later.
The study ignores these limits, capital conflicts and order expiry.
Its P&L is independent-event arithmetic, not a simulated account.
Daily P&L sums net fraction × shares × entry price over every manifest
session, with zero-event sessions included. Drawdown includes initial
zero. Fees/slippage in saved rows are return fractions; stress doubles
only slippage. Study horizon closes also differ from portfolio exit opens.

## Annual results

| Year | Primary events | Primary mean 1× | Primary mean 2× | Control events | Control mean 1× | Control mean 2× |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | 0 | — | — |
| 2004 | 0 | — | — | 0 | — | — |
| 2005 | 0 | — | — | 0 | — | — |
| 2006 | 8 | −5.43% | −6.01% | 82 | −0.02% | −0.59% |
| 2007 | 6 | +1.12% | +0.83% | 144 | +2.20% | +1.64% |
| 2008 | 25 | +4.76% | +4.08% | 605 | +1.29% | +0.56% |
| 2009 | 5 | +5.87% | +5.28% | 184 | +0.10% | −0.56% |
| 2010 | 3 | +2.69% | +2.05% | 78 | +1.48% | +0.85% |
| 2011 | 6 | −4.33% | −5.14% | 119 | +0.25% | −0.33% |
| 2012 | 2 | −1.51% | −1.94% | 91 | +0.54% | −0.01% |
| 2013 | 3 | +1.74% | +1.27% | 90 | +0.72% | +0.15% |
| 2014 | 4 | −1.92% | −2.36% | 104 | −0.26% | −0.74% |
| 2015 | 5 | +2.07% | +1.77% | 147 | −0.47% | −1.01% |
| 2016 | 5 | +3.17% | +2.56% | 142 | −0.20% | −0.82% |

| Year | Primary event P&L 1× | Primary event P&L 2× | Control event P&L 1× | Control event P&L 2× |
| --- | ---: | ---: | ---: | ---: |
| 2003 | $0 | $0 | $0 | $0 |
| 2004 | $0 | $0 | $0 | $0 |
| 2005 | $0 | $0 | $0 | $0 |
| 2006 | −$868 | −$961 | −$39 | −$973 |
| 2007 | $133 | $98 | $6,328 | $4,711 |
| 2008 | $2,375 | $2,038 | $15,556 | $6,726 |
| 2009 | $587 | $528 | $357 | −$2,051 |
| 2010 | $162 | $123 | $2,303 | $1,314 |
| 2011 | −$520 | −$617 | $584 | −$794 |
| 2012 | −$61 | −$78 | $977 | −$20 |
| 2013 | $104 | $76 | $1,299 | $273 |
| 2014 | −$154 | −$189 | −$561 | −$1,546 |
| 2015 | $208 | $177 | −$1,370 | −$2,954 |
| 2016 | $316 | $256 | −$572 | −$2,331 |

## Software checks, source limits and next decision

Focused strategy, repository and native Form 4 checks passed, as did
Ruff and all five import contracts. Tests cover original P/acquired
roles, fixed materiality, deduplication without summing, conflicting
valid filings and issuers, invalid/future records, archive warmup,
absence of a purchase-price reference, all-peer membership, exact
first price events, every-prefix replay, an intentional future-price
canary, next-minute expiry and time/auction exits.

The filing date provides conservative next-session availability.
Twenty-session slicing is supplied by the native input. P records can
include private/planned purchases; footnotes and amendments are not
resolved. Ticker matching cannot rule out every reuse or rename.
The one-month signal may be stale. Snapshot categories/cap, corporate
actions, unmeasured quotes/latency and bar execution limitations remain.

Because development fails, no Form 4 extension is requested for this
candidate, no validation date is shortened, and no later data is used.
A public-information selector improved these point estimates, but
this result does not establish informed trading, a causal effect,
a reliable live return or an eligible +3% alpha.

All empirical numbers derive from the two registered run-store studies
and their saved r_120 rows. No scratch performance, new raw acquisition
or write, rebuild, platform change, validation or post-seal market query
was used. No selected stock/date/liquidity/holding-time subset advances.
