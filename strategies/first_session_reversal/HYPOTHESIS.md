# First-session reversal

Registered 2026-11-16. Buyers and sellers on a stock's first
trading day are discovering a price with limited price history.
A steep drop from the first regular print can reflect early
holders selling quickly. An observed recovery on substantial
turnover may identify demand at a discount. The first print
may instead be overpriced, in which case the drop can persist.

The first-session follow-through studies bought an early rise
in this cohort. This rule trades a large decline followed by
a recovery while the price remains depressed. Charge this
one variant to `intraday_rebound`. Count the earlier
`new_listing_drift` tests as related search. No return from
those earlier signals determines this strategy's selection.

## Frozen definition

- Use Kinn's listed domestic common stocks with exactly zero
  preceding matched sessions. Start signals on 2004-01-02
  to avoid the dataset startup cohort. First matched session
  is a proxy and can include relistings or gaps in coverage.
  No historical ADV or price floor is available on that date.
- Require the first regular-session bar between 09:30 and
  12:30 ET inclusive, with a finite opening price at least $5.
  Exclude premarket. From the 15th through the 90th clock
  minute counting the first bar as minute one, require valid
  preceding and current clock-minute closes. Count observed
  positive finite closes and require at least five sixths of
  elapsed minutes through the current bar observed.
- Take the first completed bar whose close is at least 10%
  below the first regular opening price and at least 1%
  above the actual preceding clock-minute close. Require
  at least $2 million regular-session cumulative dollar
  turnover from the first bar and $40,000 of decision-bar
  turnover. Use close times volume. Leave at least 60 clock
  minutes before the published calendar close.
- Buy at market on the next clock minute only and sell in
  the same day's closing auction with the existing forced
  fallback. Use $20,000 equity and buying power, $2,000
  target per order, ten concurrent reservations, 5% bar
  participation and `ibkr_pro_tiered`. Keep the standard
  unknown-ADV spread. There is no threshold or exit sweep.

## Gates

1. Run `development --study` from 2003-09-10 through 2016-12-30.
   Judge the close horizon only. Require at least 150 events
   over 90 dates and 40 events in 2013–2016. Require gross
   mean at least +3% and positive 2× net both overall and
   in the later block, with a positive lower 95% day-clustered
   gross bound overall. If the study admits late entries,
   apply all gates to on-time entries as well.
2. After a committed develop verdict, run `development`
   once as a portfolio on the same dates. Require at least
   150 trades over 90 dates and 40 trades in 2013–2016.
   Require mean net at least +2.5% at 1× and above +1% at
   2× both overall and in 2013–2016, daily annualised Sharpe
   above 1 at 2× and worst 2× end-of-day drawdown below
   $10,000. Park after any missed development gate.
3. If qualified, run `validation` once on 2017-01-03 through
   2023-11-08. Require +3% mean net across all completed
   trades at 1× and +1% at 2× both overall and separately
   in 2022 through 2023-11-08. Require 150 trades on 90
   dates overall and 50 trades on 30 dates in that recent
   block, positive 1× mean in 2017–2021, full-period
   stressed Sharpe above 1 and stressed end-of-day drawdown
   less than $10,000.

Count every run and report yearly outcomes, both costs, counts,
daily t-statistics and drawdowns. Report average winners and
losers separately for portfolio stages. Quotes and auction
depth are unverified. The sample uses the latest classification
and can diverge from actual IPO dates. The sealed holdout stays
excluded.
