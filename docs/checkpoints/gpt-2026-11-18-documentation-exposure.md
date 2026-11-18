# Documentation-search exposure audit

## What happened

While checking the definition of Massive's aggregate transaction
count, a public web search returned the provider's Flat Files
Quickstart, including illustrative AAPL minute rows whose sample
timestamps are after the research seal. This was an accidental
post-seal documentation-sample exposure. It should not be
described as zero exposure to post-seal prices.

Source returned by the search:
https://massive.com/docs/flat-files/quickstart

No sample prices or volumes are copied into this repository.
The search also returned dataset listings and field descriptions;
no stock flat file, authenticated API, sealed folder or holdout
backtest was opened. There was no download, raw write or rebuild.

## Research state at exposure

The next hypothesis was already committed at `9160555` and
its strategy, configs and synthetic tests at `56eeaa2` before
the search. It has no empirical run. No parameter, universe,
score, entry rule or exit rule was selected or changed using
the sample. The opening-gap-repair study was already complete
and parked; its stored result is unchanged.

The unintentional sample exposure is still a departure from
the owner's instruction to exclude dates on or after the seal.
This audit records it so the owner can assess it explicitly;
it is not treated as if the sample had never been seen.

## Subsequent action

Stopped broad documentation searches and did not inspect or
analyse the sample. Any further vendor lookup must be confined
to field definitions or condition rules and avoid sample market
responses and file-browser pages. Preserve this audit alongside
the research reports. The pending transaction-count view change
still requires the separate owner authorization described in
`docs/requests/2026-11-18-minute-transactions-view.md`.
