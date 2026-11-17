# Distributed morning selloff

Registered before any run. A seller executing across the morning
could depress the price over several intervals without a single
dominant price jump. The stock may partially recover after the
pressure abates. Persistent selling can also reflect worsening
information. We test the price path and do not observe the
seller's orders, identity or motivation. Prior work on price
pressure from institutional selling motivates the distinction
between temporary pressure and changes in value.
[Coval and Stafford, Asset Fire Sales (and Purchases) in Equity Markets](https://www.nber.org/papers/w11357)

This is one `intraday_rebound` variant. The family carried 48
trials at the start of this research and 95 after the equity-sale
gap reclaim. Kinn's fast-drop and relative-dislocation variants
selected short, sharp shocks. Heavy-turnover stabilization used
a 15-minute shock followed by a five-minute active range. This
rule selects large drops distributed across the first 90 minutes,
with one fixed decision time. It has no news or peer gate.

## Frozen definition

- Use listed domestic common stocks, including later delistings
  while eligible. Require at least 20 matched prior sessions,
  split-adjusted prior close at least $3, prior 20-session median
  daily dollar turnover at least $1 million, and prior market
  cap from $50 million inclusive to $10 billion exclusive.
- Require an observed 09:30 regular-session open within 5% of the
  split-adjusted prior close. Use the closes of the actual bars
  labelled 09:44, 09:59, 10:14, 10:29, 10:44 and 10:59. All
  prices must be finite and positive. The 10:59 close must be at
  least 10% below the open. Of the six successive price changes
  starting at the open, at least four must be strictly negative.
  The largest one-interval price loss in dollars must be no more
  than half the total decline in dollars. Treat a missing
  checkpoint as ineligible. Ignore premarket bars.
- Require an actual 11:04 bar closing at least 1% above the
  10:59 close, with turnover of at least $40,000, estimated by
  close times volume. Buy at market at 11:05 only, expiring at
  the end of that minute. Sell in the same day's closing auction
  with the simulator's normal fallback. Use $20,000 equity
  and buying power, $2,000 per order, up to ten positions or
  reservations, 5% bar participation and `ibkr_pro_tiered`.

The 15-minute checkpoints reduce sensitivity to any one minute
and the loss-share rule disqualifies a single dominant leg.
Unobserved prices between checkpoints and unverified news remain
limitations. The five-minute rebound measures a change in
direction without inferring actual selling or recovered value.
No thresholds or exit times are swept.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30.
   Judge `r_close` only. Require at least 150 events on 90 dates
   and at least 40 events in 2013–2016. Require mean gross of at
   least +3% and positive mean at 2× overall and in 2013–2016,
   and a full-period 95% day-clustered lower gross bound strictly
   above zero. Reapply the same gates to next-minute entries if
   the study admits orders after expiry. Park after any miss.
2. After a committed develop verdict, run `development` once
   as a portfolio on the same dates. Require at least 150 trades
   on 90 dates and 40 in 2013–2016, mean net at least +2.5%
   at 1× and above +1% at 2× overall and in 2013–2016, stressed
   full-period daily annualised Sharpe above 1, and worst
   stressed end-of-day drawdown below $10,000.
3. If qualified, run frozen `validation` once from 2017-01-03
   through 2023-11-08. Require at least +3% net per completed
   trade at base costs and +1% at 2×, overall and separately
   from 2022-01-03 through 2023-11-08. Require at least 150 trades
   on 90 dates overall and at least 50 trades on 30 dates in
   the recent block, positive 1× mean in 2017–2021, stressed
   full-period daily annualised Sharpe above 1, and worst
   stressed end-of-day drawdown below $10,000.

Report samples, both cost cases, annual results, daily P&L
t-statistics and worst drawdown. Report mean winners and losers
separately for any portfolio. Count every run. Report the sample's
concentration in 2008 descriptively. The study sums independent
events, approximates marketable costs and does not establish
available size or auction fills. The holdout stays sealed.
