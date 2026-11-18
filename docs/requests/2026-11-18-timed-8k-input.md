# Scoped request: timestamped original 8-K input

Prepared before any implementation in protected platform lanes.
Candidate: `strategies/timed_earnings_discovery/HYPOTHESIS.md`.
Decision requested: authorize the narrow adapter AND a new
derived-input build from the existing raw SEC 8-K timestamp
file. The existing bar/panel data build stays as it is.

## Existing source and interface gap

The known path `raw/sec/filing_times/8k.jsonl.gz` exists.
The owner's downloader writes CIK, accession, form, filed,
accepted and items, filtered by filing date before the seal.
Only source code and file existence were inspected for this
proposal; no raw empirical measurement was made.

Existing form8k exposes date-level item records from Sharadar,
usable next session. It cannot supply same-evening acceptance
times. A strategy must not privately read the raw archive.
The timed input will remain separate so date-only strategies
retain their availability rule and manifests.

## Exact proposed native contract

- Input name/version `form8k_timed` / `form8k-timed-1`.
  Declaration `{"form8k_timed": {"sessions": 1}}` means
  current-New-York-session accepted filings only; support only
  this one-session contract initially.
- Preserve one original 8-K per accession/company. No amendments,
  other forms, stake records, later item merging, investor
  classification, press-release inference or frequency screen.
- Add typed `TimedReport(symbol, permaticker, accession, form,
  filed, accepted, items, earnings, usable_minute)`.
  `accepted` is an aware UTC datetime parsed with explicit
  timezone information. Missing/naive/invalid timestamps are
  rejected, not assumed UTC. Derive local date/minute with
  America/New_York and derive earnings from item 2.02.
- Conservative availability: usable_minute =
  floor(New York acceptance minute) + 1, as a completed-bar
  label. A strategy can act at the following opening minute
  at the earliest. DayView.upto(cut) hides records whose
  usable_minute > cut as well as later price bars. A three-bar
  candidate then observes m+1, m+2, m+3 and orders at m+4.
- Add `DayView.timed_reports` with an empty default, preserving
  legacy constructors. Load only matching session/company
  records for the current point-in-time universe. Sort oldest
  first, with accession tie-breaks. Keep each accession's items
  separate. Hide future-session filings and same-session
  not-yet-usable filings in prefix replay.
- Resolve issuer CIK through the existing Sharadar identity
  source's SEC link and permaticker, restricted to identities
  in the pinned pre-seal build. Read only identity fields from
  the existing snapshot. Reject missing/conflicting identity
  rather than guessing. Match symbols from that day's build
  universe, not today's ticker. Document static CIK-mapping
  limitations; do not generalize this to stake-subject roles.
- Enforce the seal on requested date ranges and on BOTH filed
  and local acceptance dates at build/read time. Reject
  post-seal records and ambiguous times. Store no post-seal
  records. No unseal path is added.
- Build a separate immutable dataset below
  `processed/kinn/inputs/form8k_timed/<input_id>/`; pin its id
  in workers, resume, manifest and config hash. Fingerprint
  parser version, source content and identity build/mapping.
  Persist source and rejection/coverage metadata, including
  timestamp, item, duplicate and identity failures. Fail clearly
  on missing data/coverage instead of silently supplying an
  empty unknown input.
- Extend `kinn inputs build/show` only for this input.
  Execute only the newly authorized derived-input build.
  Do not run `kinn data build`, rebuild bars/panel, download,
  write to raw or inspect sealed directories.

## Platform files and ownership

Proposed changes are limited to:

- `src/kinn/data/inputs.py`: builder, schema, id/metadata;
- `src/kinn/data/store.py`: pinned, seal-guarded timed read;
- `src/kinn/core/types.py`: appended TimedReport type;
- `src/kinn/engine/intraday/data.py`: view/load/prefix field;
- `src/kinn/engine/intraday/strategy.py`: declaration handling;
- `src/kinn/run.py`: declaration pinning and worker propagation;
- `src/kinn/cli.py`: explicit input build/show entry;
- focused tests, `docs/data/INPUTS.md` and the scoped OWNERS row.

No cost, risk, fill, universe, bar ingestion, existing input
semantics or unrelated strategy changes are included.

## Required verification before the research run

Synthetic builder/store/runner tests must cover explicit offset
parsing, winter/summer conversion, acceptance seconds, minute
boundaries, missing times, same-date versus future-session
availability, post-seal rejection, separate accession items,
issuer conflicts, ambiguous mappings, empty versus unavailable
coverage, replay hiding future filings, manifest/hash pinning,
resume and multiprocessing propagation. Existing input, regular
and extended execution tests, full suite, lint and import
contracts must pass.

The prepared strategy fixtures cover its price/turnover rule,
earliest filing, time delay, no later rescue, prefix replay and
extended next-minute execution. They intentionally do not
simulate a real loader or certify an unavailable input.

## Why owner authorization is needed

The original brief prohibits GPT platform edits and says the
data is already built and must not be rebuilt. Existing owner
exceptions cover extended execution and the minute count field,
not a timestamped filing adapter or a new derived-input build.

AGENTS.md states: “A change to a module you don't own goes to
docs/requests/ as a short note, not as code.” OWNERS.md assigns
the relevant data/core/runner lanes to Claude. This request
seeks an explicit narrow exception, including the separate
derived-input build, before protected code or data is changed.

Owner decision, 2026-11-18: "Authorize scoped timed 8-K input and
derived build." The owner explicitly supplied that answer to the
prepared request in chat. This assigns only the scope above.
