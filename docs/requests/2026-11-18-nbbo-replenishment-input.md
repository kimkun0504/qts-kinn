# Scoped request: pre-decision NBBO snapshot input

Prepared for an owner decision. Strategy and exact signal:
`strategies/bid_replenishment_reversal/HYPOTHESIS.md`.
Price-control source:
`20261119T043722Z_gpt_bid_replenishment_reversal_91e8fd86`.
The source completed with 1,933 events on 937 dates, including
406 events in 2013–2016, passing the necessary acquisition
sample counts. The primary remains untested. The frozen
all-event plan and exact owner command are ready in
strategies/bid_replenishment_reversal/OWNER_ACTIONS.md.

## Question being tested

The control is an early six-point size-peer dislocation with
the existing recovery confirmation and two-hour holding policy.
It defines the complete candidate population. The primary adds
only the frozen transition from balanced/weaker displayed bid
size to a larger, bid-heavy, firm-priced quote. The control
cannot replace the primary.

The existing quote helpers and fill checker do not expose
pre-decision quote snapshots to an intraday strategy. The fill
checker reconstructs passive limits and rejects market orders.
A strategy privately opening raw JSON would bypass the native
view, availability replay and run provenance. That is not proposed.

## Acquisition artifact

The prepared deterministic planner
`research/gpt/plan_bid_quote_windows.py` reads only the completed
control's saved event times, company/symbol and pre-open fields.
It never selects by returns or existing quote availability.
It writes all windows under a new processed-data plan directory,
with source manifest/events hashes and schema `bid-quote-plan-1`.

Each window is [T-10 seconds, T+2 seconds), where T is the end
of the completed signal bar. The decision targets are T-5 seconds
and T-1 nanosecond. The owner downloader can use its existing
CSV format and one file per stock/date. The CSV's entry_price
compatibility field contains prior close, NOT a future fill price;
only time/symbol fields drive the download. This special plan
is not a generic quote-cost report or a trading order list.

The resulting windows.csv and exact owner command will be linked
after control completion. No quote price has been inspected for
this experiment. GPT will not download or write raw files.

## Requested native adapter and separate derived index

1. Add versioned input `nbbo_replenishment` /
   `nbbo-replenishment-1`, declaration sessions=1 (current
   session), and a specialized builder exposed by
   `kinn inputs build nbbo_replenishment --plan <plan>`.
   It reads the existing owner-downloaded raw quote windows
   and the immutable source plan. It builds only a separate
   snapshot index below processed inputs; no bar/panel rebuild.
2. Require the exact clean control manifest, source hashes,
   registered price definition and data build. Preserve every
   source candidate in the index. A missing raw file refuses
   the build; empty/stale/invalid observations have explicit
   status. Never choose the candidate population from quote
   availability or return outcomes.
3. At each of the two targets, select the latest SIP timestamp
   not later than the target. Select latest BEFORE validating:
   an invalid latest observation cannot resurrect an older
   favorable quote. Exact duplicates may collapse; conflicting
   feature values at the same latest timestamp are unavailable.
   Keep only same-date, in-window observations; fail closed
   on malformed provenance.
4. Validate one-second age, finite positive prices, strictly
   uncrossed/unlocked spread and positive integer displayed
   sizes. Treat sizes in their common vendor units. No absolute
   share-capacity or investor classification is inferred.
   Preserve unavailable reasons and report valid-pair coverage
   overall, in 2013–2016 and by year. The primary's 95% coverage
   gates are fixed in the hypothesis.
5. Add immutable QuoteSnapshot(sip_timestamp, bid_price,
   ask_price, bid_size, ask_size) and BookPair(day, symbol,
   permaticker, minute, status, early, late) types. Add
   DayView.book_pairs with a backward-compatible empty default.
   Expose only the pre-decision pair. No quote after T may
   enter the view, even though the raw window includes it.
   DayView.upto(cut) hides pairs with minute > cut.
6. Match the indexed company to that session's traded symbol
   and first parent signal minute. Unknown or conflicting
   parent identity/time is an error, not a silent negative
   quote label. Leave all pre-open peers in the reference
   irrespective of their quote eligibility.
7. Fingerprint parser version, source plan/manifest/events,
   price-definition provenance and raw quote contents.
   Build an immutable id, pin it in store/workers/resume,
   include it in config hashes and manifest inputs, and
   record source parent/coverage. Changing a current pointer
   must not change historical runs. Retain existing source
   hashes; do not rewrite the parent run.
8. Apply the holdout guard to requests, plan dates and quote
   timestamps. No unseal path. No network, keys or downloads.
   A range lacking the source candidate index fails clearly.
   Do not treat unknown archive coverage as observed absence.
9. Future validation acquisition, only after development qualifies,
   may enumerate the identical price triggers without computing
   forward returns, trades or P&L. A CLI/runner planning helper
   may load the registered strategy and write a source plan;
   the data layer must not import strategies or research.
   That plan is data acquisition for one frozen primary,
   followed by ONE validation performance run. No validation
   data is requested or read now.

## Scope and ownership

Platform changes requested only for this input's typing, builder,
store, native view/replay and run pinning/planning:

- `src/kinn/core/types.py`
- `src/kinn/data/inputs.py`, `store.py` and, if needed,
  narrowly shared pure snapshot/plan helpers in `quotes.py`
- `src/kinn/engine/intraday/data.py` and `strategy.py`
- `src/kinn/run.py`, `cli.py`
- focused tests, INPUTS documentation, scoped OWNERS row
  and a SALVAGE entry if planner logic is rewritten into
  the native interface.

No cost model, risk model, fill arithmetic, default execution
profile, existing input semantics or unrelated strategy changes.
The primary still uses the regular minute-bar execution proxy.
The post-decision raw seconds are reserved for a future separately
registered execution audit, not exposed as features or treated
as verified fills.

## Required tests before the primary run

Use native synthetic source/raw fixtures to test source/hash
validation, all-candidate enumeration, exact nanosecond targets,
DST, latest-before-target selection, invalid-latest behavior,
ties, positive sizes/prices, staleness, empty versus missing
files, post-decision perturbation invariance, no cross-date or
post-seal data, source identity/time mismatches, native prefix
replay and deliberate future-quote canaries. Verify manifest/
hash pinning, resume and spawned workers. Run the full test
suite, lint and import contracts; keep old views/inputs intact.

Prepared strategy tests currently use a clearly labeled
synthetic quote contract. They do not certify the unimplemented
native builder, availability or quote data.

## Why this needs a new owner decision

The original brief prohibits GPT platform edits and data rebuilds.
Existing exceptions cover extended execution, transaction counts
and timed 8-Ks, not a quote input or new snapshot index. AGENTS.md
states: "A change to a module you don't own goes to docs/requests/
as a short note, not as code." The relevant broad lanes remain
Claude's in OWNERS.md.

The owner must separately run the existing download helper,
which reads credentials and writes raw data. GPT will neither
execute it nor access its key. No approval is inferred from
elapsed time or the active research goal.

Owner decision: pending.
