# Report: passive entry after a no-news drop

2026-11-15, claude. Definition and criteria: [HYPOTHESIS.md](HYPOTHESIS.md).
Run `20261115T201610Z_claude_intraday_rebound_passive_707a4f9d` (tick study, counted; trial 11
of family `intraday_rebound`). 415 orders from the 420-event quote sample.

## Verdict

**Not established: by the rule set in advance it does not pass, because the sample is too small
to tell.** A bid resting for 10 minutes was filled 62% of the time and earned **+0.56% net per
fill**, but the 95% interval is −0.15% to +1.29%, which includes zero. It is the first form of
this trade with a positive point estimate after real costs, and about 0.9 percentage points
better than a market order on the same events (−0.36%). It is nowhere near 3–4% a trade.

| Criterion | Result | Met? |
|---|---|---|
| Net per fill at least +0.5%, interval above zero | +0.56% (−0.15% to +1.29%) | Level yes, interval **no** |
| Fill rate at least 30% | 62% | Yes |
| Positive in 2017–2023 alone | +0.54% (−0.51% to +1.60%) | Yes, not distinguishable from zero |

## Evidence (strict fill rule: a trade strictly below the limit)

| | Orders | Fill rate | Net per fill (95% interval) | Net per order placed | Unfilled orders, had they been bought at the bid | Market order at the ask |
|---|---|---|---|---|---|---|
| All | 415 | 62% | +0.56% (−0.15% to +1.29%) | +0.35% | +1.14% | −0.36% |
| ADV under $1M | 135 | 41% | +1.19% (−0.34% to +2.86%) | +0.49% | +1.43% | −0.79% |
| ADV $1–10M | 140 | 62% | −0.36% (−1.44% to +0.79%) | −0.22% | +1.08% | −0.74% |
| ADV $10M and over | 140 | 81% | +0.96% (−0.17% to +2.08%) | +0.77% | +0.39% | +0.45% |
| 2003–2016 | 208 | 68% | +0.58% (−0.50% to +1.60%) | +0.39% | −0.04% | −0.58% |
| 2017–2023 | 207 | 56% | +0.54% (−0.51% to +1.60%) | +0.30% | +2.00% | −0.13% |

Under the lenient rule (a trade at or below the limit): fill rate 79%, net per fill +0.41%
(−0.28% to +1.06%). The truth about queue position lies between the two rules.

## Reading

- **Adverse selection is real and visible.** The orders that did *not* fill would have earned
  +1.14% had they been bought at the bid: the stocks that bounced at once left the bid behind.
  The fills are the weaker half of the events. That is the cost of being passive.
- **Passive still beats paying the spread** by about 0.9 points per trade on these events.
- **The middle liquidity bucket is negative** while the two ends are positive. With 87 fills in
  it this is as likely noise as a pattern; it is not a basis for dropping the bucket.
- **Per order placed** (unfilled counted as zero) the result is +0.35%: capital is tied up for
  10 minutes with a 38% chance of nothing happening.
- The sample is equal across liquidity buckets, so the pooled number is not the population
  average; real events are weighted toward the $1–10M bucket.

## Trial count

Family `intraday_rebound`: 11 trials. One definition, no selection among variants in this run.

## What would change the verdict

**A larger sample of the same definition, sized now and looked at once.** The interval's
half-width is about 0.7 points on 256 fills. To detect +0.5% it must be near 0.3, which needs
roughly 1,500 fills, so about **2,500 events** (2,080 more, drawn the same way with a new seed,
same windows, same rules). The owner's download takes a few minutes. Declaring the size before
looking again keeps this from becoming "sample until it passes".

Even if it then passes, +0.5% a trade on $500 positions is about $2.50 a fill. What it would
earn in a year depends on how many such orders the account can rest at once, which is the
capacity question the earlier build also ended on.
