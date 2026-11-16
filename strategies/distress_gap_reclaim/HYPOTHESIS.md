# Distress gap reclaim

Registered 2026-11-16. After a stock has lost most of its value,
good news or reduced selling pressure can change its expected
outcome sharply. A positive gap that survives an opening pullback
may reflect a repricing that continues intraday. The gap can also
reflect a transient squeeze, corporate action or speculative demand.
The rule observes price history. It does not identify actual news,
financial distress or short covering.

This is a follow-up to the opening-gap continuation work
(`20261116T002542Z_gpt_opening_gap_continuation_9db697d9`).
The earlier variant bought a positive opening move in the broad
eligible universe. This rule restricts the stocks by prior trend and
requires the opening gain to survive a selloff. It is one fixed
variant, charged to `opening_gap_continuation`. Earlier rebound
and stock-selection tests remain related looks.

## Frozen definition

- Use listed domestic common stocks including later delistings while
  eligible, at least 20 matched prior sessions, prior split-adjusted
  close of at least $3 and prior 20-session median dollar turnover
  of at least $2 million. Require a finite `ret60_prev` of −50% or
  less, using Kinn's split-adjusted price return through yesterday.
  This selects a large historical price loss. Use no size ceiling.
- Require the completed 09:30 regular-session bar, with an open at
  least 10% above the prior close. Exclude premarket prints.
- From 09:35 through 11:30 ET, take the first decision minute
  `t` for which the minimum observed regular-session close through
  `t−1` was at least 4% below the 09:30 open and stayed at or above
  the split-adjusted prior close. Require actual closes at `t−1`
  and `t`, with `t−1` below the level 1% above the 09:30 open
  and `t` at or above that level. Require decision-bar turnover of
  at least $40,000, the $2,000 target divided by 5% participation.
  Require at least 75 clock minutes before the calendar close.
  Missing closes do not establish whether prices crossed a level.
- Buy at market on the next clock minute only and hold 60 clock
  minutes from the first fill. Use a market exit with the normal
  auction fallback. All positions are closed on the entry date.
  Use $20,000 equity and buying power, $2,000 target notional, ten
  reservations, 5% bar participation and `ibkr_pro_tiered`.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30.
   Judge `r_60`. Require at least 150 events on 90 dates and
   40 events in 2013–2016. Require gross mean of at least +3%
   and positive mean net at 2× overall and in the later block.
   Require a strictly positive full-period lower 95% day-clustered
   gross bound. Apply all gates to on-time events as well if the
   study enters past expiry. Park after any miss.
2. After a committed develop verdict, run the `development` portfolio
   on the same dates. Require 150 trades on 90 dates and 40 trades
   in 2013–2016. Require mean net of at least +2.5% at 1× and
   above +1% at 2× overall and in 2013–2016, daily annualised
   Sharpe strictly above 1 at 2× and worst stressed end-of-day
   drawdown below $10,000.
3. If qualified, run `validation` once from 2017-01-03 through
   2023-11-08. Require +3% mean net across all completed trades
   at 1× and +1% at 2× overall and separately in 2022 through
   2023-11-08. Require 150 trades on 90 dates overall and 50 on
   30 in the recent block, positive 1× mean in 2017–2021, daily
   full-period Sharpe above 1 at 2× and worst stressed end-of-day
   drawdown below $10,000.

Report both costs, counts, calendar years, daily P&L t-statistics
and drawdown. Report winner and loser returns separately in a
portfolio. The study approximates both marketable legs from the
entry bar. The split-adjustment data can miss corporate actions,
and minute bars cannot confirm actual available depth. The sealed
holdout is excluded.
