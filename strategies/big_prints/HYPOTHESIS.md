# Big prints: a quiet up day traded in unusually large pieces

Written 2026-11-18 00:01 ET, before anything is measured. An indicator of our own. A fund that is building
a position trades in larger pieces than the crowd, and takes days or weeks to finish. On a
day when a stock's average trade (shares traded ÷ number of trades) is far larger than its
own normal, with more volume than usual, a modest rise and no filing, the likeliest story is
a large buyer at work; if the buying continues, the price should drift up after the day.

## Indicator

For each stock and session D: average trade size = volume ÷ transactions from the daily bars
(`transactions` in the vendor's day bars). **Footprint** = that size ÷ its geometric mean over
the 60 sessions before D.

## Events

Common stock, $300M or more in market value, $1M a day or more, $5 or more, 2005 to 13
October 2023, on a session D with:

- footprint of 2 or more;
- dollar volume of 1.5 times the 20-day average or more;
- close 0% to 4% above the previous close (up, but not a news jump);
- no 8-K by the company whose reaction session (first close after acceptance) is D or D−1;
- a stock-specific day: under 5% of these stocks have a footprint of 2 or more on D (index
  rebalances, where large closing trades hit many stocks at once, drop out).

## Trade

Bought at the open of D+1, held 10 or 20 sessions. Costs: the auction allowance and
commission. Measured against the average common stock of the same size bought at the same
open and held as long.

## Cells

size ($300M–$2B, $2B and over) × hold (10, 20) = **4**, family `big_prints`.

## What counts

Search 2010–2017: 150 trades, 1% a trade over the average, weekly t of 3, six years of eight,
positive after costs. Tests on 2005–2009 and 2018–2022 at 0.5%, t of 2.5, four years of five.
2023 is a check. The holdout stays sealed.

## Follow-up: a stronger footprint, and smaller companies (written 2026-11-18 00:02 ET, after the 4 cells)

The mid-sized cells beat the average in all eight years by about half a point. If the reading
is a large buyer, a larger footprint, and companies where a fund's order is a larger part of
the volume, should show more. **4 cells, held 20 sessions only:** $300M–$2B with a footprint
of 3 or more, and of 4 or more; $50M–$300M ($250,000 a day, $2 or more) with a footprint of 2
or more, and of 3 or more. Every other condition as above (the share of footprint days is
counted within each size). Same bars. These were chosen after seeing the first four cells, so
the search years carry less weight than the tests.

## Checks for the passed cell (written 2026-11-18 00:03 ET, after both tests passed)

1. **2023** (to 13 October): the same cell, read once.
2. **Is it the trade size, or only a quiet up day on heavy volume?** The same events with a
   footprint under 1.2 (an ordinary trade size), $50M–$300M, 20 sessions, in all three periods.
   If these do as well, the indicator adds nothing to the known high-volume premium.
3. **Year by year after costs**, and the share of signals in 2018–2022 whose stock trades
   under $1M a day (the price paid is least certain there).

Each is one trial: 3.

## Check 4: stocks that stop trading inside the hold (written 2026-11-18 00:04 ET)

The tables so far keep only signals whose stock still trades 20 sessions later, which drops
companies taken over or delisted in the hold. The passed cell is read again with the last
close inside the 20 sessions in place of the 20th (as the after_hours study does), in all
three periods and 2023. One trial.
