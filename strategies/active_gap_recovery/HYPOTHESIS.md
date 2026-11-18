# Recovery after an active-stock trading gap

Registered before any empirical run of this rule. A temporary
interruption can leave a thin market when trading resumes. In a
stock already rising on active trading, a downward discontinuity
followed by recovery within the first returning minute might
reflect temporary liquidation rather than a complete reversal.
The competing explanation is adverse information or a genuine
end to demand. This is a conjecture to falsify.

The bars contain no halt status, quotes or order book. A missing
interval is only a trading-gap proxy: inactivity, vendor omissions
and exchange interruptions can look alike. The rule cannot identify
a halt or assume that it could buy during one. A new formula or
unusual event definition supplies no evidence of an edge.

## Existing information and family

Charge the rule to `intraday_rebound`, which carries 109 counted
or declared looks at registration, including nine earlier declared
looks. The original brief's 48 trials have already been exceeded
by subsequent work. Related price-only rebounds, failed recovery
confirmation and the later-period weakness of relative-dislocation
variants are known. This rule tests a missing-minute discontinuity
after dense prior trading; it is another adaptive look in that
family, not an independent new family.

The existing filing-time scripts were inspected before registration.
They use SEC acceptance times, which can follow a press release.
They are not an existing declared intraday input. No filing-time
script or external news data is used here. The typed date-level
filing inputs cannot establish the first publication minute.

The documentation sample exposure recorded in
`docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`
predates this registration. No sample values enter this rule.
Prior strategies have already used 2017–2023; that period is not
globally pristine. No date from the sealed holdout will be loaded.

## One frozen variant

- Use listed domestic common stocks, including later delistings
  while eligible, with 20 prior matched sessions, prior
  split-adjusted close at least $3, prior median daily dollar
  turnover at least $2 million, and prior market capitalisation
  in [$50 million, $2 billion). All membership values are pre-open.
- Use only normal 09:30–16:00 sessions and require an actual 09:30
  open. Examine first returning bars t from 09:46 through 14:30
  ET inclusive. Let p be the preceding observed bar's minute.
  Require 5 through 30 wholly missing clock-minute bars between
  p and t, equivalently 6 <= t-p <= 31.
- Require all ten actual consecutive bars p-9 through p, entirely
  within regular hours, with finite positive valid OHLC, positive
  integer volume and observed positive integer transaction counts.
  Their aggregate count must be at least 1,000; proxy dollar
  turnover (sum of close times volume) at least the greater of
  $200,000 and 10% of prior median daily dollar turnover. The
  last pre-gap bar must have at least $40,000 proxy turnover.
  Its close P must be at least 10% above the 09:30 open.
- Each missing minute must have an observed bar with valid positive
  close and positive volume for at least ten distinct other company
  identifiers in the same pre-open universe. This rejects an
  obvious universe-wide missing interval, but cannot certify the
  target's feed or infer a halt.
- The returning bar must have finite positive valid OHLC,
  positive integer volume and observed positive integer count
  of at least 100. Require at least $40,000 proxy turnover.
  Its open O must be <= 0.95 P. Its close C must satisfy
  C >= 1.01 O and C <= 0.95 P. Thus a first-minute recovery
  must leave a discount of at least 5% to the last pre-gap close.
- Take the first qualifying event per symbol per session. Submit
  a regular-session market order for only the next clock minute,
  expiring at the end of that minute. Hold for 30 clock minutes
  from first fill, then sell at market using the engine's regular
  closing fallback where necessary. No stops, targets, second
  entry, alternative threshold or alternative exit is registered.
- Account and buying power $20,000; target $2,000 per position,
  ten reservations, 5% per-bar participation and
  `ibkr_pro_tiered`. Positions open and close the same day.

## Run sequence and decision

1. Run one `development --study`, 2003-09-10 through 2016-12-30.
   Judge only `r_30`. Require at least 150 events on 90 dates,
   at least 40 events in 2013–2016, mean gross >= +3% and mean
   net at doubled slippage > 0 both overall and in 2013–2016,
   and a strictly positive full-period 95% day-clustered gross
   lower bound. Apply every gate again to next-clock-minute
   entries if the legacy study includes later entries. Park
   after any miss. There is no control eligible to replace it.
2. Only after all study gates pass and a committed develop verdict,
   run the `development` portfolio once. Require at least 150
   completed trades on 90 dates, 40 trades in 2013–2016, mean
   net >= +2.5% at base costs and > +1% at doubled slippage in
   both blocks, full-period stressed annualised daily Sharpe > 1
   and stressed worst end-of-day drawdown loss < $10,000.
3. Only if every portfolio gate passes, run one frozen `validation`,
   2017-01-03 through 2023-11-08. Require mean net across all
   completed trades >= +3% at base and >= +1% at doubled slippage
   overall AND separately in 2022-01-03 through 2023-11-08.
   Require 150 trades on 90 dates overall, 50 on 30 dates in
   the recent block, positive base mean in 2017–2021, full-period
   stressed daily Sharpe > 1 and stressed drawdown loss < $10,000.
   No tuning or retry follows validation.

At most three empirical runs are registered; every run counts.
Report the actual run IDs, counts, annual returns and dollar P&L,
daily P&L t-statistics, worst end-of-day drawdown, and conditional
winner/loser means at both costs. Returns refer to all completed
events/trades, not the mean winner.

## Execution and data limits

The normal event study ignores entry expiry, capital constraints
and per-bar participation, uses a horizon close rather than the
portfolio's timed exit open, and estimates both cost legs from
the entry bar. Report any late entries and targets exceeding 5%
of entry-bar volume. A study pass is not a portfolio pass.

Reopening bars can have wide spreads and thin depth; the standard
cost fallback and doubled slippage cannot establish actual fills.
Counts are aggregate transaction observations, not signed flow or
trader identity. The other-company check cannot rule out missing
target data. Report any positive result as a bar-model candidate
requiring quote/trade verification. Missing bars must remain
missing; they may never be filled with interpolated prices.
