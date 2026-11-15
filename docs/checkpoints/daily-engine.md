# Checkpoint: the daily engine (design steps D1 to D5), 2026-11-15

**Status: built and tested. The first alpha run through it (momentum) behaved as the literature
says and failed its validation bars, as expected. Three things need the owner.**

## What was built

| Step | Delivered |
|---|---|
| D1 | Daily data with total returns (dividends, spinoffs, splits), `DailyView` with the lookahead rule |
| D2 | Daily engine: corporate actions, borrow fee, delistings, auction fills, month-by-month resume; `kinn book` |
| D3 | Single-index risk model; mean-variance optimizer with gross, net, position, beta and sector limits; ranked book |
| D4 | As-reported fundamentals (SF1), usable from the session after filing |
| D5 | `momentum_12_1`: hypothesis, three development runs, one validation run, report; Workbench page for books |

Tests: 143 Python tests (44 of them new). New canaries: an alpha that reads the session's own return is caught;
a random book on random prices loses about its costs; the same book gives the same fills twice;
a fundamental is not visible before the session after its filing.

## Results

`strategies/momentum_12_1/REPORT.md`. Validation 2017–2023: +3.0% a year, Sharpe 0.25, worst
drawdown −33.6%. Bars were Sharpe 0.5 and drawdown 25%: failed. Parked.

## Data fixes made on the way (build `6453bd3ec8`, data-5)

Dividends were on the wrong share basis; 142 split dates were days off; 744 listed splits never
showed in prices; spinoffs were missing. Details in `docs/data/DATA_NOTES.md`. **The intraday
panel changed on those days too, so earlier intraday results were computed on slightly worse
data.** They have not been re-run.

## Needs the owner

1. **Confirm decision 0015** (a split factor from the snapshot is kept only to restore dividend
   amounts).
2. **Decide whether to re-run the rebound results on the corrected data** (each re-run is a new
   run; whether it counts as a new trial is the owner's call).
3. **Choose the next daily alpha.** The engine is ready; momentum alone is not worth trading.

## Deferred (decisions 0014, 0016)

Margin calls, borrow availability, interest, intraday execution policies, a factor risk model,
multi-family trial charging, a tearsheet file for books.
