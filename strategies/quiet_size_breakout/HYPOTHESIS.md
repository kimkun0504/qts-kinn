# Larger prints at a narrow-range breakout

Registered before empirical testing. The candidate asks whether
larger aggregate-recorded prints, with transaction activity
persisting, identify demand that has not yet produced a large
price move. It enters at the first small breakout from a narrow
recent range, measured at one fixed clock time. Repeated buying
could continue after visible supply at the old price is consumed.
The competing explanation is two-sided churn or temporary price
pressure that reverses after the breakout.

There is no identification of an institution, parent order or
signed demand. A volume/count ratio is affected by order splitting
and trade-condition rules. This is a proxy to test, not a new
mathematical law or proof that a familiar idea is unexploited.

## Prior research and family

Use the existing `big_prints` family, currently charged 50 trials
including 49 declared earlier looks. The earnings/trade-size
study used expanding prints after an already positive earnings
reaction and was parked after only two events. It is not being
loosened here. This candidate uses no earnings or filing label
and explicitly requires a small recent price move instead of
an existing large rally. Related volume-surge, VWAP and premarket
momentum failures are known. The smaller-print selloff study
and its control's later-period weakness are also known.

Those observations make this an adaptive follow-up. A new rule
and a one-attempt validation do not make the overall search or
the repeatedly examined 2017–2023 period globally pristine.
Only registered primary gates can select this candidate.

## Frozen base event and two variants

- Listed domestic common stocks including later delistings while
  eligible. Require 20 prior matched sessions, prior split-adjusted
  close at least $3, prior median daily dollar turnover at least
  $2 million and prior market cap in [$50 million, $2 billion).
  Universe membership uses pre-open panel columns only.
- Use normal sessions closing at 16:00 ET. There is one decision
  after the 09:59 bar. Require eleven actual consecutive bars
  from 09:49 through 09:59, with finite positive closes, positive
  integer share volumes and observed positive integer transaction
  counts. Missing minutes or counts cannot be imputed.
- Let H and L be the highest and lowest closes among the ten
  bars 09:49–09:58. Require H <= 1.02 L. Let C be the
  09:59 close. Require C >= 1.005 H and C <= 1.03 L.
  Thus the breakout begins before a large recent price expansion.
- Window 1 is 09:50–09:54; window 2 is 09:55–09:59. Let
  V_j and N_j be total share volume and transaction count
  in window j. Require N_1 and N_2 each at least 100.
  The 09:49 bar supplies a price reference and is excluded
  from both print-size windows.
- Window 2 proxy dollar turnover, sum(close × volume), must
  reach max($100,000, 0.05 × prior median daily dollar turnover).
  The decision bar must have at least $40,000 proxy turnover.
- **Control:** use that fixed base event, at most once per stock.
- **Primary:** use the identical event only when N_2 >= N_1
  and F = (V_2/N_2)/(V_1/N_1) >= 2. Implement the ratio
  boundary as V_2 N_1 >= 2 V_1 N_2 using integer arithmetic.
  There is no later opportunity to rescue a rejected stock.

Two development variants are registered: `development` (primary)
and `development_control` (base only). Both will run. Only the
primary can advance, even if the control has better returns.
The control tests the incremental value of the large-print
condition with identical event times. It is not a second
candidate from which to choose a favorable outcome.

## Trading and cost contract

Use the platform's ordinary regular-session market-order model,
$20,000 equity and buying power, $2,000 target per position,
ten positions or reservations, five-percent participation and
`ibkr_pro_tiered`. Buy at 10:00 only, cancelling remaining
entry shares at the end of that minute. Start market liquidation
120 clock minutes after first fill, at 12:00 for an on-time
entry, with the regular closing-auction fallback. Set flatten-
before-close to zero. There are no stops, targets or other exits.
Every position opens and closes that date. Stress doubles
slippage on the same simulated trades, with fees unchanged.

The regular event study uses its legacy close mark at r_120,
entry-bar costs for both legs, no capital constraints and can
measure entries after expiry. Apply all study gates to both the
full sample and the next-clock-minute subset. Report capacity
violations. The separate portfolio run is required before a
validation run because it applies actual simulated sizing,
participation, expiry and liquidation. Neither bar opening prices
nor the cost model establish attainable quotes or retail latency.

## Fixed selection gates

1. Run both development studies on 2003-09-10 through 2016-12-30
   and judge r_120 only. The primary needs 150 events on 90
   dates overall and 40 events in 2013–2016, mean gross at
   least +3% and positive stressed mean net in both windows,
   plus a strictly positive full-period day-clustered 95%
   lower gross bound. Require the primary stressed mean to
   exceed the control in both windows. Apply all those bars
   to full and on-time samples. Park after any miss. Do not
   substitute the control or select another horizon.
2. After a committed develop verdict, run the primary development
   portfolio once. Require 150 trades on 90 dates overall and
   40 trades in 2013–2016; mean net at least +2.5% at base
   and above +1% at doubled slippage in both windows; full
   stressed annualised daily Sharpe above one and worst stressed
   end-of-day drawdown loss below $10,000.
3. If selected, run the frozen primary validation once on
   2017-01-03 through 2023-11-08. Require +3% mean net
   across all completed trades at base costs and at least
   +1% at doubled slippage overall and separately from
   2022-01-03 through 2023-11-08; 150 trades on 90 dates
   overall and 50 on 30 dates recently; positive base mean
   in 2017–2021; full stressed daily Sharpe above one and
   stressed drawdown below $10,000. No tuning or second attempt.

There is no parameter or clock-time sweep. Report both costs,
counts, years, daily P&L t-statistics, worst drawdown, mean winners
and losers, on-time sensitivity and exact primary/control event
matching. Label event diagnostics separately from an account
portfolio and count every run in the family.

## Data and research limits

Prices and volumes are unadjusted intraday prints, with the
panel's prior-close adjustment and identity limitations. The
latest-category and market-cap weaknesses remain. No information
about same-day news absence, earnings surprises, signed flow,
hidden orders, halts or quoted depth is inferred.

The earlier accidental documentation-sample post-seal exposure
is recorded in `docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`.
This registration follows that incident and does not claim zero
historical post-seal exposure. No sample value is used here.
No new post-seal lookup, sealed-folder access, raw write, download,
rebuild or date on or after 2023-11-09 is permitted in these runs.
