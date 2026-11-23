# Report: slow asset growers against fast ones

**Verdict (2026-11-23): closed.** None of the four cells meets the bar on 2010 to 2017, where
it was chosen; all four lose after costs. The test years were not read. 4 trials, family
`asset_growth`.

## What was tested

Each month, the large ($2B and up) or mid-sized ($300M to $2B) US common stocks ranked by the
growth of total assets over the past year (the latest trailing-year filing made before the
month, against the same company's period a year earlier); the slowest-growing tenth bought at
the open of the month's first session and sold at its last close, measured against the average
eligible stock of its size and against the fastest-growing tenth. Costs both ways every month.
Plan: `HYPOTHESIS.md`; code: `research/claude/asset_growth.py` (with `seasonality.py`'s
monthly table).

## Result, 2010 to 2017 (96 months; bar: +0.40% a month after costs, t 2.5, 6 of 8 years)

| Cell | After costs, a month | t | Years up | At 2× costs |
|---|---|---|---|---|
| Large, slowest tenth vs large stocks (120 stocks) | −0.26% | −1.81 | 3 of 8 | −0.34% |
| Large, slowest minus fastest tenth | −0.26% | −1.08 | 2 of 8 | −0.43% |
| Mid, slowest tenth vs mid-sized stocks (110 stocks) | −0.27% | −1.32 | 1 of 8 | −0.44% |
| Mid, slowest minus fastest tenth | −0.09% | −0.28 | 3 of 8 | −0.43% |

Before costs, the slowest growers are no better than the average (large −0.13%, mid −0.03% a
month). The fastest growers do trail (large −0.21%, mid −0.48% a month before costs), which
is where the published effect is said to sit, but a short of them was not one of the cells and
would pay borrow on a rising market; it is noted, not tested. The rank correlation of growth
and the next month's return is under 0.003 in both sizes.

## What would change the verdict

Nothing in this family on this data: the long side has no edge, and the short side would be a
new hypothesis with its own trials.
