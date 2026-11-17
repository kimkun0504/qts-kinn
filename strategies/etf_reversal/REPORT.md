# Short falls in index funds: too thin, closed

Plan: [HYPOTHESIS.md](HYPOTHESIS.md). Run 2026-11-17 00:04 ET. Family `etf_swing`, 8 trials,
holdout untouched and not needed.

## Result

No cell passes, and none comes close. Buying an index fund at the open after a short fall
and selling at the first close above its 5-day average wins about 70% of the time and earns
0.1% to 0.4% a trade: real, and too small to matter.

| Cell (14 funds pooled, 0.03% a side) | 2004–2014: a trade, weekly t | 2015–2023: a trade, weekly t | Book, 2015–2023: a year, worst year |
|---|---|---|---|
| New 5-day low close | 0.27%, 5.57 | 0.16%, 3.07 | $1,148, −$2,642 |
| New 5-day low close, above the 200-day average | 0.13%, 4.56 | 0.12%, 2.55 | $330, −$2,284 |
| New 10-day low close | 0.34%, 4.52 | 0.11%, 1.46 | $1,062, −$1,631 |
| New 10-day low close, above the 200-day average | 0.21%, 3.02 | 0.17%, 1.39 | $409, −$1,864 |
| 3 falling closes | 0.37%, 4.02 | 0.10%, 2.43 | $717, −$2,472 |
| 3 falling closes, above the 200-day average | 0.22%, 3.27 | 0.15%, 0.79 | $440, −$1,979 |
| 4 falling closes | 0.33%, 3.89 | 0.50%, 3.03 | $783, −$1,699 |
| 4 falling closes, above the 200-day average | 0.01%, 1.58 | 0.18%, 1.09 | $299, −$906 |

The book is $20,000 with at most four positions of $5,000.

- The term for going forward was 0.5% a trade where chosen; the best is 0.37%. Where tested
  the edge is about half what it was before 2015 in six of the eight cells.
- As a book it makes $300 to $1,150 a year on $20,000 (2% to 6%) with a worst year of −$900
  to −$2,600. That is a bank account's return with a stock market's bad year.
- The trend filter makes every cell worse where chosen: the bounces worth having follow
  falls in a falling market, which is also where the falls that do not bounce are.
- One cell (4 falling closes) did better where tested than where chosen. It was not the
  cell that would have been chosen, and one of eight doing so is what chance gives.

**Closed.** Index funds can carry any amount of money and have no edge of this kind worth
carrying. Leverage would scale the return and the bad year alike.

## Reproduce

```
cd research/claude && uv run python etf_reversal.py
```
