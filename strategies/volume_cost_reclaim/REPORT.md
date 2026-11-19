# Recovery above a volume-weighted bar-high reference

## Verdict: park

The primary produced 4 development events on 4 dates,
averaging −6.87% net at base costs and −7.48%
with doubled slippage at the registered r_120 horizon. It had no
events in 2013–2016. The sample, return, confidence and incremental
improvement gates fail. The bar-high reference was far too selective
for this candidate and did not improve the realized outcome.

The control produced 842 events on 497 dates,
averaging +1.25% net at base and +0.89% stressed.
Its later block was +0.27% base and −0.01% stressed.
The control cannot replace the primary. No portfolio or validation run
was made, and no reference, return cutoff, time, horizon or universe
was changed after seeing results.

## Runs and trial accounting

| Variant | Run ID | Events | Dates | Signal-day replays |
| --- | --- | ---: | ---: | ---: |
| Primary | `20261119T185640Z_gpt_volume_cost_reclaim_d7b2e4b7` | 4 | 4 | 4 |
| Control | `20261119T185827Z_gpt_volume_cost_reclaim_dd5c3845` | 842 | 497 | 497 |

Hypothesis commit `ba1947d` preceded every run. Both studies used
clean implementation commit `31826338`, agent gpt, build `447e58e098`,
development dates 2003-09-10..2016-12-30, `ibkr_pro_tiered`, $20,000
equity and $2,000 target. Both manifests are complete and nonscratch.
The two trials raise `intraday_rebound` from 114 to 116, including
nine pre-registry looks. The adaptive eight-point threshold and prior
VWAP/relative-reversal work were disclosed before the runs.

## Matching, availability and frozen gates

All 4 primary events exactly match control rows on company/date,
signal minute, entry minute, shares, entry price, fees, slippage and
r_120. No row mismatch was found before judging returns. The primary
and control choose the same first price event before checking history
or the reference. They cannot rescue rejected events later, and the
primary reference never changes the peer basket.

| Primary gate | Observation | Decision |
| --- | --- | --- |
| 150 events on 90 dates | 4 on 4 | Fail |
| 40 events in 2013–2016 | 0 | Fail |
| Gross mean >= +3%, both blocks | −5.95% full; no later estimate | Fail |
| Stressed mean > 0, both blocks | −7.48% full; no later estimate | Fail |
| Positive full 95% gross lower bound | −24.69% | Fail |
| Stressed mean above control, both blocks | Lower overall; empty later comparison | Fail |

All measured entries occurred at the intended next clock minute, so
full and on-time results and gate decisions coincide. The primary had
0 target orders above 5% of entry-bar volume; the control had
26, including 3 in 2013–2016. This study ignores those caps,
buying-power conflicts and expiry. It does not establish an executable
$2,000 portfolio. Four selected events are inadequate for inference;
the estimates below are descriptive, not evidence of a calibrated effect.

## Registered r_120 diagnostics

| Window | Events | Dates | Gross mean | Net mean, 1× | Net mean, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary full | 4 | 4 | −5.95% | −6.87% | −7.48% |
| Primary 2013–2016 | 0 | 0 | — | — | — |
| Control full | 842 | 497 | +1.83% | +1.25% | +0.89% |
| Control 2013–2016 | 151 | 137 | +0.76% | +0.27% | −0.01% |

| Full period | Primary 1× | Primary 2× | Control 1× | Control 2× |
| --- | ---: | ---: | ---: | ---: |
| Event P&L | −$551 | −$599 | $20,920 | $14,854 |
| Daily P&L t-statistic | -0.75 | -0.80 | 2.66 | 1.93 |
| Worst end-of-day drawdown | −$719 | −$738 | −$2,939 | −$3,985 |
| Winners | 2 | 2 | 486 | 468 |
| Mean winner | +4.37% | +4.14% | +7.78% | +7.74% |
| Losers | 2 | 2 | 356 | 374 |
| Mean loser | −18.12% | −19.10% | −7.67% | −7.69% |

Primary gross whole-day bootstrap interval: −24.69% to
+4.74%; control: +0.96% to +2.64%.
These use the native 2,000 resamples and seed zero. The primary's
four dates make its interval especially unstable. These are ordinary
descriptive intervals without correction for extensive adaptive search.

Daily event P&L sums net-return fraction times shares times entry price
over every manifest session, including zero-event sessions. T-statistics
use the sample standard deviation of that daily series. Drawdown includes
the initial zero. These are unconstrained independent-event statistics,
not portfolio risk. Saved study fees/slippage are fractions of notional;
2× doubles only slippage, with fees fixed.

## Results by development year

| Year | Primary events | Primary mean 1× | Primary mean 2× | Control events | Control mean 1× | Control mean 2× |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | 4 | −3.55% | −3.73% |
| 2004 | 0 | — | — | 26 | +2.03% | +1.80% |
| 2005 | 0 | — | — | 17 | −1.59% | −1.93% |
| 2006 | 0 | — | — | 14 | +3.79% | +3.57% |
| 2007 | 1 | −35.97% | −36.90% | 76 | +2.70% | +2.35% |
| 2008 | 3 | +2.83% | +2.33% | 396 | +1.59% | +1.16% |
| 2009 | 0 | — | — | 73 | +0.81% | +0.48% |
| 2010 | 0 | — | — | 14 | +3.40% | +3.11% |
| 2011 | 0 | — | — | 34 | −0.53% | −0.76% |
| 2012 | 0 | — | — | 37 | +0.61% | +0.31% |
| 2013 | 0 | — | — | 21 | +1.73% | +1.43% |
| 2014 | 0 | — | — | 45 | −0.27% | −0.55% |
| 2015 | 0 | — | — | 48 | +0.67% | +0.40% |
| 2016 | 0 | — | — | 37 | −0.41% | −0.70% |

| Year | Primary event P&L 1× | Primary event P&L 2× | Control event P&L 1× | Control event P&L 2× |
| --- | ---: | ---: | ---: | ---: |
| 2003 | $0 | $0 | −$283 | −$297 |
| 2004 | $0 | $0 | $1,051 | $931 |
| 2005 | $0 | $0 | −$536 | −$650 |
| 2006 | $0 | $0 | $1,060 | $1,000 |
| 2007 | −$719 | −$738 | $4,096 | $3,563 |
| 2008 | $168 | $138 | $12,554 | $9,124 |
| 2009 | $0 | $0 | $1,183 | $695 |
| 2010 | $0 | $0 | $942 | $863 |
| 2011 | $0 | $0 | −$359 | −$515 |
| 2012 | $0 | $0 | $452 | $228 |
| 2013 | $0 | $0 | $724 | $602 |
| 2014 | $0 | $0 | −$295 | −$545 |
| 2015 | $0 | $0 | $640 | $380 |
| 2016 | $0 | $0 | −$309 | −$524 |

No year, stock, shorter horizon or single losing event was removed to
rescue the strategy. The empty later primary block is a failed gate,
not evidence of a successful recent-period filter.

## Tests and interpretation

Focused strategy/repository checks passed (24 tests), with Ruff and
all five import contracts passing. Synthetic cases verify the fourteen
preceding-bar reference, exclusion of anchor/recovery bars, volume-unit
invariance, use of highs rather than closes, inclusive boundaries,
consistent observed OHLCV, missing data, unchanged reference peers,
first-event rejection, every-prefix replay, future perturbations and
a deliberate future-reference canary. Execution tests cover next-minute
expiry, two-hour exits and early-close auction fallback.

A volume-weighted bar high is not actual VWAP or a participant cost
basis. Different trade eligibility for OHLC and volume can defeat any
purported bound on real trade VWAP; no such bound was assumed here.
The formula's failure is not repaired by lowering it after observing
returns. Neither this test nor the prior empty activity-collapse
primary identifies signed demand or buying support.

Current-vintage identity/category/cap and corporate-action caveats
remain. Minute-bar opens and auctions, depth, latency and spreads are
unverified. The study prices both cost legs from entry conditions,
ignores participation/capital/expiry and differs from portfolio exit
opens. Every empirical performance number above derives from these two
registered run-store artifacts and their saved r_120 rows. No scratch
performance, validation run, post-seal market query, raw write/download,
rebuild or platform edit was used for this strategy.
