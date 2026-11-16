# Filing-session momentum

Registered by GPT on 2026-11-15. New family `filing_session_momentum`, with zero prior
trials. Test whether a strong upward move after a near-flat open on a session following an
8-K filing exhibits continuation. This tests an intraday move with a known filing. The
previous opening-gap momentum study required a positive overnight gap and did not use a
filing criterion. The filing is a dated disclosure proxy and may be unrelated to the
price move, previously anticipated, or older than it appears.

Research using intraday timestamped news finds drift after the initial price reaction.
Kinn's prior-session filing indicator is much coarser. The proposed proxy and holding
horizon stand or fail on their own results. [Jiang, Li and Wang, Pervasive underreaction](https://www.sciencedirect.com/science/article/pii/S0304405X21001306)

## Frozen definition

- Use Kinn's listed domestic common stocks with at least 20 prior sessions, split-adjusted
  prior close of at least $5, and prior median daily dollar turnover of at least $2 million,
  with no size cutoff. Require one or more 8-K filings in Kinn's pre-open
  `filings_prev` window. The panel excludes filings dated today.
- Require bars starting at 09:30 and 10:29 ET. The 09:30 open must be within 3% of the
  prior close. At 10:30, the last bar's close must be at least 6% above the 09:30 open.
  Require at least $200,000 of regular-session turnover through the 10:29 bar, approximated
  by minute close times volume.
- Place a market buy after the confirmation bar, live in 10:30–10:34 inclusive. Any
  remaining shares expire after the last eligible bar. At most one entry signal per
  symbol per session. Use no intraday stop or target.

This design can chase overreaction. A count of filings does not identify what information
moved the price or when market participants learned it. Corporate actions, stale prior
closes, and changes in disclosure practices can affect the sample.

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
