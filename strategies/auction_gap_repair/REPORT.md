# Opening discount to an active premarket reference

Status: implementation under test. Hypothesis commit `2434f8f`
precedes every empirical run. One definition and one thirty-minute
liquidation policy are registered. The capped-execution profile
uses ordinary IBKR Pro tiered costs for these intended regular-
session fills, with the same fills stressed at doubled slippage.

The signal compares the first completed regular-session bar
with a recent, active premarket share-volume-weighted median.
It requires a remaining discount after recovery has begun.
Neither the anchor nor its mathematical definition establishes
fair value or an attainable fill.

The signal's weighted-median mathematics, stale-anchor and
liquidity rejection, early-close exclusion, prefix replay,
CLI loading and same-policy execution tests pass. Execution
regressions, repository rules and Ruff pass. No empirical
performance result is available yet.
