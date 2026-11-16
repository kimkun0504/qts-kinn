# Intraday volume surge

Preregistered by GPT on 2026-11-15. In small caps, an extreme increase in traded dollar
volume alongside a large gain after a near-flat open may indicate continuing demand
relative to available liquidity. The competing explanation is that the surge reflects
buyers who have already paid for the move. Turnover measures activity and includes both
sides of every print. The test has no investor identity, short interest or order imbalance.
Barber and Odean find that individual investors tend to buy attention-grabbing stocks.
Whether demand persists beyond this entry is an open question.
[All That Glitters](https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/allthatglitters_rfs_2008.pdf)

New family `intraday_volume_surge`. Earlier Kinn studies tested upside opening gaps or
first-hour gains following a public filing. They used absolute turnover filters and
their results are already charged to their own families. This is the first look at
relative-turnover surges in small caps. Count it alongside those studies when assessing
the broader search. No additional parameters or alternative signals are permitted in this
registration.

## Frozen trade definition

- Listed domestic common stock with at least 20 previous observed sessions, split-adjusted
  prior close of at least $3, median dollar volume over the prior 20 sessions of at least
  $1 million and prior market cap below $2 billion. Exclude missing market cap. Membership
  uses the pre-open panel, which includes securities later delisted.
- Require a 09:30 bar with its open within 5% of the split-adjusted prior close. Evaluate
  completed bars from the one labelled 09:44 through 11:59 ET inclusive. Use the first bar
  where both it and the preceding clock minute close at least 20% above the 09:30 open and
  cumulative regular-session turnover through that bar has reached the prior full-day
  median. Approximate turnover with the sum of minute close times volume. A stale
  prior-minute print cannot count as confirmation. Send at most one order per symbol.
- Buy at market from the next bar and expire unfilled shares after five eligible clock
  minutes. Hold the fill to the same session's closing auction with Kinn's forced exit
  fallback. Use $20,000 equity and buying power, $2,000 target order size, up to ten
  positions or orders, 5% per-bar participation and `ibkr_pro_tiered`.

## Run sequence and bars

1. Run `development --study` for 2003-09-10 through 2016-12-30. Use return to the close
   only for selection. Require at least 250 events on at least 150 sessions, with mean
   return of at least +1.00% after 2× slippage, a strictly positive lower bound of the
   day-clustered 95% interval at 2×, and positive 2× mean in both 2003–2009 and 2010–2016.
   The study can measure events after order expiry. If it does, apply the same bars to the
   subset inside expiry using the saved event rows. Any failure means park.
2. After a recorded develop verdict, run the full `development` portfolio backtest.
   Select this sole variant for validation only if it has 250 completed trades across
   at least 150 sessions, mean net per trade at least +1.50% at 1× and +1.00% at 2×,
   positive 2× P&L in both development halves, annualised daily Sharpe above 1 at 2× and
   worst end-of-day drawdown strictly below $10,000 at 2×.
3. Run `validation` once if selected, 2017-01-03 through 2023-11-08. Assess the +2.00%
   research target and +3.00% stretch target on mean net return per completed trade at 1×.
   Assess the owner's paper-trading criteria separately, with mean net at least +1.00%,
   daily Sharpe above 1 and drawdown below $10,000 at 2×, and fills confirmed with actual
   trades. Also require at least 150 trades on 100 sessions. Report 1× and 2× returns,
   counts, daily P&L t-statistics, drawdown and annual results.

Each run counts. At most one study, one portfolio development run and one validation
run are registered. No date on or after 2023-11-09 is eligible.

## Risks and interpretation

Two consecutive closes limit the influence of an isolated print. Sharp rises can still
be driven by corporate actions, symbol coverage, sporadic liquidity or impending halts.
Market cap and category carry the panel's limitations. Minute bars contain no quotes
or halt flags. The study costs approximate both sides from the entry bar and ignore
portfolio constraints. A 2× stress doubles slippage on the same simulated fills, and
the close can be difficult to execute. Report the contribution of the best session and
the mean after dropping that session as descriptive checks for concentration, without
using them to change the registered decision.
