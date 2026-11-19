# Scoped request: coherent pre-open ART financial snapshot

Prepared for an owner decision. The new frozen experiment is
`strategies/cash_profit_reversal/HYPOTHESIS.md`, committed before any
empirical run. The strategy, configs and proposed-contract tests are
prepared on `agent/gpt/cash_profit_reversal`. No financial cohort return
or count has been queried, and no empirical trial has been used.

## Why this interface is needed

The existing pre-seal data build contains SF1 as-reported ART rows with
opinc, ncfo, datekey and reportperiod. A schema-only check confirmed
those columns in build `447e58e098`. No download, raw access, separate
derived build or bar/panel rebuild is needed.

DataStore.fundamentals and DailyView already support daily research.
Daily `_as_of` carries the last non-null value independently per field.
That is not a coherent pair from a single row. It cannot establish that
two fields share one reportperiod/datekey. This request does not call
that existing per-field contract a bug or change its behavior. The
intraday DayView has no financial snapshot, and a private strategy
loader would bypass native availability, replay and run provenance.

## Exact small native contract

1. Add declared input `fundamentals_art`, version `fundamentals-art-1`,
   sessions=1 only: the current session's pre-open snapshot. It reads
   fixed fields opinc and ncfo from ART only in the existing pinned build.
   No MR/restated dimension, consensus, price field or arbitrary-field
   plugin system. A missing source or unsupported version fails clearly.
2. On session D, only source rows with datekey < D are known. Match by
   the build's company identifier and current traded symbol. Within each
   company select latest filing date first; among that date use latest
   reportperiod. Do this before checking field validity. A missing
   reportperiod at latest filed date is unavailable. Exact duplicate
   paired feature values may collapse; conflicting paired values at the
   selected keys are unavailable. Never select an older favorable row
   after missing/invalid/conflicting latest data, or carry one field
   independently from another reporting vintage.
3. Add immutable core value
   `FundamentalSnapshot(symbol, permaticker, dimension, filed,
   reportperiod, opinc, ncfo, status)`. Here filed is SF1 datekey, not an
   acceptance time. Status is available, missing, conflict or invalid.
   Missing values/dates may be None. Negative/zero finite amounts remain
   available. Preserve explicit unavailable status for a session member;
   unknown/mismatched company identity is an error, not a profit label.
4. Add `DayView.fundamentals` with backward-compatible empty default.
   Declaring strategies see the native snapshot by symbol; undeclared
   strategies retain their existing behavior. The records are known
   before the open and are identical in every intraday prefix. All other
   peers remain in the view regardless of financial availability/sign.
   The strategy applies its fixed 180-day reportperiod freshness and
   optional positive-sign predicate; this is not a builder's selection.
5. Pin code version, source/build identity and source content in input id,
   configuration hash, manifest, resume and spawned workers. Record fields,
   ART dimension, row-selection and next-session availability semantics
   and observed source envelope. As with form8k, it reads the existing
   build and needs no separate build command or CURRENT data pointer.
   `kinn inputs show fundamentals_art` should expose this metadata.
6. Every request and source row passes the holdout guard, even if a store
   otherwise has an unseal flag. No unseal path. Same-day/future filings
   cannot alter an earlier snapshot or its missingness label. A corrupt
   source must not leak post-seal fields or cause silent fallback.
7. SF1's built rows have no SEC accession in this interface. Coherence
   means the same vendor source row/datekey/reportperiod/dimension; it
   does not certify an actual accession, first release, historical vendor
   delivery time or a separately audited vintage/revision history.

## Required verification before either empirical run

Native synthetic source fixtures must cover ART versus restated rows,
filing-day invisibility/next-session availability, weekend boundaries,
latest filing/reportperiod ordering, invalid latest values with older
positive rows, independent-field mixing canary, exact duplicates,
conflicting ties, missing dates/values and zero/negative values.

Also test identity matching and ambiguity, stale/current reportperiods,
same-day/future/post-seal perturbations, no unseal path, typed native
DayView and every-prefix replay, an intentional future-data canary,
source/build/config/manifest pinning, resume and spawned workers.
Migrate the explicitly labeled contract fixtures to native types and
integration tests. Run the full suite, lint/format and import contracts.

Do not interpret primary/control returns until both complete and the
exact-subset audit passes. Preserve the preregistered two-hour horizon,
account, costs, sample/risk/recency bars and one-attempt validation.

## Scoped files and exclusions

Only typing, read-only snapshot/query, input metadata and native
view/runner/CLI wiring:

- src/kinn/core/types.py
- src/kinn/data/store.py and inputs.py
- src/kinn/engine/intraday/data.py and strategy.py
- src/kinn/run.py and cli.py
- focused tests, docs/data/INPUTS.md and the scoped OWNERS row

No daily API or `_as_of` changes, features registry expansion, cost,
risk, fill or execution changes. No raw write, key, download, rebuild,
sealed access, unrelated platform module or another agent's strategy.
No platform code is included in this prepared proposal.

## Why a new owner decision is required

The original brief prohibits GPT edits under src/kinn. AGENTS.md says:
"A change to a module you don't own goes to docs/requests/ as a short
note, not as code." OWNERS.md assigns these broad lanes to Claude.
Earlier owner exceptions cover extended execution, transaction counts,
timed 8-K and NBBO snapshots. None covers this new financial snapshot.

Requested decision: authorize the exact scoped read-only intraday
financials view above. Its source is already built, so no additional
data purchase, download or build exception is requested. No approval is
inferred from elapsed time or from the active research goal.
