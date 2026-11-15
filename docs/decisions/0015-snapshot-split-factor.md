# 0015 — A split factor from the snapshot is kept, only to restore dividend amounts

**Status:** proposed, 2026-11-15 (claude). **Needs the owner's confirmation**, like 0009.

**Context.** Sharadar states dividend and spinoff amounts on today's share basis: adjusted for
every later split, including splits after the holdout seal. Example: Chesapeake's $0.045
dividend of 2004 is listed as $9.00 because of a 1-for-200 reverse split in 2020. Used as listed,
dividends were wrong by the size of every later split.

**Decision.** At ingest, each SEP row keeps `unadjust` = unadjusted close / split-adjusted close.
Multiplying a listed amount by `unadjust` on its ex-date gives the amount actually paid per
share that day. The split-adjusted close itself is still not kept.

**Why it is not lookahead.** `unadjust` on a pre-seal date does reveal that a split happened
later. It is used in one place (`build._write_master`, to write `master/dividends.parquet`), where
it cancels the same future information already inside the listed amount. The result is what a
shareholder received on the day. `unadjust` is not exposed by `DataStore`.

**Risk if misused.** Reading `unadjust` in research would leak future splits. A repo test
(`test_the_snapshot_split_factor_is_used_only_by_the_data_build`) forbids it outside the build.
