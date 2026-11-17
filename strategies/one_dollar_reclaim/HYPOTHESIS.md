# One-dollar reclaim

Registered before any run. Round numbers can attract orders. The
dollar level also has a public listing reference for some issuers,
which may make buyers react when a stock that was above it
briefly trades below and then reclaims it. This test uses listed
domestic stocks without determining exchange-specific compliance,
bid quotes, order clustering or seller intent. Listing rules
concern closing bids over multiple sessions. A single intraday
trade cannot cure a listing deficiency.
[Harris, Stock Price Clustering and Discreteness](https://academic.oup.com/rfs/article-abstract/4/3/389/1580169)
[Example of an issuer's Nasdaq bid-price disclosure](https://www.sec.gov/Archives/edgar/data/1451448/000149315223007795/form8-k.htm)

Charge both configurations to `intraday_rebound`, which carried
48 trials at the start of this research and 97 after the late
rally selloff. Earlier reversals selected distances to recent
trade prices, filings or a prior close. This design fixes an
absolute price reference and compares it with a nearby level.
The close-based signal can still capture an ordinary rebound,
independent of what investors think of the reference price.

## Frozen definition

- Use listed domestic common stocks, including later delistings
  while eligible. Require at least 20 prior matched sessions
  and prior 20-session median full-day dollar turnover of at
  least $500,000. Require the split-adjusted prior close in
  the interval from reference inclusive to 1.50 times reference
  exclusive. Use no market-cap restriction. Require the actual
  regular 09:30 open in the same price interval.
- From 09:35 through 14:45 ET, take the first completed regular
  bar `t` that closes from 1.01 to 1.08 times reference
  inclusive. Require an actual positive close in bar `t−1`
  strictly below reference. At least one positive regular close
  from `t−30` through `t−1` must have been at or below 0.97 times
  reference. The thresholds require a visible break and reclaim
  across the level. Exclude premarket prints.
- Require $20,000 turnover in the decision bar using close times
  share volume. This equals the turnover that would support
  half the target order at 5% participation at the decision
  price. Actual execution depends on the next bar. Buy at market
  on the next clock minute only and expire after that minute.
  Sell in the same session's closing auction with Kinn's
  standard fallback. Use $20,000 equity and buying power,
  $2,000 target size, ten positions or reservations, 5% bar
  participation, and `ibkr_pro_tiered`.

## Registered study configurations and selection

| Config | Reference | Role |
| --- | ---: | --- |
| `development` | $1.00 | Primary, the only candidate for a portfolio or validation |
| `development_comparison` | $1.20 | Nearby price level, study only |

Run these studies in the listed order, one at a time, allowing
both to finish even if the primary fails. The comparison is
descriptive. The names, prices and exposures can differ, so
the difference in returns cannot identify a causal effect of
the dollar threshold. Report counts, overlap of security-days
and overall and 2013–2016 average net at both cost settings.
The comparison cannot replace the primary or make it eligible.
Validation, if any, uses the primary with identical parameters.

## Run sequence and gates

1. Run both registered studies on 2003-09-10 through 2016-12-30.
   Judge `r_close` for the primary. Require at least 150 events
   on 90 dates and 40 events in 2013–2016. Require mean gross
   at least +3% and positive mean at 2× slippage both overall
   and in 2013–2016, with a strictly positive full-period 95%
   day-clustered lower gross bound. Reapply the same bars to
   next-minute entries if the study admits later prints. Park
   the primary after any miss.
2. After a committed develop verdict, run `development` once
   as a portfolio on the same dates. Require at least 150 trades
   on 90 dates and 40 in 2013–2016, 1× mean net at least +2.5%
   and 2× mean above +1% both overall and in 2013–2016, 2×
   full-period annualised daily Sharpe above 1 and 2× worst
   end-of-day drawdown below $10,000.
3. If qualified, run frozen `validation` once from 2017-01-03
   through 2023-11-08. Require +3% mean net over all completed
   trades at 1× and +1% at 2× both overall and separately from
   2022-01-03 through 2023-11-08. Require at least 150 trades on
   90 dates overall and at least 50 trades on 30 dates in the
   recent block, positive 1× mean in 2017–2021, stressed full-
   period annualised daily Sharpe above 1 and worst stressed
   end-of-day drawdown below $10,000.

Report both costs, annual counts and results, daily P&L t-statistics
and worst drawdown. Report winner and loser means for portfolio
trades separately. Count each run. Dollar tick size, fees,
spread, changes in trading depth and corporate actions matter
in low-priced stocks. Minute bars do not observe queues or
reliable auction depth. The sealed holdout is excluded.
