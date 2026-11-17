# Heavy-turnover stabilization

Registered before any run. A fast decline can come from an urgent
seller or from information that warrants a lower price. If the price
stabilizes while active trading persists, there may be buyers willing
to absorb the supply at the new level. Test a particular price and
volume pattern after the shock. A minute that closes down can contain
buyer-initiated trades, so this is a proxy based on bars. Continued
turnover can also reflect news or churn. Short-horizon reversal and
liquidity imbalances motivate the economic question.
[Heston, Korajczyk and Sadka, Intraday Patterns in the Cross-section of Stock Returns](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2010.01573.x)

This is one rebound variant. Charge it to `intraday_rebound`, which
carried 48 trials at the start of this research and 93 at the close
of the insider price reclaim study. Related Kinn tests selected
large declines, fast declines, rebounds confirmed by price, volume
surges and peer-relative one-minute rebounds. This rule demands
a distinct five-minute stabilization phase with elevated turnover
and a majority of turnover on minutes with falling closes.

## Frozen definition

- Use listed domestic common stocks, including later delistings
  while eligible. Require 20 prior matched sessions, split-adjusted
  prior close of at least $3, and median daily dollar turnover of at
  least $2 million over the last 20 sessions. Require prior market
  cap from $50 million inclusive to $10 billion exclusive.
- Each decision minute `t` needs all 21 completed, positive-price,
  positive-volume regular-session bars from `t−20` through `t`.
  The close at `t−5` must be at least 10% below the close at
  `t−20`. The 15 bars from `t−19` through `t−5` must turn
  over at least 10% of the prior median full-day dollar turnover.
  Use close times volume to approximate each bar's turnover.
- The five bars from `t−4` through `t` are the stabilization
  phase. All five closes must be within 2% below to 4% above the
  `t−5` close, inclusive, and the final close must be at least
  1% above it. Turnover per minute in this phase must be at least
  half that during the shock. At least half the stabilization
  turnover must occur in bars that close strictly below the
  immediately preceding clock-minute close. Require at least
  $40,000 turnover on the decision bar.
- Take the first qualifying bar by stock from 09:50 through 14:45
  ET inclusive, at least 75 clock minutes before the calendar
  close. Buy at market on the next clock minute only, expiring at
  the end of that minute. Hold for 60 clock minutes after the first
  fill, then sell at market with Kinn's closing auction fallback.
  Use $20,000 equity and buying power, $2,000 per order, ten
  reservations, 5% bar participation, and `ibkr_pro_tiered`.
  Positions open and close on the same session.

The turnover calculation compares five minutes to the preceding
fifteen and excludes premarket. The narrow stabilization range
demands limited further downside and leaves room for more of the
original shock to reverse. No time or threshold sweep is registered.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30 and
   judge `r_60` only. Require at least 150 events on 90 dates and
   40 events in 2013–2016. Require mean gross return at least +3%
   and positive mean net at 2×, both overall and in 2013–2016.
   Require a strictly positive lower 95% day-clustered gross bound
   overall. Evaluate the same gates on the next-clock-minute
   subset if the study admits a later entry. Park after any miss.
2. After a committed develop verdict, run the `development`
   portfolio once on the same dates. Require at least 150 trades
   on 90 dates and 40 in 2013–2016. Require mean net per trade at
   least +2.5% at 1× and above +1% at 2×, both overall and in
   2013–2016. Require full-period 2× daily annualised Sharpe above
   1 and worst 2× end-of-day drawdown below $10,000.
3. If qualified, run frozen `validation` once from 2017-01-03
   through 2023-11-08. Require at least +3% mean net at 1× and
   +1% at 2× across all completed trades, both overall and
   separately from 2022-01-03 through 2023-11-08. Require at
   least 150 trades on 90 dates overall and at least 50 trades
   on 30 dates in the recent block, positive 1× average net in
   2017–2021, stressed full-period annualised daily Sharpe above
   1 and worst stressed end-of-day drawdown below $10,000.

Count each run. Report the sample, annual results, daily P&L
t-statistics, and worst drawdown at both costs. Report conditional
win and loss averages in portfolio results. Signed order flow,
confirmed halt states, spreads and actual depth are unobserved.
Abrupt moves can share a market or news cause and cluster by
date. The study models both marketable legs from entry-bar data.
Keep the sealed holdout excluded.
