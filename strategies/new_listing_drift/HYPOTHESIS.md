# New listing drift

Registered on 2026-11-16. A newly traded stock can have limited lendable supply as
price discovery and distribution continue. A substantial regular-session gain on
unusually fast turnover may represent demand that is still being worked through.
The competing explanation is an overpriced initial trade and selling from early
allocations. Kinn observes neither allocations, short inventory, nor offer prices.
[Short-Sales Constraints and Aftermarket IPO Pricing](https://mitsloan.mit.edu/sites/default/files/inline-files/Short-Sales%20Constraints%20and%20Aftermarket%20IPO%20Pricing.pdf)

The key stock selector is listing age as approximated by prior matched trading
sessions. This differs from the earlier upside tests driven by opening gaps,
filing dates, or a small-cap turnover surge. The market mechanism is the early
aftermarket, so use family `new_listing_drift`. Record the earlier momentum screens
as related search when interpreting results across the research program.

## Frozen definition

- Pre-open universe is listed domestic common stock with **one through nine** prior
  observations in Kinn's daily panel, prior split-adjusted close of at least $5,
  and historical median daily dollar turnover of at least $5 million. With fewer
  than 20 observations the median uses available history. Start signals on
  November 3, 2003 so the start of data coverage cannot qualify all existing
  names as young at once. The cohort can include relistings, coverage changes and
  securities first matched late. It is an observed-age screen.
- Require bars labelled 09:30 and 09:59 ET. The opening price must be within 5%
  of prior close. At 10:00, require the 09:59 close to be at least 6% above the
  open and cumulative regular-session dollar turnover to be at least 25% of the
  prior median daily turnover. Approximate turnover as minute close times volume
  and exclude pre-market prints.
- Submit one market buy for the next clock minute only. Expire at the end of that
  bar. Sell in the same day's closing auction. Use $20,000 equity and buying power,
  at most ten positions or outstanding orders, $2,000 target size, 5% participation
  and `ibkr_pro_tiered`. Prices and participation are modelled in Kinn.

## Run sequence

One fixed definition in this registration. Count every run. Use return to the close
in the study. Market data ends on 2023-11-08 and the holdout stays sealed.

1. Event study `development --study`, 2003-09-10 through 2016-12-30. Require 150
   events on 90 sessions and at least 40 events in 2013–2016. Require mean gross at
   least +3% and positive mean net at 2× both overall and in 2013–2016, and positive
   lower session-clustered 95% gross bound overall. Recheck the same gates on
   next-bar-only events if the study admitted later prints past order expiry.
2. After a committed develop verdict, run the `development` backtest on the same
   dates. Require at least 150 trades on 90 sessions and 40 trades in 2013–2016.
   Require +2.5% or more at 1× and above +1% at 2× both overall and in 2013–2016,
   2× daily Sharpe above 1, and 2× worst end-of-day drawdown under $10,000. A failure
   at either development stage parks the definition.
3. If qualified, run `validation` once, 2017-01-03 through 2023-11-08. Require
   +3.00% average net per completed trade at 1× and at least +1% at 2×, both overall
   and in January 2022 through the seal eve. Also require at least 150 completed
   trades on 90 dates overall, at least 50 trades on 30 dates in the recent block,
   positive 1× mean in 2017–2021, full-period 2× daily Sharpe above 1 and 2× worst
   end-of-day drawdown under $10,000. Average all wins and losses for the hurdle.
   Report conditional average win and loss rates separately.

Report results at both costs, annual breakdowns, t-statistics and drawdown. Study
P&L is unconstrained. IPO cycles and data coverage can change the count of qualifying
stocks. The entry bar and auction approximations require independent execution
validation before paper trading. No market data dated on or after 2023-11-09 is eligible.
