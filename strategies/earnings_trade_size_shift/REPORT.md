# Trade-size expansion after an available earnings disclosure

Status: awaiting the transaction-count view and its platform
replay tests. Hypothesis commit `9160555` precedes every
empirical run. The signal, entry, exit, dates and gates are frozen.

The prepared strategy compares average shares per transaction
across two five-minute windows after an available typed earnings
report. Price and activity must also progress. Print size is
not investor identity or evidence of informed demand.

Synthetic tests cover the exact ratio boundary, count growth,
missing or invalid counts, price and liquidity requirements,
opening-auction exclusion and fail-fast behavior when the view
has no counts. These do not substitute for the full prefix
replay once the platform exposes the field.

The exact platform request is in
`docs/requests/2026-11-18-minute-transactions-view.md`. The
source column already belongs to the built minute data.
There is no request for a raw write, download or rebuild.
The original platform restriction and the limited scope of
the extended-hours reassignment require a separate owner
decision before changing the data view. No empirical run
has started and no return estimate is available.

Vendor documentation confirms that sale conditions can affect
aggregate price and volume differently. The ratio is a vendor-
aggregate proxy, not a verified estimate of the size of the
trades setting price. The source and measurement caveat are in
the hypothesis addendum.

The same documentation search accidentally exposed illustrative
post-seal AAPL rows. The strategy and thresholds were committed
before that search and the example was not used to alter them.
The incident is recorded in
`docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`.
No empirical strategy run, sealed-folder access or holdout
backtest occurred, but zero post-seal exposure cannot be claimed.

A synthetic execution audit also confirms that completed-bar
statistics can change the opening-fill cohort. The pending
candidate has no empirical result to revise. Its future bar-
based result must be identified as provisional unless quote
checks establish feasible execution. The full audit and evidence
request are in `docs/requests/2026-11-18-opening-fill-selection-audit.md`.
