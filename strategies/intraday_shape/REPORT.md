# Intraday shape: a stock pushed up into the close, day after day, gives it back

**Verdict: closed; one finding worth keeping as a warning.** 28 cells on 2010 to 2017, none
meets the bar set in [HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 28 trials. The
holdout is untouched.

From minute bars, for every listed common stock of $50M or more and every session from 2005
to October 2023 (15.2 million stock-days): the return of the first half hour (the open to
10:00) and of the last half hour (15:30 to the official close), summed over the last 10
sessions. The 10 stocks with the highest (or lowest) score in a size group, bought at the next
open and held 5 or 10 sessions. Code: `research/claude/intraday_shape.py`.

## The 10 stocks most pushed up in the last half hour (2010–2017)

| Size | Hold | A trade after costs | Over the average stock of its size | Weekly t of that |
|---|---|---|---|---|
| $50M–$300M | 5 | −1.41% | −0.86% | −6.23 |
| $50M–$300M | 10 | −1.73% | −1.36% | −6.30 |
| $300M–$2B | 5 | −0.74% | −0.59% | −3.74 |
| $300M–$2B | 10 | −0.91% | −1.02% | −4.06 |
| $2B+ | 5 | −0.48% | −0.48% | −5.58 |
| $2B+ | 10 | −0.51% | −0.73% | −4.99 |

- **A stock that rises into the close session after session trails other stocks** by half a
  percent to 1.4% over the next two weeks, in every size, with a weekly t of −4 to −6. Buying
  pressure at the close is temporary.
- **The other end is weak.** The 10 most pushed down into the close beat the average stock by
  up to 0.72% (small, 10 sessions, t 3.04), +0.36% after costs. The first half hour, at either
  end, predicts little.
- **The short is not worth it after costs.** Long the 10 most pushed down and short the 10 most
  pushed up, in companies of $2B or more: 0.20% a trade for 10 sessions (weekly t 1.79). The
  stocks pushed up into the close are thin for their size; the round trip costs them 0.21%.

**Use:** as a warning on a stock already chosen for another reason. A candidate for the
earnings rule or the insider rule that has been pushed up into the close for two weeks is
worth checking against this before it is bought; that check has not been run.

## Reproduce

```
cd research/claude
uv run python night_bids.py daily
uv run python intraday_shape.py collect 2005 2023
uv run python intraday_shape.py table
uv run python intraday_shape.py search
uv run python intraday_shape.py search_low
uv run python intraday_shape.py pairs search
```
