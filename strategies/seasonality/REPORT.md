# Report: stocks repeating their own calendar months

**Verdict (2026-11-23): closed.** None of the four cells comes near the bar on 2010 to 2017,
the years it was chosen on. The test years were not read: the plan closes the family when no
cell passes where chosen. 4 trials, family `seasonality`.

## What was tested

Each month, the large ($2B and up) or mid-sized ($300M to $2B) US common stocks ranked by their
average return in the same calendar month of the previous five years (at least three); the top
tenth bought at the open of the month's first session and sold at its last close, measured
against the average eligible stock of its size and against the bottom tenth. Costs both ways
every month. Plan: `HYPOTHESIS.md`; code: `research/claude/seasonality.py`.

## Result, 2010 to 2017 (96 months; bar: +0.40% a month after costs, t 2.5, 6 of 8 years)

| Cell | After costs, a month | t | Years up | At 2× costs |
|---|---|---|---|---|
| Large, top tenth vs large stocks (112 stocks) | −0.17% | −1.06 | 2 of 8 | −0.26% |
| Large, top minus bottom tenth | −0.29% | −1.23 | 3 of 8 | −0.46% |
| Mid, top tenth vs mid-sized stocks (94 stocks) | +0.03% | 0.17 | 3 of 8 | −0.14% |
| Mid, top minus bottom tenth | −0.09% | −0.36 | 4 of 8 | −0.43% |

Before costs the tenths line up with nothing: large stocks' tenths run −0.10% to +0.11% around
the average with no order, and the rank correlation of score and next month's return is
−0.0002 a month (mid-sized +0.013). The mid-sized top tenth is +0.25% before costs, which costs
take back.

## What would change the verdict

A longer history (the published effect uses up to twenty earlier years; ours has five) or a
signal limited to the recurring causes themselves (the results month, the dividend month), which
are tested elsewhere. Not worth more trials in this family.
