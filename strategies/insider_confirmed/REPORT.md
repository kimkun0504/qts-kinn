# Insider buying, confirmed: waiting for the market makes it worse

**Verdict: closed.** 4 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 4 trials. The holdout is untouched.

Rule I's insider purchases ($50M to $300M, $100,000 or more), then the first strong rise on
volume within 10 or 20 sessions; bought at the next open, held 15 sessions. Code:
`research/claude/insider_confirmed.py`.

| 2010–2017, after costs | Trades | A trade | Median | Weekly t | Years positive |
|---|---|---|---|---|---|
| Rise 10% on 3× volume within 10 sessions | 324 | +1.94% | −1.17% | 1.62 | 6 of 8 |
| … within 20 sessions | 452 | +1.25% | −1.25% | 1.15 | 5 of 8 |
| Rise 15% on 5× volume within 10 sessions | 104 | +3.51% | −2.06% | 1.42 | 6 of 8 |
| … within 20 sessions | 157 | +1.76% | −2.06% | 0.84 | 5 of 8 |

Rule I itself made 3.2% a trade in these years. After a strong rise the typical confirmed
purchase gives some back; the average rests on a few large winners.

## Reproduce

```
cd research/claude
uv run python insider_confirmed.py search
```
