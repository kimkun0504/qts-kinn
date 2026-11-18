# Opening-fill selection audit for the capped bar proxy

## Finding

`extended_v1` tests cap feasibility using modeled slippage
computed from the completed execution bar's range and volume.
Those statistics are not available at the bar's opening.
Consequently they affect which orders the model treats as
opening fills. This is an execution-selection dependency;
passing the strategy's prefix replay does not resolve it.

Synthetic checks in `tests/test_execution_inference_audit.py`
hold the order, prior history and opening price fixed. Changing
only the later execution-bar range changes fill acceptance.
Changing only volume can do the same even when either volume
would allow the full order under the participation cap.
These are implementation demonstrations, not empirical alpha
returns or calibration estimates.

The checks establish that the proxy depends on completed-bar
information. They do not establish the direction of return
bias or the true executable opening price, because there are
no observed opening quotes in the model. Calling the stricter
cap rule conservative does not prove conservative selection
of the eventual trade sample.

## What changed

Added a versioned inference-assumptions record to new capped
run manifests and their config hashes, study summaries and
portfolio summaries. Reports explicitly distinguish signal
replay from verification of fills. The existing fill arithmetic
and all old run outputs are preserved. No historical result
was recomputed and no new empirical trial was run for this audit.

The current reports for these GPT candidates retain this limit:

- `close_unwind_impact_decay`: parked, no filled events.
- `premarket_price_discovery`: parked after its negative study.
- `auction_gap_repair`: parked, no signals.
- `earnings_trade_size_shift`: untested, awaiting its declared
  transaction-count view and platform replay tests.

## What would resolve it

Execution-price and fill-selection checks need quotes available
at the order's decision and eligible execution times, with quote
sizes and timestamps, and trade/condition data for the active
minute. A prior-bar volatility proxy alone would not prove
opening liquidity or remove fill-model uncertainty. Filling at
the bar's worst price can also change the selected sample and
cannot be called an unbiased repair without testing.

The completed premarket study's saved `events.parquet` identifies
development symbols and entry/exit windows suitable for a quote
audit: run `20261118T135731Z_gpt_premarket_price_discovery_6fc253b3`.
Its stored period is before the seal. Any quote acquisition is
an owner-only raw-data action; GPT has not downloaded or written
raw files. A later quantitative audit must use versioned inputs
and the registered run store, not a scratch performance script.

The present changes expose the limitation. They do not claim
that it has been fixed or that a passing bar backtest alone
would establish the requested tradable edge.
