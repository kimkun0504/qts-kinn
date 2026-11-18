# Night bids: resting buy orders below the market after hours

Written 2026-11-17 20:45 ET, before anything is measured. The owner's thought: "one thing I also think
has a big edge is after hours trading. Especially if trading sizes are below 5k."

## Why

Every test so far predicted where a price would go. This one does not predict. After 16:00
almost nobody is quoting, so a seller in a hurry has to take whatever bid is there, and the
price can drop several percent on a few thousand dollars. At 09:30 the whole market is back.
If such drops are mostly about nobody being there, the one buyer who was there is paid for
it by the next open. A fund cannot do this (the size is a few thousand dollars a stock). An
account of this size can.

The danger is the opposite case: the seller knows something (an offering, a warning), the
order is filled, and the stock opens lower still. Whether the first outweighs the second is
the whole question, and only the measurement can say.

## Rule

Each session D, each listed common stock with a market value of $50M or more and $250,000
a day, **no results due** (no results 8-K accepted between 12:00 on D and 09:30 the next
session; report dates are announced ahead):

- A buy order rests at the official close × (1 − x), for x of **3%, 5% and 8%**, from 16:05
  to 19:59.
- **Filled** only when the after-hours market trades through it and stays under it: minutes
  from 16:05 whose **high** is under the order's price, adding up to at least 5 trades and
  $5,000. The price paid is the order's price. A single stray print does not count.
- **Cancelled before the fill** if the company files anything we hold (8-K, prospectus,
  shelf, and the other downloaded forms) between 16:00 and the first minute under the order.
  A program can read the SEC feed live; nothing later than the fill is used.
- **Sold** at the next session's open, or at its close.

Dropped as bad data: a stock-day whose last regular minutes (15:55 to 16:00) are more than
2% from the official close. Costs: commission both ways and the auction allowance on the
sale; no spread on the purchase, which is a resting order.

Sizes: $50M to $300M, $300M to $2B, $2B or more.

## Cells

3 depths × 3 sizes × 2 exits = **18**, family `night_bids`. A deeper order is also inside
the shallower one's fills; each depth is its own rule.

## What counts

Search 2010–2017: 150 trades, 1% after costs, weekly t of 3, six years of eight. Tests on
2005–2009 and 2018–2022, each cell that goes forward run once: 0.5%, t of 2.5, four years
of five, in both. 2023 (to 13 October) is a check for a cell that passes and is not looked
at otherwise. The holdout stays sealed. For every cell the report gives the worst trade and
the worst 1%, and how many of the fills were followed by a filing the next morning.

## What the data cannot show

There are no after-hours quotes on disk, only trades by the minute. The fill rule is built
to be on the careful side (the whole minute under our price, several trades), but whether an
order at a retail broker would have been the one filled is not proven until it is tried.
