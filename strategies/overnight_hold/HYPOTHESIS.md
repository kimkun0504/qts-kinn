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

**Search result, 2026-11-17 22:12 ET.** In REPORT.md. **No cell meets the bar at the costs set above.**
The day books lose before costs. The night books gain before costs in every size, most with
the 60-session score: 0.30% a night under $300M, 0.24% from $300M to $2B, 0.14% at $2B
and over (2010–2017, top 10 a night). The auction allowance (0.20% to 0.50% a round trip)
takes all of it: after costs −0.13%, −0.005% and −0.02%. 12 trials.

## Addendum, 2026-11-17 22:12 ET: is the night gain in the prices a seller actually gets?

Written after the search above, before any test period is looked at. The allowance is an
assumption written for a different trade (buy at the open, sell at the close), where the
tick check of 16 November found it about right. For a $2,000 market-on-close buy and
market-on-open sale, what is paid is commission and the exchanges' auction fees, if the
official close and open are prices that really printed and are large enough to fill
against. So the night books are priced again, conservatively, from minute bars:

- **Bought at D's official close only if** it lies inside the prices printed from 16:00 to
  16:05 in the minute data and those minutes traded $100,000 or more. Otherwise that stock
  is left out that night.
- **Sold at the lowest price of D+1's first regular minute** (09:30), not at the official
  open, and only if that minute traded $50,000 or more (otherwise sold at that minute's low
  anyway, and counted).
- **Costs:** commission and auction fees both ways, $0.0045 a share with a floor of 0.0175%
  a side. No other allowance.

The six night cells (2 windows × 3 sizes), same picks, same bar: search 2010–2017 at 0.08% a
session, weekly t of 3, six years of eight; each cell that meets it goes once to 2005–2009
and 2018–2022 at 0.04%, t of 2.5, four years of five. **6 cells**, charged to
`overnight_hold`. This re-reading is made after seeing the search years; the test periods
of this family have not been looked at.

**Result of the re-pricing, 2026-11-17 22:16 ET.** **Every one of the 6 cells loses** (−0.25% to −0.49% a
night). Two reasons, from a look at the picks of the search years afterwards: only 18% to 56%
of picks (small to large) have any minute bars from 16:00 to 16:05, so one to three stocks a
night are left; and the lowest price of the first minute is on average about 0.5% under the
official open (the median gap is 0% to 0.1%; the average is a few opening collapses). A
market-on-open order fills at the opening cross, which the tick check of 16 November found
to be the official open in 86% of cases, not at that minute's low; the test above used a
price no such order receives. It stands as written: failed. 6 trials.

## Addendum, 2026-11-17 22:16 ET: the auction prices, where both auctions can be seen

Written before it is measured; the test periods of this family are still unseen. A last
reading, at prices a market-on-close and market-on-open order do receive:

- A stock counts on a night only if **its official close lies inside prices printed from
  16:00 to 16:05** in the minute data (any amount) and **D+1's first regular minute opened
  within 0.2% of the official open** (the opening cross printed there). Otherwise it is left
  out that night; the book holds the rest of its ten.
- Bought at the official close, sold at the official open. Costs: commission and auction
  fees, as in the re-pricing. No other allowance.

The six night cells, the same bar. **6 cells.** A cell that passes is "auction-dependent"
in the sense of the swing search's rule of 16 November and is a lead to confirm with ticks,
not a finding.
