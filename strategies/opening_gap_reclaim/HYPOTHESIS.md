# Opening gap reclaim

Registered by GPT, 2026-11-15. A severe overnight down gap can reflect one-way urgent
sell orders at the open; a rebound in the first rotation may signal those orders are
being absorbed. Test whether there is additional recovery after the rebound is observable.
A down gap can instead be a permanent loss of value and the initial rebound can reverse.
This differs from Kinn's intraday decline event, which excludes down gaps of this size.
Charge this test to `intraday_rebound` anyway because both are long reversal hypotheses.
The shared registry has 48 prior family trials at registration, including nine pre-registry
looks. The earlier opening-gap continuation was a long trade on upward gaps.

Prior work documents substantial temporary liquidity imbalances during the session. The
evidence motivates the test and does not establish the sign or size of this particular
gap-down signal. [Heston, Korajczyk and Sadka, Intraday Patterns in the Cross-section of Stock Returns](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2010.01573.x)

## Frozen definition

- Use Kinn's listed domestic common stocks with at least 20 prior sessions, split-adjusted
  prior close of at least $5, and prior median daily dollar turnover of at least $2 million,
  with no size cutoff.
- Require the bars starting at 09:30 and 09:44 ET. The 09:30 open must be 15% to 40% below
  the prior close, inclusive. At 09:45, the last bar's close must be at least 3% above the
  opening price and still at least 8% below the prior close. Require at least $100,000
  of regular-session turnover through the 09:44 bar, approximated by minute close times
  volume. The remaining gap condition leaves room for the posited recovery.
- Place a market buy after the confirmation bar, live in 09:45–09:49 inclusive. Any
  remaining shares expire after the last eligible bar. At most one entry signal per
  symbol per session. Use no intraday stop or target.

The prior close can be stale after an interruption. Unrecorded corporate actions and
secondary-class shares can yield spurious gaps, and the security category uses the latest
vendor classification. We observe price and volume, with no seller identity or verified
catalyst. Compare year-by-year results to show any concentration.

## Research protocol

The sequence is `opening_gap_reclaim`, then `filing_session_momentum` if the first
strategy is parked in development. Each has one fixed definition. The first strategy to
qualify in development gets the slate's sole validation run. Finish each candidate before
starting the next. Two studies, up to two development backtests and one validation are
registered. Each run counts in its declared family, including failures. Development is
2003-09-10 to 2016-12-30. Validation is 2017-01-03 to 2023-11-08. The holdout starts
2023-11-09 and stays sealed.

1. Run `development --study` first. Use only the return to the official close for the gate.
   Develop only if there are at least 250 measured events across at least 150 sessions,
   the mean at 2× slippage is at least +1.00%, its day-clustered 95% interval has a
   positive lower bound and the mean at 2× is positive in both 2003–2009 and 2010–2016.
   Apply the same bars to the subset with entries within the registered order lifetime if
   the study includes any late entries. This is a diagnostic from the saved events because
   the study ignores expiry. Park if any bar fails.
2. After recording that gate result, run the `development` portfolio backtest for the
   same definition. Validate only with at least 250 filled trades across at least 150
   sessions, mean net of at least +1.50% per trade at 1× and +1.00% at 2×, positive 2×
   total net P&L in both development halves, annualised daily Sharpe above 1 at 2× and
   worst end-of-day drawdown less than $10,000 at 2×. Otherwise park.
3. Run the frozen `validation` config once for the qualifying strategy. Mark the +2.00%
   research target and +3.00% stretch target against its arithmetic mean net per trade at
   1×. Separately assess the owner's paper-trading criteria of +1.00% net at 2×, annualised
   daily Sharpe above 1, drawdown less than half the account, and tick confirmation.
   Evaluate the Sharpe and drawdown at 2× and require at least 150 filled trades and 100
   traded sessions for this slate. Tick confirmation needs a separate owner-run data
   check. Park a result that misses the statistical or risk bars. Report both cost
   scenarios, completed round trips, daily t-statistics, drawdowns and annual results.
   No validation result triggers another strategy run.

For both strategies use $20,000 equity and buying power, $2,000 target orders, at most ten
concurrent positions and orders, 5% bar participation, and `ibkr_pro_tiered`. Kinn
sizes at the signal close and reserves that approximate notional. Exit in the official
closing auction, with the engine's forced exit fallback. Modelled costs cannot confirm
execution. Minute opens, auction prices and bar volumes approximate live fills. The
event study charges two marketable sides using the entry bar and treats every event
individually. Use the full engine to test the actual participation, capital and auction
rules. Report the annual outcomes descriptively and leave thresholds fixed.
