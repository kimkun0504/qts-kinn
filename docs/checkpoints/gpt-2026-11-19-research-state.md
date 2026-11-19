# GPT research state, 2026-11-19

The +3% all-completed-trade validation objective remains active and
unachieved. No recent candidate has qualified for a portfolio or a
validation run. All strategies below are parked, so none is active.
The common intraday_rebound charge is 118, including nine prior looks.
Do not lower the count/sample/recency/risk bars to promote a control.

## Completed recent evidence

- Bid replenishment: control
  `20261119T043722Z_gpt_bid_replenishment_reversal_91e8fd86`.
  Owner acquisition arrived. Separate index `2738076d4b` retained every
  candidate but failed both frozen valid-pair coverage gates. No primary
  or validation performance run. Do not relax freshness or tied-timestamp
  rules after seeing coverage. See that strategy's REPORT and OWNER_ACTIONS.
- Air pocket: primary
  `20261119T184554Z_gpt_air_pocket_reversal_a41443c6`, control
  `20261119T184744Z_gpt_air_pocket_reversal_071998df`.
  Primary had no events. The positive control cannot replace it and is
  too sparse in later development. See its REPORT.
- Volume-cost reference: primary
  `20261119T185640Z_gpt_volume_cost_reclaim_d7b2e4b7`, control
  `20261119T185827Z_gpt_volume_cost_reclaim_dd5c3845`.
  Four sparse negative primary events; no later primary events. See REPORT.
- Recent disclosed purchase: primary
  `20261119T220741Z_gpt_disclosed_value_reversal_5b20f5b2`, control
  `20261119T221034Z_gpt_disclosed_value_reversal_20c0c123`.
  Selector improves descriptive means in full and later development but
  fails sample and gross-return bars. All primary rows exactly match
  the control. Both pin Form 4 `fe7c80978b`. See REPORT for every number.

These are sequential registered experiments, not globally independent
discoveries. No selected alternate horizon or liquidity subgroup can
rescue them. The CLI automatically displays all horizons; only r_120
was used for the registered decisions. For future primary/control tests,
avoid interpreting even preliminary return output until both runs finish
and the exact-subset audit passes. Status/count updates can precede it.

## Next prospective direction, not yet registered

Prefer testing an economically distinct public stock selector over
inventing another restrictive bar transform. The existing build already
contains as-reported Sharadar ART fundamentals. `opinc` and `ncfo` are
available source fields. A paired positive operating-profit/operating-
cash-flow selector is a prospective hypothesis, not a tested result.
Using signs avoids comparing mixed USD and company-currency amounts.
No fundamental cohort count or return has been measured for it.

It would need a coherent native intraday snapshot. Existing DataStore
fundamentals and DailyView support daily use, but DayView has no such
field. Daily `_as_of` carries each field's latest non-null value separately;
that contract cannot establish that a pair came from one period/filing.
This is a limitation for the proposed paired rule, not a claimed bug
in the existing last-value API. Do not privately load data in a strategy
or change daily behavior.

Before any test, write and commit the complete new HYPOTHESIS, strategy,
configs and contract tests, and a precise owner request for a small
typed native snapshot (as-reported only, filed before session, coherent
row, no revival of an older favorable row when latest data is invalid,
explicit missing/conflicting status, freshness rule, version/build pin
and seal tests). Push the reviewable proposal before asking for the
platform exception. No rebuild or download should be needed. Existing
authorizations for execution, counts, timed 8-K and NBBO do not authorize
this new financials view. Do not edit src/kinn for it without approval.

Current Form 4 archive ends 2023-09-29. No extension is requested for
its failed candidate, and no validation dates may be truncated to fit it.
Analyst consensus is absent; general news is sparse before 2021 and lacks
first-received timestamps. Timed original 8-K and count inputs already
exist; do not ask again for those completed permissions.

Continue only in wt-gpt on agent/gpt branches. Raw remains read-only,
sealed access and post-seal market dates are forbidden, and every
empirical result must come from registered nonscratch Kinn runs.
