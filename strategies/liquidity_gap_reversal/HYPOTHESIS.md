# Liquidity gap reversal

Registered on 2026-11-16. A break in trading can interrupt liquidity provision. When
the first observed trade after the break reprices the stock sharply downward and the
same minute partially recovers, the initial markdown may include a temporary liquidity
discount. The opposing explanation is price discovery after news. The volume condition
before the gap screens out routinely sparse symbols. Five minutes is motivated by the
published US trading-pause mechanism. Missing minute bars are a proxy with no halt
identifier, and market structure differed during the early sample.
[Limit Up–Limit Down Plan](https://www.luldplan.com/)

This definition uses a gap between observed trades as its event. It does not require
a fixed decline from yesterday's close, a benchmark limit order, or an opening-range
breakout. Charge it to the shared `intraday_rebound` family because it buys reversals.

## Frozen event and execution

- Listed domestic common stock with at least 20 observed prior sessions, split-adjusted
  prior close at least $2, and trailing median daily dollar volume at least $1 million.
  Use Kinn's pre-open eligibility and include subsequently delisted issues.
- Look for a first bar after **5 to 15 missing clock minutes**. Its label must be
  09:45 to 14:45 ET inclusive and late enough to have its pre-gap sequence in the regular
  session. The last five bars before the gap must have consecutive clock labels and
  total at least $100,000 in dollar turnover, approximated by close times volume.
- The resumption bar must open at least **8% below** the last traded close before
  the gap. Its close must be at least **2% above** its own open and still at least 2%
  below the pre-gap close. Act only on the first such completed bar per symbol per day.
- Buy at market in the next clock minute only, expiring at the end of that minute.
  Exit in the same day's closing auction. Use $20,000 equity and buying power, $2,000
  target order, 5% bar participation and `ibkr_pro_tiered`. Kinn's normal market
  entry, auction, and forced-exit pricing apply.

## Development, validation and recent regime

One definition and no threshold sweep in this registration. Count each study,
portfolio development run, or validation in the shared family.

1. Run `development --study`, 2003-09-10 through 2016-12-30. Require at least 150
   events across 90 dates and at least 40 events during 2013–2016. Require gross
   mean to the close at least +3% in the full sample and in 2013–2016, a positive
   full-sample lower 95% day-clustered gross bound, and positive net at 2× in both
   the full and 2013–2016 samples. Recheck on next-bar-only events if the study's
   expiry mismatch admits late entries. Park if any gate fails.
2. Following a committed develop verdict, run `development` as a portfolio backtest
   on the same dates. Require at least 150 fills on 90 sessions and at least 40 fills
   during 2013–2016. Require 1× net mean at least +2.5% and 2× net mean above +1%
   in the full and 2013–2016 samples, full-sample 2× daily Sharpe above 1, and
   end-of-day drawdown under $10,000 at 2×. Park if any gate fails.
3. If qualified, run `validation` exactly once, 2017-01-03 through 2023-11-08. The
   main bar is **+3.00% arithmetic mean net across all completed trades at 1×**.
   Separately require +3.00% at 1× in 2022 through the seal eve, with at least 50
   completed trades across 30 sessions in that block and at least 150 across 90
   in validation. Require positive 1× mean in 2017–2021, +1% or more at 2× on
   both the full validation period and the recent block, full-period daily Sharpe
   above 1 and end-of-day drawdown under $10,000 at 2×. Report average winners and
   loss rates separately. All dates on or after 2023-11-09 stay sealed.

Report counts, both costs, daily t-statistics, drawdowns and annual results. Study
P&L is the unconstrained hypothetical series. An auction close, observed reopening
print and ended halt can all differ from an achievable order fill. The research
target applies to simulated returns after costs. Paper trading would additionally
require independent tick and quote validation.
