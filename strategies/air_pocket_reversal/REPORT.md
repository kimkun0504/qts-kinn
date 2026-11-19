# Transaction-activity collapse during a relative selloff

## Verdict: park

The primary produced no signals or completed events. Its sample and
return gates fail; no primary net-return, t-statistic or drawdown
estimate exists. Removing the activity-collapse condition produced
178 control events on 125 dates, with +5.27% net at base
costs and +4.75% with doubled slippage at the registered r_120
horizon. The control cannot replace the primary. Its 19 later
development events also miss the required 40-event minimum.

No portfolio or validation run was made. No threshold, count window,
history requirement, price trigger, clock time or exit was adjusted.
A high control mean does not establish an eligible or validated alpha.

## Registered runs and trials

| Variant | Run ID | Events | Dates | Native signal-day replays |
| --- | --- | ---: | ---: | ---: |
| Primary | `20261119T184554Z_gpt_air_pocket_reversal_a41443c6` | 0 | 0 | 0 |
| Control | `20261119T184744Z_gpt_air_pocket_reversal_071998df` | 178 | 125 | 125 |

Hypothesis commit `ca9d6b5` preceded all runs. Both runs used clean
implementation commit `6479111d`, agent gpt, data build `447e58e098`,
2003-09-10..2016-12-30, `ibkr_pro_tiered`, $20,000 account and $2,000
target. Both manifests are complete and nonscratch. The two empirical
trials increase `intraday_rebound` from 112 to 114, including nine
pre-registry looks. Earlier size-peer, quote, volume and momentum
experiments remain search history; these are not independent first looks.

## Study gates and exact-subset audit

Primary events: zero overall, zero dates, zero in 2013–2016. All primary
sample/return/improvement gates therefore fail or are not estimable.
The primary is the empty exact control subset; matching is vacuous
and is not evidence that the filter helps. Both implementations choose
the first price event before data/ratio checks and cannot rescue a
rejected event later. Both use every eligible peer, regardless of its
count availability.

The activity-collapse condition removes the entire qualified control
population under this frozen definition. The control is an ablation,
not a selected second alpha. Its positive mean does not authorize a
portfolio or a validation test. Any future follow-up must be registered
separately and charged to the existing family.

## Control diagnostics at r_120

| Window | Events | Active dates | Gross mean | Mean net, 1× | Mean net, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full development | 178 | 125 | +6.06% | +5.27% | +4.75% |
| 2013–2016 | 19 | 19 | +4.41% | +3.73% | +3.34% |

| Full control | 1× slippage | 2× slippage |
| --- | ---: | ---: |
| Sum of modeled event P&L | $18,692 | $16,868 |
| Daily P&L t-statistic | 3.46 | 3.21 |
| Worst end-of-day drawdown | −$1,532 | −$1,565 |
| Annualized daily event Sharpe | 0.95 | 0.88 |
| Winners | 122 | 118 |
| Mean winner | +12.92% | +12.91% |
| Losers | 56 | 60 |
| Mean loser | −11.41% | −11.29% |

Full gross 95% whole-day bootstrap interval:
+3.63% to +8.49%, with 2,000 resamples and seed zero,
matching the native study convention. These ordinary intervals do
not correct for the extensive adaptive family search.

All control entries were on the intended next clock minute, so full
and on-time samples coincide. 4 target orders exceeded 5% of actual
entry-bar volume. The study ignores that cap and portfolio conflicts;
this is independent-event P&L, not a capital-constrained account.
Its daily dollar series sums net return times shares times entry
price over every session in the manifest, including zero-event dates.
Drawdown includes the initial zero. Study fees and slippage are return
fractions; 2× doubles slippage only, with fees fixed.

## Annual control results

The primary has no events in every year; its returns and risk estimates
are not estimable.

| Year | Control events | Mean net, 1× | Mean net, 2× | Event P&L, 1× | Event P&L, 2× |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2003 | 0 | — | — | $0 | $0 |
| 2004 | 3 | +11.20% | +10.95% | $670 | $655 |
| 2005 | 2 | −15.35% | −15.71% | −$615 | −$629 |
| 2006 | 4 | +9.48% | +9.15% | $758 | $731 |
| 2007 | 13 | +11.03% | +10.47% | $2,861 | $2,716 |
| 2008 | 109 | +5.40% | +4.80% | $11,739 | $10,432 |
| 2009 | 12 | −0.75% | −1.04% | −$177 | −$247 |
| 2010 | 4 | +3.71% | +3.51% | $292 | $276 |
| 2011 | 6 | +3.66% | +3.31% | $437 | $396 |
| 2012 | 6 | +10.98% | +10.62% | $1,315 | $1,272 |
| 2013 | 4 | +9.59% | +9.12% | $767 | $729 |
| 2014 | 5 | +3.10% | +2.81% | $309 | $280 |
| 2015 | 5 | +5.36% | +4.98% | $533 | $495 |
| 2016 | 5 | −1.96% | −2.39% | −$197 | −$239 |

The control is concentrated in 2008: 109 of 178 events.
Later development has only 19 events; positive point estimates
cannot substitute for its failed sample requirement. No later-year
subgroup or alternative holding horizon was selected as a replacement.

## Tests and limitations

Focused strategy/repository checks passed (24 tests), as did Ruff and
all five import contracts. Synthetic tests cover the unequal normalized
count windows, exclusion of the decision bar, exact integer boundaries
and large products, missing counts/bars/volume, first-event handling,
primary/control subsets, unchanged peer membership, future perturbation
invariance, every-prefix replay, an intentional future-count canary,
next-minute expiry, two-hour exits and early-close auction fallback.
The primary has no empirical signal-day replay; synthetic tests remain
software evidence rather than an execution or profitability guarantee.

This outcome does not prove that liquidity gaps cannot revert. It shows
that this particular collapse condition produced no eligible events.
The positive control needs neither reinterpretation as the primary nor
a retrospective loosening of the rule. Counts do not identify signed
flow or order cancellation; full observed histories exclude many other
events. Quote completeness, executable prices, auction allocation and
latency are unverified. The normal study estimates both cost legs from
the entry bar and ignores participation, expiry and capital constraints.
Snapshot category/cap and corporate-action limitations persist.

All performance numbers derive from the two registered run-store
artifacts and their saved r_120 rows. No scratch empirical result,
validation planning, post-seal market data, raw write/download, rebuild
or platform change was used for this strategy.
