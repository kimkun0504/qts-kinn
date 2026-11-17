# Earnings gap follow-through

Registered before any run. A positive opening gap after an earnings
disclosure becomes available can reflect favorable repricing. If buying
continues through the opening rotation on unusually high turnover,
there may be residual demand later that session. An opening overshoot,
unrelated news or subsequent profit-taking can reverse that move.
Item 2.02 identifies an earnings disclosure. The signal's direction
comes entirely from the observed price response.

Charge this single definition to `opening_gap_continuation`. The prior
broad gap rule and Claude's dated 8-K and gap screens are related
search. The distinct confirmation here combines a typed earnings item,
an opening gap, consecutive actual closes and high relative turnover
observed through 09:44. Earlier swing results do not establish a
same-session effect.

## Frozen definition

- Use Kinn's listed domestic common stocks, including later delistings
  while eligible, at least 20 matched prior sessions, prior split-adjusted
  close at least $2, prior 20-session median dollar turnover at least
  $1 million and prior market cap from $50 million inclusive to $2
  billion exclusive. All selections use pre-open information.
- Declare `inputs = {"form8k": {"sessions": 1}}`. Require an available
  report with the earnings flag and a filing date before this session,
  matched to the symbol and company identity here. The input carries
  filings from earlier dates. It does not identify a real-time release
  timestamp or analyst expectations. An earnings report filed this
  morning remains hidden in this session.
- Require the 09:30 regular-session bar, with an open at least 10% above
  the split-adjusted prior close. Require actual closes in the 09:43
  and 09:44 bars, both at least 1% above the opening price. Sum regular
  dollar turnover through 09:44 using minute close times volume. Require
  at least 25% of the prior median full-day turnover and $40,000 in the
  completed 09:44 bar. This selects sustained demand after the gap.
  Exclude premarket trades. Take one qualifying signal per stock.
- Buy at market at 09:45 only, with expiry at the end of that minute.
  Sell in the same session's official closing auction, using the
  engine's fallback where required. Use $20,000 equity and buying
  power, a $2,000 target and ten concurrent reservations, 5% per-bar
  participation and `ibkr_pro_tiered`. All trades are intraday.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30
   and judge `r_close` only. Require at least 150 events across 90
   dates and at least 40 events in 2013–2016. Require mean gross
   of at least +3%, positive net at doubled slippage both overall
   and in 2013–2016, and a strictly positive full-period 95%
   day-clustered gross lower bound. Apply the same gates to on-time
   entries if the study admits a later entry. Park after any miss.
2. Only after a committed develop verdict, run the matching
   `development` portfolio on the same dates. Require 150 trades
   across 90 dates and 40 trades in 2013–2016, mean net at least
   +2.5% at base costs and above +1% at 2× in both development
   blocks, full-period daily Sharpe above 1 at 2× and worst
   stressed end-of-day drawdown below $10,000.
3. Only if qualified, run `validation` once from 2017-01-03 through
   2023-11-08 with the frozen definition. Require +3% average
   net across all completed trades at 1× and +1% at 2×, both
   overall and separately for 2022-01-03 through 2023-11-08.
   Require at least 150 trades across 90 dates overall and 50
   trades across 30 dates in the recent block, positive 1× mean
   in 2017–2021, full-period stressed daily Sharpe above 1 and
   worst stressed end-of-day drawdown below $10,000.

Count every run. Report both costs, counts, annual results, daily
P&L t-statistics and worst drawdown, plus mean winners and losers
in a portfolio. Record the exact Form 8-K input version. A gap can
include unrelated news or a corporate action. A typed date-level
event cannot establish release timeliness or measure an earnings
surprise. Minute-bar entries, closing auctions and actual available
depth remain modelled. The sealed holdout stays excluded.
