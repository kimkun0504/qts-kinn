# Turnover compression breakout

Registered 2026-11-16. A stock can trade heavily within a narrow range while
available sell orders absorb demand. An upward break that holds through the
next minute may follow depletion of that supply. High turnover can also
come from two-sided trading with no persistent imbalance, and the break
could exhaust the remaining demand. Minute bars cannot identify orders or
measure who initiated trades.

The earlier volume-surge rule required a large gain before checking
cumulative turnover. This definition requires turnover and a tight price
range before the breakout. It shares the volume-driven continuation
mechanism and is charged to `intraday_volume_surge`. Earlier opening-range
and other momentum tests are related looks. There is one variant and no sweep.

## Frozen signal

- Use the point-in-time domestic common-stock universe, with at least
  20 matched prior sessions, a split-adjusted prior close of at least $3,
  prior 20-session median daily dollar turnover of at least $5 million,
  and a positive prior cap below $2 billion. Retain subsequent delistings
  until they cease to be eligible. Require an observed 09:30 regular
  opening bar whose open is within 5% of the split-adjusted prior close.
- For a proposed decision at regular-session clock minute `t`, measure the
  30-minute interval `t−31` through `t−2`, inclusive. The full interval
  must be in the regular session. Require at least 28 valid observed
  closes, maximum close no greater than 1.02 times the minimum, and
  total dollar turnover at least 30% of the stock's prior median daily
  dollar turnover. Use minute close times volume and exclude premarket.
  This requires roughly four times the uniform regular-session pace.
  Unobserved minutes do not contribute to the range or turnover.
- Require actual closes at `t−1` and `t`, both at least 3% above the frozen
  range maximum and with `t` strictly above `t−1`. The decision bar must
  trade at least $40,000 by close times volume, the $2,000 target divided
  by 5% participation. Take the first eligible signal per stock from
  10:01 through 13:30 ET and at least 75 minutes before the session close.
  Use only completed bars. The range measurement excludes both breakout
  bars.
- Buy at market on the next clock minute only and let the order expire
  after that bar. Exit 60 clock minutes after the first fill at market,
  with the existing closing auction fallback. Use $20,000 equity and
  buying power, a $2,000 target, ten reservations, 5% bar participation,
  and `ibkr_pro_tiered`. All positions open and close on the same day.

## Gates

1. Run `development --study` from 2003-09-10 through 2016-12-30. Use the
   `r_60` horizon. Require 150 events on 90 dates and 40 events in
   2013–2016. Require +3% mean gross and positive 2× mean net both
   overall and in 2013–2016, and a strictly positive full-period lower
   95% day-clustered gross bound. If the study fills later than expiry,
   apply every gate to the next-clock-minute-only events as well.
   Park if any gate fails.
2. After recording a develop decision, run `development` as a
   portfolio on the same dates. Require 150 trades on 90 dates and 40
   trades in 2013–2016, +2.5% or greater 1× mean net and above +1% at 2×
   overall and in the later block, daily annualised Sharpe above 1
   at 2× and worst end-of-day drawdown below $10,000 at 2×.
3. Only if qualified, run `validation` once from 2017-01-03 through
   2023-11-08. Require +3% mean net across all completed trades at base
   costs and +1% at 2×, both overall and separately in 2022 through
   2023-11-08. Require 150 trades on 90 dates overall and 50 on 30 dates
   in the recent block, positive 1× mean in 2017–2021, full-period
   stressed daily Sharpe above 1 and stressed end-of-day drawdown
   under $10,000. Report mean winners and losers separately.

Count every run. Report both cost cases, counts, yearly results, daily
t-statistics and drawdown. Study dollars are the sum of hypothetical
independent orders. Bar participation, quoted depth, minute prices,
halts and auction fills limit execution claims. Point-in-time identities
still depend on latest-vintage classifications. No date from 2023-11-09
onward is eligible.
