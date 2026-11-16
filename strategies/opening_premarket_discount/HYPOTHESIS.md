# Opening premarket discount

Registered 2026-11-16. The opening rotation can bring a different mix of
orders than the preceding half hour. An opening price far below recent
premarket transactions can reflect transient sell pressure. A subsequent
recovery while the discount persists leaves room for further repricing.
New information or better price discovery at the open can make the lower
price persist. Premarket volume and quotes are often thin.

Charge this one variant to `intraday_rebound`. Prior gap-reclaim and
rebound studies used the previous close or a regular-session price.
This uses a traded reference from the same morning. No news timestamp
or auction imbalance is inferred. Keep one fixed definition with no
threshold sweep.

## Frozen definition

- Use listed domestic common stocks including later delistings while
  eligible, at least 20 matched prior sessions, prior split-adjusted
  price of at least $3, and prior 20-session median dollar turnover of
  at least $1 million. No market-cap exclusion.
- At the open, construct a reference from the completed minutes 09:00
  through 09:29 ET inclusive. Retain positive finite closes and
  positive volumes. Require at least four observed bars, at least
  one bar from 09:25 through 09:29, and at least $100,000 summed
  dollar turnover. The reference is the volume-weighted mean of the
  observed closes. Require the 09:30 bar, with an opening price
  at least 8% below that reference.
- From 09:34 through 09:59 ET, take the first completed bar whose
  close is at least 1% above its actual preceding clock-minute close
  and at least 6% below the reference. Require $40,000 in that bar's
  turnover, the $2,000 target divided by the 5% participation rate.
  Require at least 75 minutes before the exchange calendar close.
  The 8% discount and 6% remaining gap capture a large dislocation
  with partial evidence that the opening sale has abated.
- Buy at market on the next clock minute only and hold 60 clock
  minutes from the first fill, then sell at market with the normal
  auction fallback. Use $20,000 equity and buying power, $2,000
  target per order, ten reservations, 5% bar participation and
  `ibkr_pro_tiered`. Close positions on the entry date.

## Gates

1. Run `development --study` for 2003-09-10 through 2016-12-30.
   Use `r_60`. Require at least 150 events on 90 dates and 40 events
   in 2013–2016. Require gross mean at least +3% and positive 2× mean
   overall and in 2013–2016, with a strictly positive full-period
   lower 95% day-clustered gross bound. If there are late study
   entries, apply the same bars to the next-clock-minute subset.
   Park after any miss.
2. Following a committed develop verdict, run the `development`
   portfolio on the same dates. Require 150 completed trades on
   90 dates and 40 trades in 2013–2016, 1× net mean at least +2.5%
   and 2× mean above +1% in both development blocks, stressed
   annualised daily Sharpe above 1 and worst stressed end-of-day
   drawdown below $10,000.
3. Only if qualified, run `validation` once, 2017-01-03 through
   2023-11-08. Require +3% arithmetic mean net across all completed
   trades at 1× and +1% at 2× overall and separately from 2022
   through 2023-11-08. Require 150 trades on 90 dates overall and
   50 trades on 30 dates in that recent block, positive 1× mean in
   2017–2021, stressed full-period daily Sharpe above 1 and
   stressed end-of-day drawdown under $10,000.

Count every run. Report both cost cases, daily P&L t-statistics,
drawdown and years. Report winner and loser averages separately for
a portfolio. Study entries approximate independent orders, and the
opening bar's first price need not be an auction print. The historical
premarket coverage, timestamp quality and actual entry depth can all
affect inference. The holdout stays sealed.
