# Closing bids: a large stock pushed down into the close comes back by the morning, but not steadily enough to pass

**Verdict: not passed; a lead.** 26 cells and 2 test runs, 28 trials. One cell met the search
bar and failed the weekly t in both tests. The holdout is untouched.

Plan: [HYPOTHESIS.md](HYPOTHESIS.md). A limit-on-close buy order entered at 15:49, a few
percent under the price then, is filled at the official close only if the stock falls that
far in the last ten minutes; sold at the next open. No results due that evening. Every listed
common stock of $50M or more, 2005 to October 2023. Code: `research/claude/closing_bids.py`,
`research/claude/closing_funds.py`.

## The 18 cells (2010 to 2017, after costs, sold at the next open)

| Close under the 15:49 price by | Company | Fills | A trade | Median | Weekly t | Years positive | Worst |
|---|---|---|---|---|---|---|---|
| 2% or more | $50M–$300M | 309 | +2.03% | +0.27% | 1.81 | 6 of 8 | −31% |
| 2% or more | $300M–$2B | 557 | +0.31% | +0.27% | 1.63 | 5 of 8 | −53% |
| **2% or more** | **$2B+** | **173** | **+1.28%** | **+0.50%** | **3.30** | **8 of 8** | **−13%** |
| 3% or more | $50M–$300M | 148 | +3.67% | +0.41% | 1.77 | 5 of 8 | −31% |
| 3% or more | $300M–$2B | 205 | +0.50% | +0.45% | 1.77 | 6 of 8 | −53% |
| 3% or more | $2B+ | 59 | +2.41% | +1.59% | 3.38 | 8 of 8 | −13% |
| 5% or more | $50M–$300M | 49 | +8.75% | +0.59% | 1.48 | 4 of 8 | −29% |
| 5% or more | $300M–$2B | 55 | +1.66% | +0.45% | 1.16 | 7 of 8 | −37% |
| 5% or more | $2B+ | 6 | +7.87% | +6.76% | 2.50 | 4 of 4 | 0% |

Every cell is positive, the opposite of the same order after hours (`night_bids`, every cell
negative). Sold at the next close the figures are similar and less steady. Only the $2B+
cell at 2% has the count, the t and the years. These figures are after a data check added
when the first reading looked too good: the official close must lie inside the prices that
printed between 16:00 and 16:05 in the minute data. It removed a third of the fills and a
false −81%.

## The cell that went to the tests: $2B and over, close 2% or more under the 15:49 price

| After costs | Fills | A trade | Median | Weekly t | Years positive | Winners | Worst |
|---|---|---|---|---|---|---|---|
| 2010–2017 (search) | 173 | +1.28% | +0.50% | 3.30 | 8 of 8 | 65% | −13% |
| 2005–2009 (test) | 857 | +1.51% | +1.98% | **0.33** | 4 of 5 | 68% | −90% |
| 2018–2022 (test) | 1,521 | +1.35% | +0.98% | **1.37** | 4 of 5 | 71% | −24% |

By year: 2005 +2.11% (11), 2006 +1.04% (6), 2007 +0.94% (32), 2008 +1.86% (688), 2009 −0.35%
(120), 2018 +1.85% (36), 2019 −0.09% (20), 2020 +1.86% (995), 2021 +0.36% (332), 2022 +0.13%
(138).

- **The average is the same in all three periods (1.3% to 1.5% a night) and positive in 16
  years of 18.**
- **It fails the test set beforehand on the weekly t, in both periods.** Four fifths of the
  test fills are in 2008 and 2020. In those years whole weeks win or lose together, and week
  by week the result is too uneven to tell from luck.
- In a quiet year it fills 6 to 36 times; in a crisis year hundreds.

## What the gain is made of (2 cells)

| After costs | 2010–2017 | 2005–2009 | 2018–2022 |
|---|---|---|---|
| The auction fill, as above | +1.28% | +1.51% | +1.35% |
| With SPY sold short overnight against it | +1.20% (t 3.23) | +0.35% | +0.32% |
| SPY's own overnight return on those fills | +0.05% | +1.13% | +1.00% |
| Fills on days with ten or more | 0% | 64% | 69% |
| Bought after the close instead (first minute from 16:06, at its high) | +0.91% (t 2.08) | +1.21% | +1.32% |

- **In quiet years it is the stock's own rebound**: fills are scattered one or two a day
  (BAC and MA on 8 August 2011, TSLA on 13 January 2012), the market does nothing overnight,
  and the hedged trade keeps 1.2%. About 20 a year.
- **In crisis years it is mostly the market**: two thirds of the fills come on days when
  everything is sold into the close, and with SPY sold against them 0.3% is left.
- **It can be bought after the close** at about the closing price (0.0% to 0.3% over it), for
  0.9% to 1.3%. That matters because a limit-on-close order has to be resting in every large
  stock at 15:49, which a small account cannot fund; a scan at 16:01 can.

## The market itself after a late sell-off (6 cells)

SPY, QQQ and IWM bought in the last minute when the price at 15:58 is under the 15:49 price,
sold at the next open, 2005 to 2022.

| After costs | Trades | A trade | Weekly t | 2005–2009 | 2010–2017 | 2018–2022 |
|---|---|---|---|---|---|---|
| SPY, down 0.5% or more | 63 | +0.11% | −0.15 | −0.06% | −0.10% | +0.64% |
| QQQ, down 0.5% or more | 69 | +0.09% | −0.43 | +0.12% | −0.47% | +0.27% |
| IWM, down 0.5% or more | 91 | −0.24% | −1.43 | −0.42% | −0.43% | +0.27% |
| SPY, down 1% or more | 18 | +0.87% | 1.30 | +0.20% | +0.77% | +2.11% |
| QQQ, down 1% or more | 19 | +1.36% | 2.39 | +0.80% | +1.23% | +2.27% |
| IWM, down 1% or more | 20 | +0.39% | 0.50 | +0.03% | +0.96% | +1.22% |

No trade. A fall of 1% in ten minutes happens about once a year and the result rests on 18
to 20 nights.

## What it is worth

Not passed, and the honest size of it is small: in a normal year about 20 trades of 1.2%, on
$2,000 each about $500. Its interest is that it is the first positive result that has
nothing to do with earnings, it needs no borrow, and it fills most when the market is being
sold, which is when the earnings book is losing. As a lead to follow on paper it needs a
scan a minute after the close each day (stocks of $2B or more that closed 2% or more under
their 15:49 price), which the nightly run can reconstruct afterwards from minute bars.

Not tested: quotes in the auction or after hours (none on disk); the opening auction.

## Reproduce

```
cd research/claude
uv run python night_bids.py daily
uv run python night_bids.py filings
uv run python closing_bids.py collect 2005 2023
uv run python closing_bids.py search
uv run python closing_bids.py test 2 large open
uv run python closing_bids.py followups
uv run python closing_funds.py collect
uv run python closing_funds.py measure
```
