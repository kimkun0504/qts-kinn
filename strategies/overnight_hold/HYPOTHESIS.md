# Overnight hold: owning a stock only at night, chosen by where its gains have been made

Written 2026-11-17 22:10 ET, before anything is measured. The owner asked for indicators of our own and
for ways in and out other than the usual ones. On 17 November I proposed one indicator built
from a measurement a daily chart hides: **where a stock's move happens**, between the close
and the next open or between the open and the close. This tests it in the simplest form that
uses it: hold only during the part of the day where the stock has been making its gains.

## Why

Different people trade at different times. The opening auction is where overnight news and
orders placed by people who don't watch the market all day are met; the session is where
the active traders work. A stock whose gains have come at night for weeks has buyers who act
at the open; if those buyers are slow to change, the pattern continues. Both auctions can be
used with no spread: a market-on-close buy and a market-on-open sale (or the reverse), entered
before the cut-offs. Nothing in this repository has held only at night or only by day: the
swing search used 20-day overnight and daytime sums as features for 5- to 15-session holds.

## Rule

Each session D, each listed common stock with a market value of $50M or more, $250,000 a
day, a price of $5 or more, a previous session no more than five days earlier, and **no
results due** (no results 8-K accepted from 12:00 on D to 09:30 on D+1):

- **Night score:** the sum of the stock's overnight log returns (open against previous close)
  over the last 20 (or 60) sessions to D. **Day score:** the same for open-to-close returns.
- **Night book:** the 10 stocks with the highest night score in a size group, bought at D's
  close and sold at D+1's open.
- **Day book:** the 10 stocks with the highest day score, bought at D+1's open and sold at
  D+1's close.

Equal money in each. Costs per stock: the auction allowance and commission, both ways (as in
the earnings rule). A next-session move beyond 50% is dropped as bad data.

Sizes: $50M to $300M, $300M to $2B, $2B or more.

## Cells

2 books × 2 windows × 3 sizes = **12**, family `overnight_hold`.

## What counts (set now, for a book held one night or one day at a time)

The book's return each session after costs, averaged. Search 2010–2017: **0.08% or more a
session** (about 20% a year), weekly t of 3, six years of eight positive. Tests on 2005–2009
and 2018–2022, each cell that goes forward run once: 0.04% a session, weekly t of 2.5, four
years of five, in both. 2023 (to 13 October) is a check for a cell that passes. The holdout
stays sealed. The report gives each cell's yearly return and worst drawdown.

## Note on the raw data

While listing the raw Sharadar tables tonight (22:10 ET) to see what they hold, the first
three rows of ACTIONS, SP500 and SF3A were printed. They were rows from 2026 (three small
stock splits; institutional holdings of NVDA, AAPL and MSFT at 30 September 2026). No return
or price was shown, nothing was measured on them, and the extracted copies were deleted.
Every query on raw tables from now on is filtered to dates before 2023-11-09.
