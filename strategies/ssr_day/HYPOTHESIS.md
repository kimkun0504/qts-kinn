# SSR day: the session after the short-sale circuit breaker trips

Written 2026-11-17 22:57 ET, before anything is measured. Since 28 February 2011 (SEC Rule 201), once a
stock trades 10% or more under the previous close, short sales may only be made above the
best bid for the rest of that session and all of the next. Short sellers are a large share of
the selling on a bad day; holding them back for a full session may leave the next session
with less selling than it would otherwise have. The rule gives a natural control: a stock that
fell to −9% is the same kind of stock with no restriction, and before 2011 there was no rule
at all. Nothing here has used it.

## Events

Each session D from 2005 to 13 October 2023, listed common stock of $300M or more, $1M a day,
a close of $5 or more on the session before, and **no results 8-K** from the session before to
D+1 (A50's flag, and `night_bids`' results nights). **Tripped:** D's low is 10% or more under
the previous close. **Near miss (control):** D's low is 8% to 10% under it.

## Trade

Bought in the closing auction of D, sold in the closing auction of D+1 (the restricted
session). Costs: the auction allowance and commission, both ways. D's close is recorded in two
groups: **recovered** (closed less than 10% down) and **stayed down** (closed 10% or more down).

Sizes: $300M to $2B; $2B or more.

## Cells

Tripped: 2 sizes × 2 close groups = **4 cells**, family `ssr_day`. The near misses and the
years before 2011 are shown beside each cell as the control, not counted as cells.

## What counts (set now; the rule exists only from 2011)

Search 2011–2017: 0.3% a trade after costs, weekly t of 3, five years of seven, and the tripped
group at least 0.2 of a point better than the near misses of the same size and close group.
Test 2018–2022, each cell that goes forward run once: 0.15%, t of 2.5, four years of five.
**Placebo** 2005–2010: if the same gap over the near misses is there before the rule existed,
the cell is not the rule's doing and fails. 2023 is a check. The holdout stays sealed.

**Results, 2026-11-17 22:58 ET.** In REPORT.md. **None of the 4 cells meets the bar, and there is no sign
of the rule.** In 2011–2017 the tripped stocks did *worse* the next session than the near
misses ($300M to $2B, recovered: −0.43% against −0.21%; $2B or more: −0.35% against −0.28%);
those that stayed down made +0.07% and +0.29% (t under 1). 4 trials. No tests run.
