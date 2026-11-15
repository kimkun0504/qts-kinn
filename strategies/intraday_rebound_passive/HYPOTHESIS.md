# Hypothesis: passive entry after a no-news drop

Written 2026-11-15 by claude, before any test of it. Same family as `intraday_rebound`.

## Rationale

The market-order form of the rebound failed on costs: the bounce is +0.90% gross, and the quoted
half-spread at the entry is 27 bps at the median (53 at the mean), paid twice. A buyer who rests a
limit order **at the bid** pays no spread on the way in. The catch is adverse selection: a
resting bid is filled when someone sells into it, which is more likely when the price is about to
fall further. The question is whether what is saved on the spread is larger than what is lost by
being filled on the wrong events.

## Events and universe

Exactly the events of the `intraday_rebound` event study
(run `20261115T191143Z_claude_intraday_rebound_217e2dd7`), restricted to the 420-event quote sample
already drawn (70 per liquidity bucket per period, seed 0; decision 0012). No new selection.

## The order (one definition, fixed here)

- At the start of the minute after the event bar, place a buy limit **at the best bid** quoted at
  that instant. Skip the event if there is no valid quote.
- The order rests for **10 minutes**, then is cancelled.
- **Filled** only if a trade prints **strictly below** the limit during those 10 minutes (the
  price traded through us; conservative about queue position). The fill price is the limit.
- A filled position is sold in the **closing auction** at the official close.
- $500 a position, whole shares. Costs from the platform model: commission and fees for a passive
  buy and an auction sell, plus the model's auction slippage. No spread on either leg.

## What is measured, and what counts

- **Primary:** mean net return per **filled** order, with a 95% interval resampling whole sessions,
  over the whole sample (equal-weighted across the six cells, so not the population average).
- Also reported: the fill rate; net per *placed* order (unfilled = 0); the same with a lenient fill
  rule (a trade at or below the limit); the market-order result on the same events with real
  spreads (buy at the ask, same exit), for comparison; each by liquidity bucket and period.
- **Worth developing** if all hold: net per filled order is at least **+0.5%** with an interval
  above zero; the fill rate is at least **30%**; and the result is positive in 2017–2023 alone.
- **Not worth developing** otherwise.

## Risks to the hypothesis

1. **Adverse selection**, as above. This is the main one.
2. **Small sample**: at most 420 orders, fewer filled. Intervals will be wide.
3. **Queue position**: the strict rule may understate fills; the lenient rule overstates them.
   Truth is between.
4. **The exit**: selling a thin stock in the closing auction may move the price. The model charges
   10 bps; no auction data is available to check it.
5. **Not the population**: the sample is equal across liquidity buckets, while real events are
   not. Bucket results matter more than the pooled number.

## Prior looks at this data (they count)

Everything in `intraday_rebound/HYPOTHESIS.md`, plus that event study and its quote sample, which
motivated this idea. The earlier build's best lead was also a resting limit order (at the open, in
micro caps). This is therefore a follow-up shaped by the data, not independent evidence. The
family is charged 10 trials before this one.
