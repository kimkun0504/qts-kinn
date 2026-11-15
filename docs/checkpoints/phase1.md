# Checkpoint: Phase 1 (data layer), 2026-11-15

**Done.** Bars `65fa113929` (5,077 daily and 5,077 minute sessions as Parquet, 2003-09-10 to
2023-11-08) and build `07b6a77a41` (security master, symbol history, splits, daily panel,
Sharadar tables). Reports: [../data/AUDIT.md](../data/AUDIT.md),
[../data/DATA_NOTES.md](../data/DATA_NOTES.md).

Commands: `kinn data bars`, `kinn data build`, `kinn data audit` (all resumable).

## What the audit says

- Massive and Sharadar agree on all 5,077 sessions. Where both have a close, they are within
  1% on 98–100% of company-days.
- Every listed common-stock day matches. The 6–15% of Sharadar days with no Massive bar are
  OTC days (delisted to pink sheets), which Kinn should not trade anyway.
- Bars are unadjusted; splits come from Sharadar and check out on known cases.
- Extended hours are in the data: 08:00–20:00 in 2003–2004, 04:00–20:00 from 2005.
- **No quotes and no halt flags.**

## Decisions taken that need the owner's eye

| # | Decision | Where |
|---|---|---|
| 1 | Read post-seal ticker-change events to recover pre-seal symbols; nothing else post-seal | decision 0009 |
| 2 | `category` and `exchange` are the 2026 labels, not point in time | DATA_NOTES |
| 3 | Sharadar `marketcap` assumed point in time, not verified | DATA_NOTES |
| 4 | Fundamentals, insider and 13F tables not ingested (no current use) | DATA_NOTES |

## Tests added

Seal (5), data build end to end on synthetic vendor files (15), including: no processed file
holds a holdout date or the planted marker; renames before and after the seal; a reused symbol;
a split; and the point-in-time canary (a build that ends earlier agrees on every earlier row).
