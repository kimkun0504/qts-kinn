# Closing bids: a limit-on-close order under a stock pushed down in the last ten minutes

Written 2026-11-17 21:09 ET, before anything is measured. Tonight's `night_bids` took the owner's
thought (a small account paid for being the buyer when nobody else is) to after-hours
trading and found the order is filled by people who have read the news. The same thought
belongs where there is selling without news.

## Why

In the last minutes of the session funds have to finish their orders, and the closing
auction takes whatever is left at one price. Results and most announcements come after
16:00, so a stock that drops in the last ten minutes is mostly being pushed, and the push is
gone by the next morning. A fund cannot buy much of it (the auction is the liquidity); a
$2,000 order can. The order type exists for it: a limit-on-close order, entered before the
exchange's cut-off (15:50 to 15:55), is filled at the closing price only if that price is at
or under the limit.

## Rule

Each session, each listed common stock with a market value of $50M or more and $250,000 a
day, no results due that evening or the next morning, that traded between 15:40 and 15:49:

- At 15:49 a **limit-on-close buy** is entered at the last price × (1 − x), for x of **2%, 3%
  and 5%**.
- **Filled at the official close** if the close is at or under the limit, and only if the
  closing minutes (16:00 to 16:05, where the auction prints) traded $50,000 or more, so that
  there was an auction to be filled in.
- **Sold** at the next session's open, or at its close.

Dropped as bad data: a close more than 30% under the 15:49 price. Costs: the auction
allowance and commission, both ways.

Sizes: $50M to $300M, $300M to $2B, $2B or more.

## Cells

3 depths × 3 sizes × 2 exits = **18**, family `closing_bids`.

## What counts

Search 2010–2017: 150 trades, 1% after costs, weekly t of 3, six years of eight. Tests on
2005–2009 and 2018–2022, each cell that goes forward run once: 0.5%, t of 2.5, four years of
five, in both. 2023 (to 13 October) is a check for a cell that passes. The holdout stays
sealed. The report gives the worst trade and the worst 1% of every cell, and how many
orders a year fill.

## What the data cannot show

Whether the stock had an auction, and at what price our order would have stood in it, is
read from trades by the minute and the official close. The cut-off times changed over the
years (15:45 to 15:50 on NYSE, 15:50 to 15:55 on Nasdaq); 15:49 is used throughout.

**Search result and a data check added before any test, 2026-11-17 21:12 ET.** Search: two cells met the
bar, both in companies of $2B or more with a close 2% or more under the 15:49 price (265
fills in eight years): sold at the next open 1.44% after costs (weekly t 3.71, seven years
of eight, 70% winners), sold at the next close 2.08% (t 3.56, eight of eight). Every other
cell was positive too, which a wrong closing price in the daily table would also produce
(a close recorded too low makes a fall and a rebound out of nothing). So before the tests,
one check is added to the rule, in the direction that can only remove trades: **the official
close must lie inside the prices that actually printed between 16:00 and 16:05 in the minute
data** (from a different vendor than the daily table). The search is re-read with it, the
two cells are re-judged, and only then tested. Recorded here as a change made after seeing
the search years; the 18 cells are counted once.

**Results, 2026-11-17 21:15 ET.** In REPORT.md. With the data check the search has one cell over the bar:
$2B or more, close 2% or more under the 15:49 price, sold at the next open: 1.28% after costs
on 173 fills, weekly t 3.30, **eight years of eight**, 65% winners, worst −13% (the −81% in
the first reading was a wrong close and the check removed it). Tested once on each period:
2005–2009 1.51% (857 fills, four years of five, **weekly t 0.33**); 2018–2022 1.35% (1,521
fills, four of five, **weekly t 1.37**). **Not passed:** the t fails in both. The average is
the same in all three periods and positive in 16 of 18 years, but four fifths of the test
fills are in 2008 and 2020, and week to week in those years the result swings too far for
the test. 18 cells and 2 test runs: 20 trials.

## Addendum, 2026-11-17 21:15 ET: can it be done without the auction order, and is it the market?

Written before it is measured, and after all three periods of the cell above were seen, so
nothing below is a blind test. Two questions decide whether the lead is usable:

- **Bought after the close instead.** A limit-on-close order has to be resting in every
  large stock at 15:49, which an account of this size cannot fund. The usable version looks
  at 16:01 for stocks of $2B or more that closed 2% or more under their 15:49 price and buys
  them after hours: **at the high of the first minute that trades from 16:06 to 16:20**. Sold
  at the next open. 1 cell.
- **With SPY sold short at the close and bought back at the next open**, for the same
  dollars (0.03% added for its costs), on the auction fills. If the gain is the market's own
  overnight rebound after a late sell-off, this is near zero and the trade is simply SPY. 1
  cell.

**2 cells** on the search years, the same bar; the other two periods are shown beside them
because they are already known for the base cell. Charged to `closing_bids`.

**Results of the two follow-ups, 2026-11-17 21:19 ET.** In REPORT.md. In the search years the fills are
scattered (173 fills on 149 days), SPY did nothing overnight after them (+0.05%), and the
hedged trade made 1.20% (weekly t 3.23, seven years of eight): the stocks' own rebound. In
the two test periods two thirds of the fills are on days with ten or more (market-wide
sell-offs into the close, mostly 2008 and 2020), SPY itself was up 1.0% to 1.1% by the next
open on those fills, and the hedged trade made 0.35% and 0.32%. Bought after the close
instead: 0.91% in the search years (143 of the 173 traded after hours; weekly t 2.08, under
the bar), 1.21% and 1.32% in the other two. 2 cells; `closing_bids` has 22 trials.

So there are two things here. A large stock pushed down alone into the close comes back by
the morning (about 20 a year, 1.2% each, and it has to be bought in the auction). And when
the whole market is sold into the close, the market itself comes back overnight.

## Addendum, 2026-11-17 21:19 ET: the market itself after a late sell-off (SPY, QQQ, IWM)

Written before it is measured. What is already seen: SPY's overnight return averaged over
the stock fills above (near zero in 2010–2017, about 1% in the other two periods, weighted
towards the worst days of 2008 and 2020). Not seen: the funds' own late falls, day by day.

**Rule.** For SPY, QQQ (QQQQ before 2011) and IWM, each session: if the price at 15:58 is
**0.5% or more** (or **1.0% or more**) under the price at 15:49, **buy at the high of the
15:59 minute** and **sell at the next session's open**. Costs 0.03% a round trip plus
commission. An overnight move beyond 15% either way is dropped as a split or bad data.

Cells: 3 funds × 2 depths = **6**, charged to `closing_bids`.

**What counts.** One fund cannot make 150 trades in eight years, so the bar is set for this
part now: over 2005–2022 together at least 40 trades, 0.3% a trade after costs, a weekly t
of 3, and a positive average in each of 2005–2009, 2010–2017 and 2018–2022 separately. All
three periods are used, so there is no untouched test: a cell that clears this is a **lead
to follow on paper**, not a pass. 2023 to 13 October is its only unseen check.

**Results for the funds, 2026-11-17 21:20 ET.** In REPORT.md. **No cell clears the bar.** After a fall of
0.5% or more in the last ten minutes, bought in the last minute and sold at the next open:
SPY +0.11% on 63 trades (weekly t −0.15), QQQ +0.09% on 69, IWM −0.24% on 91, each negative
in at least one period. After a fall of 1% or more the averages are 0.4% to 1.4%, on 18 to 20
trades in eighteen years. The 1% seen over the stock fills came from weighting the worst
days by how many stocks they hit. 6 cells; `closing_bids` has 28 trials.
