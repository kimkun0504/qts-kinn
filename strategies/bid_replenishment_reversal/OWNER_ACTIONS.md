# Owner actions for the frozen bid-replenishment experiment

The primary quote rule is committed. The completed price-only
control defines every acquisition window. No quote prices have
been inspected for this experiment.

1. Decide on the scoped platform adapter and separate snapshot
   index in `docs/requests/2026-11-18-nbbo-replenishment-input.md`.
   Existing authorizations cover execution, counts and timed
   8-Ks; this is a separate quote input.
2. Run the existing OWNER-ONLY downloader from the main repository
   `/Users/kkim/Desktop/QTS/qts-kinn/qts-kinn`:

```sh
KINN_AGENT=owner UV_NO_ENV_FILE=1 uv run --no-env-file --locked python tools/owner/download_quotes.py /Users/kkim/Desktop/QTS/MarketData/processed/kinn/quotes_sample/gpt_bid_replenishment_20261119T043722Z/windows.csv --workers 8
```

The helper fetches quotes and trades only for the dated development
windows and records failures. It uses the owner's credentials
locally; do not send an API key to GPT. GPT will not execute this
command or write raw data. No validation or sealed-holdout window
is requested.

All 1,933 control events are included, independently of returns
or existing-file availability. Features may use only quotes
before the decision boundary. The raw post-boundary seconds are
reserved for a future registered execution audit and are not
exposed as strategy features.

A file count alone does not prove usable quote coverage. After
authorized indexing, missing/stale/invalid observations remain
explicit, and the preregistered coverage and performance gates
still apply. No successful alpha has been established.
