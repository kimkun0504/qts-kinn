# Five dollars: a small company that climbs back over $5

Written 2026-11-17 22:54 ET, before anything is measured. Many funds may not own a stock under $5, and
brokers do not lend against one. A company that has traded under $5 for months and climbs
back over it becomes buyable, and marginable, for a whole class of money at once. If that
money arrives over weeks, the price should drift up after the crossing. Nothing in this
repository has used a price level as a signal.

## Events

A listed common stock that **closed under $5 on each of the 60 sessions before** and then
closes at $5 or more (raw price, as funds and brokers see it), with a market value of $50M
or more and $250,000 a day. Two confirmations: the **first close** over $5; or **five
closes in a row** at $5 or more (signal on the fifth). One event a company in 120 sessions.
No results 8-K in the two sessions up to the signal (a jump on results is A50's business).
2005 to 13 October 2023.

## Trade

Bought at the next open, sold at the close 20 or 60 sessions after the signal. Costs: the
auction allowance and commission, as the earnings rule. Each trade is measured against every
stock of its size group bought at the same open and held as long.

Sizes: $50M to $300M; $300M or more.

## Cells

2 confirmations × 2 holds × 2 sizes = **8**, family `five_dollars`.

## What counts

As `dividend_signal`: search 2010–2017 against the average stock, 1% a trade for 20 sessions
and 2% for 60, a weekly t of 3, six years of eight, positive after costs; tests on 2005–2009
and 2018–2022 at half those, t of 2.5, four years of five, in both. 2023 is a check. The
holdout stays sealed.
