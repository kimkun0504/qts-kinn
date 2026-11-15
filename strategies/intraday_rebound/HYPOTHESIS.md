# Hypothesis: intraday rebound after a no-news drop

Written 2026-11-15 by claude, before any Kinn test of it. Changes go in dated addenda below.

## Rationale

A stock that falls sharply within a session **without news** is often being pushed by one
impatient seller (a liquidation, a stop cascade, a large order worked badly) rather than by new
information. Liquidity providers step back while the selling lasts and return when it ends, so
part of the fall reverses within the session. The buyer is paid for providing liquidity when it
is scarce. Who loses: the forced seller. Why it could persist: the trade is small, uncomfortable
(falling knives) and capacity-limited, so large funds do not compete it away.

When there *is* news, the fall is information and should not reverse. Separating the two cases
is the whole strategy.

## Universe (point in time, known before the open)

US domestic common stocks listed on an exchange, with a prior close of at least $1.00, a 20-day
median dollar volume of at least $250,000, and at least 20 prior sessions.

## Event definition (one definition, fixed here; no search in this phase)

The **first** regular-session one-minute bar, from 09:35 to 15:00 New York, whose **close** is at
least **10% below** the split-adjusted prior close, on a day when:

1. **the drop is intraday, not a gap:** the session's first bar opened no lower than 5% below
   the prior close;
2. **no news, as far as can be known at that minute:**
   - no 8-K filing for the company since the prior session (Sharadar EVENTS dated from the
     prior session up to, not including, today);
   - pre-market dollar volume (04:00–09:29) under 5% of the 20-day median dollar volume.

Features and when each is available:

| Feature | Available |
|---|---|
| prior close, 20-day dollar volume, filings since the prior session | before the open |
| pre-market dollar volume, the first bar's open | when their bars close |
| return from the prior close | at each bar's close |

**Action studied:** a market buy at the open of the bar after the event bar. $500 a position.

## What is measured, and what counts

The mean forward return from that entry, by minutes held (1 to 240, capped at the close) and to
the official close, gross and net of the platform cost model at 1× and 2× slippage, with 95%
confidence intervals that resample whole sessions.

- **Primary measure:** net return held to the close, 1× slippage, full sample.
- **Worth developing** if all hold: the primary measure is at least **+0.5%** with a confidence
  interval above zero; it is positive in 2017–2023 taken alone; and it is positive at 2×
  slippage.
- **Not worth developing** otherwise. The owner's target of 3–4% net a trade is noted; this
  phase reports how far the plain event is from it.

Reported splits, fixed in advance, for reading only: by year; by liquidity (20-day dollar volume
under $1M, $1–10M, $10M and over); by time of the event (before 11:00, 11:00–13:00, after).

## Risks to the hypothesis

1. **The news filter is weak.** 8-K filings miss most news (press releases, analyst notes,
   sector news), and a same-day 8-K is not knowable at the event minute. Many "no-news" drops
   will have news.
2. **Fills.** A market order after a 10% drop in a thin stock pays a wide spread. The data has
   no quotes; the cost model's spread is a conservative fallback, not a measurement.
3. **Bad prints.** A single erroneous trade can look like a 10% drop. The event uses a bar's
   close, which helps, but does not remove this.
4. **Market-wide selloffs.** On days when everything falls, drops do not reverse the same way.
5. **Fading.** The earlier build found the related effect near zero in 2020–2023.
6. **Capacity.** The effect, if any, is expected in the least liquid names.

## Prior looks at this data (they count)

The earlier build tested the same idea on the same window (docs/retired/intraday-rebound-v0.md):
6 pre-registered trials and about 2,300 exploratory variants, with a best conservative estimate
near +2% a trade for a *resting limit order at the open* in micro caps, and +0.2% to +1.5% for
*reacting after the print*, which is what this event study does. So the result here is expected
to be positive but small, and it is a **replication on a new engine, not independent evidence**.
The only untouched evidence is the holdout.

The family `intraday_rebound` is charged 9 prior trials (6 pre-registered and 3 logged
exploratory looks). How to charge the 2,300 variants is an open owner decision.
