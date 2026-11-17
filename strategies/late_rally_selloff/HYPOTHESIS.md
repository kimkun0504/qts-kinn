# Late rally selloff

Registered before any run. A stock that rallied earlier in the
session can sell off as short-horizon holders reduce exposure
before the close. If a partial recovery starts before the auction,
temporary selling may leave a discount that can still narrow.
The deadline is the scheduled close. The data do not identify
which holders sold, whether they faced a deadline or whether the
decline was justified by news.

This variant counts in `intraday_rebound`. The family carried 48
trials at the start of this research and 96 after the distributed
morning selloff. The base rebound assumes a decline against the
prior close. This rule starts from an intraday rally, anchors to
its late-afternoon level, and tests a reversal in the last hour.
The descriptive late events in the earlier heavy-turnover study
are a related development look. They used a different signal
and contribute no out-of-sample evidence for this one.

## Frozen definition

- Use listed domestic common stocks, including later delistings
  while eligible. Require at least 20 matched prior sessions,
  prior split-adjusted close at least $2, prior 20-session median
  daily dollar turnover at least $1 million, and prior market
  cap from $50 million inclusive to $2 billion exclusive.
- Trade regular sessions with the normal 09:30–16:00 ET
  schedule only. Require the actual 09:30 regular-session open
  and actual closes at 14:59, 15:19 and 15:24. All four prices
  must be positive and finite. The 14:59 close must be at
  least 10% above the open. The 15:19 close must be at least
  6% below the 14:59 close. The 15:24 close must be at least
  1% above the 15:19 close and still at least 3% below the
  14:59 close. Require $40,000 of turnover in the 15:24 bar,
  approximated by close times volume. The rule uses no news
  or same-day auction data.
- Signal once per symbol after the 15:24 bar. Buy at market
  at 15:25 only and expire at the end of that bar. Sell in the
  same day's closing auction using Kinn's standard fallback.
  Use $20,000 equity and buying power, $2,000 target per
  order, at most ten positions or reservations, 5% volume
  participation, and `ibkr_pro_tiered`.

The remaining discount leaves room for further recovery. It
does not guarantee a fill at the decision price or a close
above it. No alternate entry times, cutoffs or exits are registered.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30.
   Judge `r_close`. Require at least 150 events on 90 dates
   and 40 events in 2013–2016. Require gross mean at least +3%
   and positive mean at 2× slippage both overall and in
   2013–2016. Require a strictly positive full-period 95%
   day-clustered lower gross bound. Apply the same gates to
   the next-minute-only subset if the study enters late.
   Park after any miss.
2. After a committed develop verdict, run the `development`
   portfolio once on the same dates. Require 150 trades on
   90 dates and 40 trades in 2013–2016. Require mean net
   at least +2.5% at 1× and above +1% at 2× overall and in
   2013–2016, stressed full-period daily annualised Sharpe
   above 1, and worst stressed end-of-day drawdown below
   $10,000.
3. Only if qualified, run frozen `validation` once on
   2017-01-03 through 2023-11-08. Require +3% arithmetic mean
   net across all completed trades at 1× and +1% at 2× both
   overall and separately from 2022-01-03 through 2023-11-08.
   Require 150 trades on 90 dates overall, 50 on 30 dates
   in the recent block, positive 1× mean in 2017–2021,
   stressed full-period daily annualised Sharpe above 1,
   and worst stressed end-of-day drawdown below $10,000.

Count all runs. Report both cost settings, date concentration,
annual results, daily P&L t-statistics and drawdowns. Report
average winners and losers separately for any portfolio.
The study estimates both marketable legs from the entry bar.
An official closing price does not establish that the order
would receive an auction fill. The sealed holdout is excluded.
