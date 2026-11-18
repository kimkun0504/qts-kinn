# Opening discount to an active premarket reference

Registered before any empirical run. The earlier premarket
continuation study failed. This is a separate hypothesis about
the transition into the regular session: a price discontinuity
relative to active trading just before the opening, followed by
recovery in the first regular minute. The proposed source of
return is an opening liquidity imbalance that partly corrects
once continuous trading begins. Competing explanations are
new adverse information, misleading premarket prints or a
premarket price that was itself too high.

The premise does not assume that institutions are absent before
the open. A price anchor summarizes observed trading, not fair
value. The formula is a direct discrepancy measurement and
makes no claim of mathematical novelty or an unused market edge.
The empirical test decides whether it predicts attainable returns.

## Family and prior looks

Charge this to `intraday_rebound`, whose current shared count is
106 including nine declared earlier looks. It began this program
with 48 trials. The prior opening-gap reclaim used yesterday's
close as its anchor and waited through the opening rotation.
The strong size-peer development result and its later recency
failure are also known, as are failed attempts to improve that
class using early clock exits. This candidate uses a same-day
premarket reference and enters after the first minute, with one
fixed short holding policy; it is not an exit sweep on that class.

Claude's latest inspected branch `agent/claude/intraday-entry`
at `c173694` includes related after-hours, night-bid and
intraday-shape research, primarily with overnight or multi-session
holds. Those prior looks inform the broader search history.
They are not this candidate's results or fresh validation evidence.
The earlier volume and VWAP studies remain part of the search.

## One frozen signal

- Listed domestic common stocks including subsequent delistings
  while eligible. Require 20 prior matched sessions, prior split-
  adjusted close at least $2, prior median daily dollar turnover
  at least $2 million and prior market cap in [$50 million, $2
  billion). Use the pre-open panel only for universe membership.
- Use normal calendar sessions closing at 16:00 ET. Form the
  reference from observed bars labelled 09:00 through 09:29.
  Require at least 15 valid bars in this interval, each with
  finite positive close and positive volume, including the actual
  09:29 bar. No earlier or regular-session bar enters the anchor.
- Let M be the share-volume-weighted median of these minute
  closes: sort the closes in ascending order and choose the
  first whose cumulative share volume reaches half the total.
  If the cumulative volume is exactly half, use that lower
  median price. This is a bar-based summary of trading, not
  a true transaction-level median or an order-book midquote.
- Require M at least 1.15 times prior close. Require the
  09:29 close in [0.98 M, 1.02 M] and at least $20,000
  turnover in that bar, approximated by close times volume.
  Total proxy dollar turnover in the reference window must
  reach max($250,000, 0.10 × prior median daily dollar turnover).
  These requirements reduce reliance on one stale or isolated
  premarket print; they do not establish executable prices.
- Require the actual 09:30 bar with finite positive open and
  close. Its open O must be at most 0.90 M. Its close C
  must be at least 1.01 O and at most 0.95 M, leaving a
  discount after recovery has begun. Require at least $40,000
  proxy turnover in the completed 09:30 bar. Generate one
  signal after that bar, regardless of any later prices.

## Entry and early liquidation

Use $20,000 equity and buying power, $2,000 target per order,
ten positions or reservations and five-percent share participation.
Buy with a cap of 1.005 C during 09:31 only. Size whole shares
against the cap; an unfilled or partially filled remainder
expires after that clock minute. Require both modeled base
and doubled-slippage execution prices to fit the cap.

Liquidation starts 30 clock minutes after first fill, at 10:01
for an on-time fill. Use a sell limit two percent below the
last observed positive-volume completed close. The order expires
after the next minute and is replaced from the close then
available. Gaps through the cap do not fill at that opening.
Missing bars cannot fill. Retry through 20:00 ET under the
tested capped-execution profile; report any exit after 16:00.
Any unresolved position at that boundary fails the same-day
requirement. No auction fallback supplies a fictitious exit.

Implementation uses `extended_v1` to apply the identical
capped-order policy in the study and portfolio. Its configured
entry window is 09:31 only. Because the intended executions
are during the regular session, set its slippage multiplier to
**1.0**: the base is the ordinary `ibkr_pro_tiered` marketable
spread and impact, and stress doubles it. Each filled replacement
is a new commission order. An exit that slips into after-hours
would be costed too cheaply by this setup; **any such exit also
fails advancement**, even if it eventually closes that date.

## Research sequence and fixed gates

There is one variant and one holding policy, with no comparator,
threshold search or alternative exit registered.

1. Run `development --study` on 2003-09-10 through 2016-12-30,
   measuring the scheduled thirty-minute liquidation policy only.
   Require 150 completed events on 90 dates overall and 40
   events in 2013–2016. Require mean gross at least +3% and
   positive mean net at doubled slippage in both windows, with
   strictly positive full-period day-clustered 95% gross lower
   bound. Every filled entry must respect the one-minute expiry.
   There may be no unresolved position or after-hours exit.
   Any miss means park, with no portfolio or validation run.
2. After a committed develop verdict, run the same development
   portfolio once. Require 150 trades on 90 dates overall and
   40 trades in 2013–2016, mean net at least +2.5% at base
   costs and above +1% at doubled slippage in both windows,
   full stressed annualised daily Sharpe above one and worst
   stressed end-of-day drawdown loss below $10,000. No unresolved
   position or after-hours exit is allowed.
3. Only if selected, run validation once on 2017-01-03 through
   2023-11-08. Require at least +3% average net across all
   completed trades at base costs and +1% at doubled slippage,
   both overall and separately from 2022-01-03 through 2023-11-08.
   Require 150 trades on 90 dates overall and 50 trades on
   30 dates in the recent window; positive base mean in
   2017–2021; full stressed daily Sharpe above one and worst
   stressed drawdown below $10,000. No unresolved or after-hours
   position is allowed. Do not tune after seeing this run.

Report both costs, counts, years, daily P&L t-statistics,
drawdown, mean winners and losers, delayed exits and the input
build. Event-study P&L ignores account capital conflicts and
must be identified as such. Count every run and keep the seal.

## Data and execution limits

The opening price is the first price in a minute aggregate,
not necessarily an attainable official-auction fill. The entry
uses the following minute and never assumes the first-minute
low is obtainable. Minute volume and range approximate subsequent
capacity and impact; they cannot establish opening-print depth,
quoted spreads, queue priority or true transaction-level volume
distribution. Share categories and market capitalisation have
the panel's documented weaknesses. No contemporary news label,
headline timestamp or analyst expectation is inferred. No data
rebuild, raw write, current motivating stock example, or date
on or after 2023-11-09 is permitted.
