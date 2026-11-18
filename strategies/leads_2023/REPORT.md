# The 2023 check for four leads

Each lead that failed its tests on steadiness but stayed positive in most years, read once on
January to 13 October 2023 with the rule it was tested with. Plan and reading rule:
[HYPOTHESIS.md](HYPOTHESIS.md). 4 trials, charged to the leads' own families (after_hours 2,
closing_bids 1, rebalance_flows 1). The holdout is untouched. Code:
`research/claude/leads_2023.py`.

| Lead | 2005–2009 | 2010–2017 | 2018–2022 | **2023** | Reading |
|---|---|---|---|---|---|
| **after_hours short:** $300M–$2B, down 15%+ after hours on results, sold short at the minute's low, bought back at the next open | +2.98% (143, t 3.79) | +2.82% (251, t 3.89) | +1.60% (201, t 1.15; 5 of 5 years) | **+6.66% (44, t 2.89; median +6.13%)** | not contradicted |
| … bought back at the next close | +4.42% | +3.41% | +2.10% | +8.80% | |
| after_hours long, resting order: $2B+, up 5–15%, 15 sessions | +1.21% | +1.45% | +1.45% (t 1.98) | −0.85% (139) | contradicted |
| closing_bids: $2B+, a limit-on-close 2% under the 15:49 price | +1.51% | +1.28% | +1.35% | +0.56% (39; median −0.14%) | not contradicted (weak) |
| rebalance_flows: own the side that won the month, first two sessions | +0.41% | +0.72% | +0.26% | +1.17% (10 months) | not contradicted |

After costs. None of these passed its tests; this reading can only rule a lead out.

**The after-hours short is the strongest thing found since the earnings rule.** A company of
$300M to $2B whose stock is down 15% or more half an hour after an after-close results 8-K
has been lower again by the next open, on average, in all 10 test years and in 2023, by 1.6%
to 6.7% a trade, about 30 to 45 trades a year. It failed the test set beforehand only on the
weekly t of 2018–2022. What it still needs before money:

1. **Borrow at that moment.** These are mid-sized companies, usually borrowable, but after a
   15% fall many want to short them; whether IBKR shows shares and at what fee has to be
   recorded on each signal night.
2. **The fill.** The test sold at the low of the first minute after the reading; a third of
   2023's entries were in minutes with under $5,000 traded, and there are no after-hours
   quotes on disk.
3. **The tail.** Single trades lost up to 29% overnight in 2023 (38% to the close).

**What to do:** follow it on paper, one signal at a time, with the borrow and fee IBKR shows
recorded beside each. About one signal a week, most in the reporting seasons.

The month-end lead is a once-a-month trade of about 1% before the market's own move; it can be
watched without building anything.
