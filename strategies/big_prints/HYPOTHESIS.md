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
