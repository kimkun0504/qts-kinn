# Trade-size expansion after an available earnings disclosure

Registered before empirical testing. The owner suggested volume,
momentum and stock selection. Volume alone cannot distinguish
many small prints from fewer large prints. Massive's existing
minute aggregates include transaction counts, which would let
this candidate measure a change in average shares per print.
The current strategy view omits the count; an owner-authorized
data-view change is required before any empirical run.

The economic hypothesis is repeated demand after an earnings
disclosure: average print size expands while transaction count
does not decline, and price progresses upward. A program buying
increasingly large pieces might not be finished. This is a
proxy, not identification of a buyer or its orders. One parent
order can generate many prints; block reporting, trade conditions
and execution algorithms affect the count. The opposite mechanism
is late, uninformed demand that pays for an exhausted rise.

## Prior looks and family

Use the existing `big_prints` family and carry its declared
49 prior looks at Claude's inspected commit `c173694`. Claude's
work mainly uses longer-period footprint changes and multi-session
holds. This candidate uses a within-session change after a
next-session-available typed earnings disclosure and exits that
date. GPT's failed typed earnings-gap, volume-surge, VWAP and
premarket-momentum studies are related broader search. The
formula does not make this an independent first look at demand
or momentum. No claim of market-wide novelty is made.

## One frozen signal

- Listed domestic common stocks, including later delistings
  while eligible. Require at least 20 prior matched sessions,
  prior split-adjusted close at least $2, prior median daily
  dollar turnover at least $2 million and prior market cap
  in [$50 million, $2 billion). Universe membership uses only
  the prior-session panel.
- Declare `inputs = {"form8k": {"sessions": 1}}`. Require
  at least one available earnings report, matching the current
  symbol and permaticker, with filing date strictly before
  the session. Use the engine's next-session availability rule.
  It does not identify a contemporaneous news timestamp, good
  news, analyst expectations or an earnings beat.
- Use normal sessions closing at 16:00. Require actual finite
  positive closes and positive share volume for every bar
  09:30 through 09:40 inclusive. The 09:30 close must be at
  least 1.05 times prior close; the 09:40 close must be at
  least 1.03 times the 09:30 close.
- Window 1 comprises 09:31–09:35 and window 2 09:36–09:40.
  The opening bar is deliberately excluded from print-size
  comparisons because it can mix the opening auction with
  continuous trading. Let V_j be total share volume and N_j
  total transaction count in window j. Require an observed,
  finite positive integer transaction count in every bar.
  Missing counts must never be replaced with zero or inferred.
- Define F = (V_2/N_2)/(V_1/N_1). Require N_1 and N_2
  each at least 100; N_2 at least N_1; and F at least 2.
  The integer inequality V_2 N_1 >= 2 V_1 N_2 implements
  the final boundary without floating-point ambiguity.
- Window 2 proxy dollar turnover, sum(close × volume), must
  reach 0.10 times prior median daily dollar turnover. The
  completed 09:40 bar must have at least $40,000 turnover.
  Send one signal per qualifying symbol after that bar.

The price and participation requirements form one hypothesis,
not separately selected alphas. No alternative windows, price
gates, count thresholds or footprint ratios are registered.

## Entry, exit and costs

Use $20,000 equity and buying power, $2,000 target per order,
ten positions or reservations and five-percent participation.
Buy with a cap of 1.005 times the decision close during
09:41 only, sizing against the cap. Cancel remaining entry
shares after that clock minute. Both modeled base and stressed
execution prices must fit each cap.

Begin liquidation 120 clock minutes after the first fill,
at 11:41 for an on-time entry. Use retrying one-minute sell
limits two percent below the last observed positive-volume
completed close, through the capped profile's 20:00 boundary.
Missing bars do not fill. No auction fallback is permitted.
Any unresolved position or exit at or after 16:00 invalidates
advancement; report such events explicitly.

Use `extended_v1` for its matched study/portfolio capped-order
semantics with a slippage multiplier of 1.0 for the intended
regular-session execution. Baseline is ordinary
`ibkr_pro_tiered`; stress doubles slippage with fees unchanged.
Each filled replacement is a new commission order. Minute
volume and range affect inferred capacity, costs and cap
feasibility. This is not quote-level evidence of an attainable
opening fill, and replaying signals does not validate it.

## Research sequence and gates

There is one variant. Do not run until transaction counts
are exposed, truncated by replay and tested in the platform.
No raw download, rebuild or extra derived input is needed.

1. Run `development --study` on 2003-09-10 through 2016-12-30
   and judge the registered r_120 execution policy only.
   Require 150 completed events on 90 dates overall and 40
   events in 2013–2016, mean gross at least +3% and positive
   stressed net in both windows, and strictly positive full-
   sample day-clustered 95% lower gross bound. Every entry
   must respect expiry. No unresolved or after-hours position.
   Park after any miss, with no portfolio or validation run.
2. After a committed develop verdict, run the same development
   portfolio once. Require 150 trades on 90 dates and 40
   trades in 2013–2016; mean net at least +2.5% at base
   and above +1% at doubled slippage in both windows; full
   stressed annualised daily Sharpe above one and worst
   stressed end-of-day drawdown below $10,000; no unresolved
   position or after-hours exit.
3. If selected, run validation once from 2017-01-03 through
   2023-11-08. Require +3% mean net across all completed
   trades at base costs and at least +1% at doubled slippage,
   both overall and in the separate 2022-01-03 through
   2023-11-08 block. Require 150 trades on 90 dates overall
   and 50 trades on 30 dates recently, positive base mean
   in 2017–2021, full stressed daily Sharpe above one and
   stressed drawdown below $10,000. No unresolved position
   or after-hours exit. No second validation attempt or tuning.

Report both costs, counts, years, daily P&L t-statistics,
worst drawdown, conditional winners and losers, delayed exits
and the Form 8-K input version. Identify isolated event P&L
as distinct from a capital-constrained account portfolio.
Count all runs. Never load the sealed period or a date on
or after 2023-11-09.
