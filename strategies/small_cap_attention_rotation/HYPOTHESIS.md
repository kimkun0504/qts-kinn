# Small-cap attention rotation

Registered before any run. An early rally in several previously
weak small caps can draw demand toward other names with similar
trading characteristics. If lagging stocks then gain on abnormal
turnover, buying activity may persist past the first advance.
The early leaders can instead be reacting to unrelated news, and
buying the laggards can pay for a temporary price jump. Research
on return spillovers motivates the sequence. This cohort sorts on
capitalisation and prior returns, which are trading characteristics
and do not establish economic links.
[Cohen and Frazzini, Economic Links and Predictable Returns](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2008.01379.x)

Use the new `small_cap_attention_rotation` family. Earlier
`intraday_volume_surge` and opening momentum studies selected
stocks by their own activity. The Kinn market recovery lag study
used a broad large-cap selloff and recovery. Related search also
includes Claude's opening drive and stock-selection cells.
This rule selects delayed entrants to an already active cohort.

## Frozen definition

- Use listed domestic common stocks, including later delistings
  while eligible. Require at least 60 matched prior sessions,
  prior adjusted close at least $2, prior 20-session median daily
  dollar turnover at least $1 million, and prior market cap from
  $50 million inclusive to $2 billion exclusive. Require a finite
  split-adjusted price return of −20% or less over the 60 sessions
  ending at the prior close. This selects previously weak small caps.
- At 10:00 ET, identify early leaders using observations through
  the 09:59 bar. Each needs an actual 09:30 open and 09:59 close
  at least 10% above it, and turnover from 09:30 through 09:59 at
  least 50% of its prior median full-day dollar turnover. Require
  at least three distinct security identifiers satisfying those
  conditions that morning. The leader calculation never uses
  later prices. Approximate turnover by minute close times volume
  and exclude premarket prints.
- A tradable laggard is another member of that pre-open cohort
  with an actual 09:30 regular-session open within 5% of its prior
  close, and an observed 09:59 close within 2% of the regular open.
  Require actual closes in the bars labelled 10:13 and 10:14, each
  from 4% through 10% above the laggard's 09:59 close, inclusive.
  Turnover during 10:00–10:14 inclusive must reach 12% of the
  laggard's prior median full-day turnover. Require at least
  $40,000 of turnover in the 10:14 decision bar. Each laggard can
  signal once and needs at least 75 clock minutes before the
  calendar close. Leader and laggard identities must be disjoint.
- Enter at market only at 10:15, expiring at the end of that
  minute. Hold for 60 clock minutes from first fill and then sell
  at market with the engine's normal auction fallback. Use
  $20,000 equity and buying power, a $2,000 target per order,
  ten reservations, 5% bar participation and `ibkr_pro_tiered`.
  Positions open and close on the same day.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30
   and judge `r_60` only. Require at least 150 events on 90 dates
   and 40 events in 2013–2016. Require at least +3% gross mean
   and positive mean at 2× slippage overall and in 2013–2016,
   plus a strictly positive full-period 95% day-clustered lower
   gross bound. Apply the same gates to next-minute entries if
   the study admits later prints. Park after any miss.
2. After a committed develop verdict, run the `development`
   portfolio once on the same dates. Require at least 150 trades
   on 90 dates and 40 in 2013–2016. Require at least +2.5%
   mean net at 1× and above +1% at 2× both overall and in
   2013–2016, full-period 2× annualised daily Sharpe above 1
   and 2× worst end-of-day drawdown below $10,000.
3. If qualified, run frozen `validation` once from 2017-01-03
   through 2023-11-08. Require +3% mean net over all completed
   trades at 1× and +1% at 2× overall and separately in
   2022-01-03 through 2023-11-08. Require at least 150 trades
   on 90 dates overall and at least 50 trades on 30 dates
   in the recent block, positive 1× mean in 2017–2021,
   2× full-period annualised daily Sharpe above 1 and 2× worst
   end-of-day drawdown below $10,000.

Register one definition. Count every run. Report study and portfolio
counts, daily P&L t-statistics, worst drawdown and yearly results at
both costs. Report conditional win and loss means for completed
portfolio trades. More than one trade from the same session can
share a common shock. The study models entry pricing and both
cost legs from minute bars without measuring actual execution.
Keep the sealed holdout excluded.
