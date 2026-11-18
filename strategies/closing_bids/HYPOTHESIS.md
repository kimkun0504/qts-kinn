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
