# Hypothesis: intraday momentum and VWAP

Written 2026-11-16 00:25 ET, before any measurement. Owner's direction after the rebound family
was parked: momentum and VWAP, intraday only.

## Rationale

A move that starts on unusual volume tends to continue for the rest of the session: news is
absorbed over hours, and large orders are worked through the day. The other side is whoever
fades the first move too early. This is the opposite bet to the rebound, and it does not need
the first second after an event: the rules below act on bar closes or on resting stop orders.

Three published rule sets are tested as written, not invented here. All three come from the
same authors (Zarattini, Aziz, Barbon), one of whom runs a trading school, and an independent
replication of the VWAP paper found a Sharpe near 0.7 out of sample against the 2.1 reported.
The development years here (2003 to 2016) come before two of the three papers' samples, so
this is mostly an out-of-sample test of their claims.

## The rules

**A. Opening range breakout on stocks in play** ("A Profitable Day Trading Strategy for the
U.S. Equity Market", 2024; their sample 2016 to 2023).

- Universe each day: first regular-session price above $5; mean daily volume of the prior 14
  sessions at least 1,000,000 shares; mean true range of the prior 14 sessions above $0.50; no
  split in those sessions.
- In play: volume in the first 5 minutes at least equal to the stock's mean first-5-minute
  volume over the prior 14 sessions. The 20 highest ratios each day are the candidates.
- Direction: first 5 minutes closed above their open: long only. Below: short only.
- Entry: a stop order at the high of the first 5 minutes (long) or the low (short), live from
  09:35.
- Exit: a stop 10% of the 14-day mean true range from the entry, otherwise the close.

**B. VWAP trend** ("VWAP: The Holy Grail for Day Trading Systems", 2023; QQQ, 2018 to 2023).
Long while the one-minute close is above the session's volume-weighted average price, short
while below, flat at the close. Trades at the next bar's open.

**C. Noise-area momentum** ("Beat the Market", 2024; SPY, 2007 to 2024). For each time of day,
the noise is the mean absolute move from the open to that time over the prior 14 sessions. At
each half hour from 10:00, a price above the open (or the prior close, whichever is higher)
plus the noise is a long; below the mirror level is a short. A long is closed when the price
falls under the higher of that level and VWAP, and the reverse for a short. Flat at the close.

## Variants measured (10 trials, counted against the family)

| | Variant |
|---|---|
| A1 | A as written, long and short |
| A2 | A, long side only (the engine is long only today) |
| A3 | A with a 15-minute opening range |
| A4 | A1 with a VWAP exit in place of the fixed stop: out when a one-minute close crosses VWAP |
| B1, B2 | B on QQQ: long and short; long only (flat below VWAP) |
| B3, B4 | B on SPY: long and short; long only |
| C1, C2 | C on SPY; on QQQ |

## Sizing and costs

- $20,000 margin account, no compounding. The $25,000 day-trading minimum was abolished on
  2026-06-04, so an account this size can day trade on margin; a broker may still phase the
  new intraday margin rules in.
- A: $4,000 a position, up to 20 at once (4 times the account, the intraday limit). B and C:
  one $20,000 position.
- Commission $0.0035 a share, $0.35 minimum an order. Slippage at 1×: 5 basis points a side
  for A (stop orders in fast stocks), half a cent a share for B and C. Reported at 1×, 2× and,
  for A, 4×.
- Shorting cost and availability are ignored. Stocks in the news are often hard to borrow, so
  the short side of A is an upper bound.

## Known weakness of the test, stated now

A's stop is about 0.3% to 0.5% of the price, narrower than many one-minute bars in these
stocks. Bars cannot say whether the stop was touched before or after the high. Rule used: in
the entry bar the stop counts only if the bar closes beyond it; in later bars it counts when
the low (or high, for shorts) reaches it, filled at the stop or at the bar's open if that is
worse. This is the usual convention and it flatters tight stops. Any variant that passes needs
a check against real trades before anything else.

## What would count as support, and as failure (development, 2003-09-10 to 2016-12-30)

The owner's target of 1% net a trade was set for the rebound. Momentum with a tight stop earns
a small amount on many trades, so that number does not apply; the bars below replace it for
this family, **subject to the owner's confirmation before any validation run**.

A variant goes forward only with all of:

1. Sharpe of daily profit, at 2× slippage, at least 1.0;
2. net profit at 2× positive in at least 11 of the 14 calendar years;
3. worst drawdown at 2× under $10,000;
4. net profit at 2× of at least $2,000 a year on the $20,000 account (10%);
5. for A: Sharpe still at least 0.5 at 4× slippage.

If several pass, the highest Sharpe at 2× goes forward. If none passes, the family is parked.

After a pass: the rule is built into the engine (A needs stop entries, and shorts for A1), one
validation run with bars set before it, a fill check against real trades, and only then the
holdout, which is still clean for this family.

## Risks to the hypothesis

Published by authors with something to sell; in-sample selection in the papers (the 5-minute
range and the 10% stop were the best of several); stop fills on bars; crowding since
publication; hard-to-borrow shorts; for B, costs on dozens of trades a day.

## Prior looks at this data

Astra tested three momentum ideas on these development years and parked all three: a volume
surge (−1.65% a trade at 2×), an opening gap continuation (−0.13%) and filing-session momentum
(−0.37%). None used an opening range with a tight stop, or VWAP on an index ETF. Their gross
returns to the close were +0.4% or less, which is a warning for A.
