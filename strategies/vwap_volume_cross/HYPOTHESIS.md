# VWAP cross with a turnover surge

Registered before any run. The owner's observation is that a
stock sometimes accelerates when it crosses above its session
VWAP on explosive volume. A brief cross can also be the last
part of a move. This study tests whether unusually high turnover
at the cross adds information beyond the same price sequence with
ordinary turnover. It waits for another completed block before
entry, so an apparent payoff during the cross is excluded.

Count both registered studies in `intraday_rebound`. There were
48 family trials at the start of this research and 97 at the close
of the late rally selloff. Related work includes the gap washout
VWAP reclaim, standalone turnover momentum, and the owner's VWAP
discussion. The earlier washout required a large gap and selloff.
Here the session VWAP cross and its turnover determine eligibility.

## Frozen definition

- Use listed domestic common stocks, including later delistings
  while eligible. Require 20 prior matched sessions, prior
  split-adjusted close of at least $2, median prior 20-session
  dollar turnover of at least $1 million, and prior market cap
  from $50 million inclusive to $2 billion exclusive.
- Partition the regular session into five-minute clock blocks,
  starting at 09:30. Estimate cumulative VWAP using the sum of
  valid minute close times share volume divided by the cumulative
  valid shares. Require positive finite prices and positive volume
  for contributions. Exclude premarket. This is a trade-bar proxy.
- Scan cross blocks ending in bar labels 10:04 through 13:59 ET.
  Require actual, valid last-minute closes for the preceding
  block, the cross block and the immediately following block.
  The preceding block's last close must be strictly below
  regular-session VWAP through that close. Take that VWAP as a
  fixed reference. The cross block must end at least 2% above
  the reference. The following block must end above it too and
  its last bar must turn over at least $40,000. Require at least
  75 clock minutes from the confirmation bar label to the
  exchange calendar close.
- Take the first such price-and-liquidity setup per stock,
  independent of the cross-block turnover classification.
  Compare that block's turnover, in dollars estimated from valid
  minute bars, with the median turnover of the six immediately
  preceding five-minute blocks, all in the regular session.
  Require this median to be positive for a turnover classification.
  Missing bars contribute no observed turnover. This measures
  acceleration against the same stock's preceding 30 minutes.
  The current strategy interface exposes prior full-day turnover.
  It lacks a historical same-clock baseline, so this comparison
  can be affected by time of day.
- Buy at market only in the next clock minute after the
  confirmation block, and expire at the end of that minute.
  Hold for 60 clock minutes from the first fill and then sell
  at market with the standard same-day auction fallback. Use
  $20,000 equity and buying power, $2,000 target size, maximum
  ten positions or reservations, 5% bar participation and
  `ibkr_pro_tiered`.

## Configurations and selection

| Config | Cross turnover divided by prior six-block median | Role |
| --- | ---: | --- |
| `development` | At least 3.0 | Primary, the only candidate for portfolio or validation |
| `development_ordinary` | 1.0 to 1.5, inclusive | Ordinary-turnover comparator, study only |

A stock-date can contribute to at most one group. Run both studies
in order and finish both even if the primary misses. The comparator
measures a different set of stock-dates. Report the difference at
both costs and date overlap, with no causal interpretation. There
is one fixed candidate. Comparator results cannot select a variant.

## Run sequence and gates

1. Run both `--study` configurations on 2003-09-10 through
   2016-12-30. Judge `r_60`. For the primary require 150 events
   on 90 dates and 40 events in 2013–2016. Require mean gross at
   least +3% and positive mean net at 2× both overall and in
   2013–2016, with a strictly positive full-period 95%
   day-clustered lower gross bound. Reapply to next-minute
   entries if the study admits later ones. Park after any miss.
2. After a committed develop verdict, run the primary
   `development` portfolio once on the same dates. Require
   150 trades on 90 dates and 40 trades in 2013–2016, mean net
   at least +2.5% at 1× and above +1% at 2× in both windows,
   full-period 2× daily annualised Sharpe above 1, and worst
   2× end-of-day drawdown below $10,000.
3. If qualified, run the frozen primary `validation` once
   from 2017-01-03 through 2023-11-08. Require mean net across
   all completed trades at least +3% at 1× and +1% at 2×
   overall and from 2022-01-03 through 2023-11-08. Require
   at least 150 trades on 90 dates overall, at least 50 trades
   on 30 dates from 2022, positive mean at 1× in 2017–2021,
   full-period 2× daily annualised Sharpe above 1 and worst
   2× end-of-day drawdown below $10,000.

Count each run. Report both costs, counts, annual results, daily
P&L t-statistics and worst drawdown. In portfolios report average
winners and losers separately. The study prices both cost legs
from entry-bar conditions and does not measure actual depth or
capital usage. The sealed holdout stays excluded.
