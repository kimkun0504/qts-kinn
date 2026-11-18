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
