# Index deletion: a company dropped from the S&P 500 that stays listed

Written 2026-11-17 23:30 ET, before anything is measured. Funds that track the S&P 500 must sell a
deleted company at the close of the day the change takes effect, whatever they think of it.
Published work finds that such stocks, when they stay listed (most move to a mid-cap index),
recover over the following weeks as the forced selling ends. It is a long trade in companies
large enough to trade at any size.

## Events

Sharadar's S&P 500 changes (action "removed", dated at the change, read before 2023-11-09), 2005
to 13 October 2023, for a company that still trades 20 sessions later (not an acquisition or a
bankruptcy). **D** is the first session on or after the change date.

## Trade

Bought at the open of D+1, sold at the close 20 or 60 sessions later. Costs: the auction
allowance and commission. Each trade is measured against every stock of $2B or more bought at
the same open and held as long.

## Cells

2 holds = **2**, family `index_deletion`.

## What counts

Search 2010–2017 against the average large stock: 1% a trade for 20 sessions, 2% for 60, weekly t
of 3, six years of eight, positive after costs; there are about 75 such companies in these
years, so the count is reported and does not stop a cell that meets the rest. Tests on 2005–2009
and 2018–2022 at half those, t of 2.5, four years of five. 2023 is a check. The holdout stays
sealed.
