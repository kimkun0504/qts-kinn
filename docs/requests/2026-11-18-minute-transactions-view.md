# Expose existing minute transaction counts in the strategy view

Prepared for a scoped owner decision before implementation.
The candidate is preregistered in
`strategies/earnings_trade_size_shift/HYPOTHESIS.md`.

## Confirmed source and gap

`kinn.data.bars` already writes Massive's `transactions` column
to the minute Parquet files. `DataStore.minute(..., columns=...)`
can select it from the sealed-guarded build. No raw data access,
download, additional input build or rebuild is needed.

`kinn.engine.intraday.data.load_day` selects only OHLC and
volume, and `SymbolDay` has no transaction-count member. A
strategy therefore cannot measure average shares per print
through its authorized view. Reading a second data stream inside
strategy code would bypass the intended interface and manifest
discipline and is not proposed.

## Exact requested implementation

Only `src/kinn/engine/intraday/data.py` and focused tests need
platform changes:

1. Append optional `transactions: np.ndarray | None = None`
   after `prior` in `SymbolDay`, preserving all existing
   positional constructors. None means unavailable, never zero
   inferred transactions. Preserve real missing entries rather
   than silently filling them.
2. In `SymbolDay.upto`, truncate the count array with the
   identical prefix length as price and volume. Preserve None.
   Transaction counts become available at the close of their
   bar, with the same replay boundary as volume.
3. Add a keyword-only `transactions=None` argument to
   `make_symbol_day` for synthetic fixtures, preserving old
   calls and alignment. Validate one-dimensional alignment
   when the field is supplied.
4. Select the existing `transactions` column in `load_day`,
   pass the corresponding symbol slice to `SymbolDay`, and
   give an empty count array to members with no bars. Do not
   replace missing per-bar counts with fictitious values.
5. Test real loader-column propagation using a fake store,
   typed alignment, truncation, unavailable values, zero-bar
   members, legacy construction, and a strategy prefix canary.
   Retain ordinary fill and existing strategy results.

The run's existing data build ID pins the minute data; the
code commit pins the added view semantics. This exposes a
field of the existing build, not an undeclared external input.
No ingestion, calendar, seal or cost-model changes are requested.

## Why a separate authorization is required

The original brief prohibits GPT edits under `src/kinn/`.
The earlier explicit reassignment covers extended-hours
execution, not general research data-view expansion. AGENTS.md
states: “A change to a module you don't own goes to
`docs/requests/` as a short note, not as code.” OWNERS.md
retains Claude's broader platform lanes. GPT will not modify
the platform data view until the owner explicitly assigns
this narrow change or the lane owner supplies it.

The proposed strategy can use missing-data rejection and has
no permission to infer a transaction count or bypass the view.
Its empirical results remain unmeasured until this dependency
and the lookahead replay tests are satisfied.

## Owner authorization

The owner selected “Authorize the scoped transaction-count
view change” in this chat on 2026-11-18. The corresponding
narrow lane is recorded in OWNERS.md. GPT may implement the
field, loader propagation and replay tests specified above.
The signal and research thresholds remain frozen. No data
download, raw write, input rebuild or ingestion change is
part of the authorization or implementation.
