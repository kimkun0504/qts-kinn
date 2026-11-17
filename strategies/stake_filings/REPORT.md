# Stake filings: a little more than the market, not enough

**Verdict: closed.** 24 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run and the holdout is untouched. 24 trials.

26,812 initial 13Ds and 161,770 initial 13Gs matched to stocks; 87,834 in the universe
(financial companies and 82 frequent filers left out). Buy at the open after the session the
filing could first move the stock; after costs, a trade; 2010 to 2017.

| Initial 13D, any reaction | 15 sessions | Over IWM | 40 sessions | Over IWM | Weekly t (40) |
|---|---|---|---|---|---|
| $50M–$300M (1,135) | +1.12% | +0.89% | +1.77% | +0.69% | 2.05 |
| $300M–$2B (1,628) | +1.06% | +0.62% | +1.83% | +0.51% | 3.69 |
| $2B and over (1,028) | +0.45% | −0.31% | +1.40% | +0.07% | 3.85 |

| Initial 13G (the passive control) | 15 sessions | Over IWM | 40 sessions | Over IWM |
|---|---|---|---|---|
| $50M–$300M (5,302) | +2.24% | +0.71% | +4.28% | +0.85% |
| $300M–$2B (14,013) | +2.31% | +0.35% | +4.06% | +0.55% |
| $2B and over (9,903) | +2.04% | −0.17% | +3.43% | −0.07% |

- **After a 13D a stock does about half a point to a point better than small stocks in
  general** over the next three to eight weeks. The raw figures look larger because the
  market rose in these years.
- **The passive filings do the same,** so what is left is not about activism. It looks like
  the ordinary drift of a stock that a large holder has just been buying.
- **Requiring the stock to rise on the filing day makes it worse** in small companies (up 5%
  on volume: −3.7% over 40 sessions).
- No cell reaches 2% over 15 sessions or 4% over 40 with a weekly t of 3 and a point over
  the index fund. The rise the studies of activism report is mostly on and before the
  filing day, which a buyer at the next open does not get.

Limits: the bulk file does not name the filer, so a known activist cannot be told from any
other holder; that would need each filing's header.

## Reproduce

```
cd research/claude
uv run python stake_filings.py table
uv run python stake_filings.py search
```
