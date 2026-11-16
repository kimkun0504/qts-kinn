# Volume surge pullback

Registered 2026-11-16. Buying the high-turnover advance in
`intraday_volume_surge` lost after costs in development run
`20261116T012352Z_gpt_intraday_volume_surge_9a2e5bc8`. The rapid gain can
attract buyers early enough to exhaust demand. When a stock subsequently
pulls back while retaining part of its gain, a recovery can indicate that
buyers remain willing to participate at a lower price. A pullback can
also be the start of a sustained unwind. Prices and volume do not reveal
buyers' motives or carry a verified catalyst.

This is one fixed, data-informed definition. Keep the original surge
as a setup and trade the subsequent reversal. Charge the new runs to
`intraday_rebound` and disclose the prior `intraday_volume_surge` look.
The earlier gap-washout test required an overnight move and a reclaim
of VWAP. Here the advance starts after a near-flat open and the
benchmark is the completed post-surge peak.

## Frozen definition

- Use point-in-time listed domestic common stocks with at least 20
  matched prior sessions, a split-adjusted prior close of at least $3,
  20-session median daily dollar turnover of at least $1 million, and
  positive prior cap below $2 billion. Include later delistings while
  eligible. Require a 09:30 bar whose open is within 5% of prior close.
- From 09:44 through 11:59 ET identify the first observed minute
  whose close and preceding clock-minute close are both at least 20%
  above the 09:30 open and whose completed regular-session cumulative
  dollar turnover is at least the prior full-day median. Use close
  times volume and exclude premarket. This marks the setup only.
- Track the maximum of observed regular-session closes from the
  setup minute onwards. After the setup, take the first completed
  decision bar whose close is at least 8% below the maximum close
  known before that bar, at least 1% above the actual immediately
  preceding clock-minute close, and strictly above the opening
  price. Both confirmation bars must come after the setup. Require
  at least $40,000 of decision-bar turnover. The decision bar must
  be labelled at or before 14:45 ET and at least 75 clock minutes
  before that day's calendar close. The 8% decline requires a
  material pullback inside the preceding 20% or larger advance.
- Buy at market on the next clock minute only. Hold for 60 clock
  minutes from the first fill and exit at market, with the normal
  same-day auction fallback. Use $20,000 equity and buying power,
  $2,000 target size, ten reservations, 5% bar participation and
  `ibkr_pro_tiered`. Start and finish every trade on the same date.

## Sequence and gates

1. Run `development --study` from 2003-09-10 through 2016-12-30.
   Use `r_60` only. Require at least 150 events on 90 dates and
   40 events in 2013–2016. Require mean gross at least +3% overall
   and in 2013–2016, positive 2× mean in both blocks and a strictly
   positive full sample day-clustered lower 95% gross bound. If
   any study entries are late, reapply the gates to the on-time
   subset. Park after any miss.
2. After a committed develop decision, run `development` once as
   a portfolio on the same dates. Require 150 trades on 90 dates,
   at least 40 trades in 2013–2016, mean at least +2.5% at 1× and
   above +1% at 2× in both development blocks, annualised daily
   Sharpe above 1 at 2× and stressed end-of-day drawdown under
   $10,000.
3. Only if qualified, run `validation` from 2017-01-03 through
   2023-11-08 once. Require at least +3% mean net across all
   completed trades at 1× and +1% at 2×, overall and separately
   from 2022 through 2023-11-08. Require 150 trades across 90 dates
   overall, 50 across 30 in the recent block, positive 1× mean
   in 2017–2021, stressed full-period daily Sharpe above 1 and
   worst end-of-day drawdown under $10,000 at 2×.

Count every run. Report sample, annual results, daily P&L t-statistics
and drawdown at both costs, and average winners and losers separately
in any portfolio. Solo events approximate two marketable legs from the
entry bar and omit portfolio limits. The backtest uses bar fills, with
halt timing and actual quote depth unverified. The later holdout stays
sealed and no run uses any market data dated 2023-11-09 or later.
