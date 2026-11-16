# Hypothesis: earnings drift in companies of $50M to $300M

Written 2026-11-16, after the rule was found and tested in
[`strategies/swing_search`](../swing_search/REPORT.md) (rule A50) and before any run of this
folder. This folder holds the rule as something `kinn swing` can run, so that the owner can
run it once on the holdout. It adds no new idea and no new parameter.

## The rule, frozen

- **Signal,** read at a close: the company is common stock worth $50M to $300M, closed at $1
  or more and normally trades $250,000 or more a day; it filed an earnings 8-K on the
  previous session or since; its two-day return is 15% or more; the larger of the two days'
  dollar volume is at least five times normal.
  A stock whose previous session was more than 7 days earlier gives no signal: its "two-day
  return" would span a halt. The research scripts did not have this line; it removes nine
  of their 1,488 trades of 2005 to 2022, stocks back from a halt or a relisting.
- **Trade:** buy at the next open, sell at the close 15 sessions after the signal day. If the
  stock stops trading first, the position ends at its last close with the forced-exit cost.
- **Book:** $20,000, 10 positions of $2,000, no leverage. A signal needs a free slot at the
  open; when several arrive together the one with the most volume against normal goes first.
- **Costs:** commission and fees from the cost model; slippage at 1× is an allowance for
  joining the auctions (25 bp a side under $1M a day, 10 bp to $10M, 5 bp to $100M, 2 bp
  above); 2× doubles it. The result with the quoted spread crossed is reported beside them.

## Why it might be real

A small company's good earnings reach few investors on the day. The search found the drift in
2010 to 2022, and it then passed on 2005 to 2009, on 2018 to 2022 as a test of the $50M floor,
and was not contradicted by 2023. It is the long-documented drift after earnings, in the
stocks too small for funds to trade.

## Why it might not be

It was picked out of about 12,000 cells. The profit is in the best 5% of trades. The allowance
for auction fills is assumed, not measured. Half the account can be lost in the 10-position
book.

## Runs planned

1. `research` and `early`: the search years and 2005 to 2009, to confirm that this code
   reproduces the research scripts' trades. These add no trial: same rule, same data.
2. `holdout`: 2023-11-09 to 2026-11-06, once, by the owner, with `--unseal`. Set now: the rule
   **passes** if the mean a trade at 2× is 1% or more and the run's total at 2× is positive;
   it **fails** if the mean a trade at 1× is zero or less. In between it is unproven.
   About 250 trades are expected, so the mean will be known to about ±1.5%.
