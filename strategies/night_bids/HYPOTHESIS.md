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

**Results, 2026-11-17 20:51 ET.** In REPORT.md. **Every one of the 18 cells loses**, in every search
year for 14 of them: −0.9% to −8.5% a trade after costs, weekly t from −3.8 to −11.5. The
median fill loses little (−0.3% to −1.2% to the next open for the 3% and 5% orders in
companies of $300M or more) and the average is pulled down by collapses of 50% to 87%:
FXCM on 15 January 2015, NVAX on 15 September 2016, drug-trial failures told by press
release after the close with no SEC filing until the next day. A quarter to two fifths of
the fills were followed by a filing before the next open. The resting buyer after hours is
filled by someone who has read the news. 18 trials. No tests run (nothing met the bar).

## Addendum, 2026-11-17 20:51 ET: trading with the move instead (the price as the news feed)

Written before it is measured, and after seeing the result above on the search years: a fall
after hours with real trading and no results due is, more often than not, news that has not
reached a filing. So the same reading may work as a detector of news, in both directions.
That the falls continue from the order's price is known from the search years; what a trader
who acts **after** the signal gets is not, and neither is anything about rises.

**Signal.** As above (common stock, $50M, $250,000 a day, no results due, no filing of ours
since 16:00, the bad-data rule), at the first minute T from 16:05 by which the minutes lying
wholly beyond the level add up to 5 trades and $5,000:

- **Fall** of 3%, 5% or 8%: minutes whose high is under the close × (1 − x).
- **Rise** of 3%, 5% or 8%: minutes whose low is over the close × (1 + x).

**Trade**, in the first minute that trades after T (within 20 minutes, by 19:59):

- Rise: **buy at that minute's high**; sold at the next open, or the next close.
- Fall: **sell short at that minute's low**; bought back at the next open. A borrow fee of
  10% a year for the night. This side also says what a holder should do with a position
  that falls after hours, which matters whether or not shorts can be borrowed.

Cells: rise 3 levels × 3 sizes × 2 exits = 18; fall 3 levels × 3 sizes × 1 exit = 9.
**27 cells**, charged to `night_bids`. What counts: as above. For the short cells the
report gives the worst trade and worst 1%.

**Results of trading with the move, 2026-11-17 20:56 ET.** In REPORT.md. **None of the 27 cells meets
the bar and 25 lose.** Buying a rise at the next minute's high lost 0.6% to 2.2% a trade in
companies of $300M or more (weekly t −3 to −8, winners 34% to 38%); selling a fall short at
the next minute's low lost 0.2% to 1.7%. Both directions lose because the price does not
move on after the signal (a stock first seen 5% up is paid for at 7.0% up and opens 5.6% up;
one first seen 5% down is sold at 7.1% down and opens 6.4% down) while a minute's best and
worst prices after hours are 1% to 3% apart. Read with the first part: after hours the middle
price is about right, the taker pays the gap, and the resting order is picked off by news.
27 cells; `night_bids` has 45 trials. No tests run.

**Correction, 2026-11-17 21:05 ET.** The paragraph above gave two figures from memory that the check
does not support. Measured: a stock first seen 5% up is paid for at 7.0% up and opens **6.2%**
up, not 5.6% (medians, $300M to $2B); and the entry minute's best and worst prices are the
same in half the cases, more than 1.1% apart in a quarter and more than 2.5% apart in a tenth
(2015), not "1% to 3% apart". The loss from following the move is a small overshoot that is
given back by the open (about a tenth of the move, in both directions), plus costs. The
counts, returns and verdict are unchanged. REPORT.md carries the corrected reading.
