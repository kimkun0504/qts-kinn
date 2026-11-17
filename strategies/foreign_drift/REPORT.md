# Foreign drift: the rule fails in 6-K filers, and the jumps reverse

**Verdict: closed.** The rule fixed in [HYPOTHESIS.md](HYPOTHESIS.md), run once on each span.
3 trials. No holdout run.

| | Trades | 2005–2009 | 2010–2017 | 2018–2023 | All years | Weekly t |
|---|---|---|---|---|---|---|
| F50, $50M–$300M | 421 | −2.86% | −3.17% | −7.05% | **−5.27%** | −4.21 |
| F50Q (quality test) | 276 | −0.33% | −1.70% | −9.61% | −6.07% | −3.66 |
| F50, $300M–$2B | 648 | −0.68% | −2.07% | −2.65% | −2.17% | −2.74 |

After costs, a trade. A two-day jump of 15% on five times volume after a 6-K, bought at the
next open and held 15 sessions, in companies that file no 8-K.

## What it says

- **It is not the earnings drift.** The rule A50 makes 3% to 5% a trade in 8-K filers; the
  same price pattern in 6-K filers loses 5%, in every span, and the quality test does not
  help. Five years of nineteen are positive.
- **It does not test A50 as cleanly as hoped.** A 6-K is filed for every press release, not
  only for results, and the plan made no attempt to tell them apart. So this is a jump on
  any news in a small foreign company, and those are given back. That agrees with what the
  8-K studies found for news other than results (`news_hours`; family 18 of `swing_search`),
  and with a group of stocks where promotion is common.
- **It is another fall that a buyer cannot use.** Sold short it would have made about 5%
  before borrow, in small foreign listings, which are among the hardest stocks to borrow.
  Not pursued (`short_search`).
- **For the paper ledger:** the live rule requires an earnings 8-K, so it never takes these
  companies. This result says that is right.

Not done: reading which 6-Ks are results (the bulk file has no item codes for them; the
text of each filing would be needed).

## Reproduce

```
cd research/claude
uv run python foreign_drift.py table
uv run python foreign_drift.py measure
```
