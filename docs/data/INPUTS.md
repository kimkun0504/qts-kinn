# Versioned inputs

An input is a dataset a strategy may read that is not part of the data build. It is built
from raw files into `processed/kinn/inputs/<name>/<input_id>/` and never changes once
written. The id is a hash of the input's code version and the raw files it was built from;
`CURRENT` names the latest. A run that uses an input records its id and version in the
manifest (`inputs`) and its workers read exactly that id, so a run can be repeated after a
newer input is built.

```bash
uv run kinn inputs build form4     # from raw/sec/insiders (read only); prints the id
uv run kinn inputs show form4
```

## `form4`: insider transactions

Source: the SEC's Insider Transactions Data Sets, downloaded by the owner with
`tools/owner/download_insiders.py` (2006 Q1 to 2023 Q3; the next file reaches past the seal).
One row per filing, transaction code and direction, for Forms 4 and 4/A, non-derivative
transactions. Rows filed on or after 2023-11-09 are not written, and the store's date guard
refuses them as well.

| Column | Meaning |
|---|---|
| `accession` | The SEC's accession number of the filing |
| `issuer_cik`, `issuer_name`, `symbol` | The company: its CIK, its name and the trading symbol on the filing |
| `filed` | Filing date |
| `document_type` | `4` or `4/A` (an amendment repeats or corrects an earlier filing) |
| `transaction_code`, `acquired` | The SEC's code (P purchase, S sale, A award, M option exercise, F tax, G gift, ...) and `A` acquired or `D` disposed |
| `shares`, `amount` | Shares, and shares times price in dollars (empty when no price was reported) |
| `purchase_amount` | `amount` for an open-market purchase (code P, acquired); empty otherwise |
| `first_traded`, `last_traded`, `lines` | Transaction dates and how many lines were added up |
| `owner_cik`, `owner_name`, `owners`, `officer`, `director`, `ten_percent_owner`, `title` | The reporting person (the first, when several file together) and their relationship |

**When a strategy may use it.** A filing is available from the first trading session after
its filing date. `DataStore.form4(day, sessions=N)` returns filings dated before `day` and
on or after the Nth session before it, and nothing else; a filing dated on `day` is hidden
until the next session, whatever time it was filed. Asking for a day more than a week past
the input's last filing raises an error, so a run cannot go on with silently empty data.

**In the intraday engine.** A strategy declares the input and reads `view.disclosures`:

```python
class MyStrategy:
    inputs = {"form4": {"sessions": 5}}  # five sessions of filings, newest last

    def signals(self, view, features):
        for symbol, filings in view.disclosures.items():  # tuples of kinn.core.types.Disclosure
            bought = sum(d.purchase_amount or 0 for d in filings)
            ...
```

Disclosures are matched to the session's universe by trading symbol. The same view is given
to the look-ahead replay, and `tests/test_inputs_form4.py` checks that building a newer
input with later filings does not change what a past session saw.

Not included yet: derivative transactions and footnotes.

## `form8k`: 8-K filings by item, with earnings marked

Source: Sharadar's EVENTS table, which is already part of the data build, so there is nothing
to build or download: `kinn inputs show form8k` prints what the current build holds (2.2
million company-days with a filing, 1993-11-08 to the seal). Its id is a hash of the code
version (`form8k-1`) and the data build's id; a run is pinned to its build, so it is pinned
to this input as well.

One record per company and filing date, `kinn.core.types.CurrentReport`:

| Field | Meaning |
|---|---|
| `symbol`, `permaticker` | The company, under the symbol it trades with that session |
| `filed` | Filing date |
| `codes` | Sharadar's event codes for that date, as integers: `(22, 91)` |
| `items` | The 8-K items among them: code XY is item X.0Y, so `("2.02", "9.01")` |
| `earnings` | True when item 2.02 (results of operations and financial condition) is among them |

Codes that are not items of Form 8-K (34, 35, 37 and 40 occur in this data) are Sharadar's
own additions. They stay in `codes` and are left out of `items`; read Sharadar's EVENTS
documentation before using them.

**When a strategy may use it.** The same rule as `form4`: a filing is available from the
first trading session after its filing date. `DataStore.form8k(day, sessions=N)` returns
filings dated before `day` and on or after the Nth session before it. The table has dates
and no times of day, so a release filed before the open of `day` is hidden until the next
session, and the session it moved the price is seen only in that session's bars. Earnings
released after the close and filed the same evening are visible the next morning.

**In the intraday engine.**

```python
class MyStrategy:
    inputs = {"form8k": {"sessions": 1}}  # what became usable this morning

    def signals(self, view, features):
        for symbol, reports in view.reports.items():  # tuples of CurrentReport, oldest first
            if any(r.earnings for r in reports):
                ...
```

A strategy may declare both inputs. The run's manifest records
`inputs.form8k = {input_id, version, last_filed, rows}`, and the id is part of the config
hash. `tests/test_inputs_form8k.py` checks the next-session rule, the typing, the seal, the
manifest, and that a filing is hidden when its own day is replayed.

**What it is not.** It says a company reported, not whether the report was good. There are
no analyst estimates on disk (Sharadar's fundamentals are as reported, dated by the 10-Q or
10-K, which often arrives days after the earnings 8-K), so an earnings beat cannot be
measured against a consensus. The price move on the day of the report is the nearest
measure available: `strategies/earnings_drift` uses a two-day jump of 15% on five times
normal volume.

## `form8k_timed`: original SEC 8-K accessions with acceptance time

This separate owner-authorized input reads the existing
`raw/sec/filing_times/8k.jsonl.gz` and identity fields from the
Sharadar snapshot of the pinned build. Build only its new derived
dataset with `kinn inputs build form8k_timed`; no bar/panel rebuild
or download is involved. `kinn inputs show form8k_timed` gives the
id, code version, observed archive coverage and rejections.

Declare `inputs = {"form8k_timed": {"sessions": 1}}`.
Here one session means acceptance on the current New York date,
rather than the date-only form8k input's prior-day rule. Only this
one-session contract is supported. `view.timed_reports[symbol]`
contains immutable `TimedReport(symbol, permaticker, accession,
form, filed, accepted, items, earnings, usable_minute)` values,
oldest acceptance first with accession tie-breaks.

Acceptance requires an explicit timezone, is stored as aware UTC,
and is converted through America/New_York. Missing/naive/invalid
times are rejected. A filing accepted during minute m becomes
usable at completed-bar label m+1; its earliest signal can act
at the opening minute m+2. `DayView.upto(cut)` hides filings with
usable_minute > cut alongside later price bars. The filing's items
are never combined with a later accession. Original 8-K only;
amendments and stake filings are outside this adapter.

The input joins issuer CIK to an unambiguous permaticker within
the pinned pre-seal build, then uses the session's trading symbol.
Missing and conflicting identities are excluded, including
accessions appearing with conflicting issuer/time/item records.
Exact duplicates collapse. The derived table retains issuer CIK
for provenance. Static SEC-link mapping remains a snapshot-based
identity limitation and is not a solution for stake-subject roles.

Each immutable id fingerprints parser version, source contents,
identity snapshot and master content, and data build id. Runs,
resume, sweeps and worker processes pin that id. A sweep refuses
different pinned input sets. The run manifest records input
version, build, rows and observed source coverage.

Both filed and local acceptance dates must precede 2023-11-09.
Requested dates pass the seal even if a DataStore otherwise has
unsealed access: this input adds no unseal path. Reading outside
the observed valid source archive envelope fails explicitly.
An envelope is not a completeness guarantee for every issuer.
Rejection and identity counts are preserved in input metadata.

SEC acceptance establishes public-by timing for the filing, not
the first release of a press announcement. No analyst consensus,
text sentiment, trading halt status, quoted depth or execution
latency is supplied by this input.


## `nbbo_replenishment`: two pre-decision quote snapshots

This owner-authorized input is specific to the frozen
`bid_replenishment_reversal` price population. It is a signal input,
not a quote fill model. The owner alone downloads the planned raw
windows with the existing owner helper. GPT never invokes that helper,
reads keys or writes raw files.

After acquisition, build only the separate index:

```sh
KINN_AGENT=gpt UV_NO_ENV_FILE=1 uv run --no-env-file --locked kinn inputs build nbbo_replenishment --plan <processed-quotes_sample-plan-directory>
```

`kinn inputs show nbbo_replenishment` gives its immutable id, source
hashes and valid-pair coverage overall, in 2013–2016, in 2022–2023 and
by year. Missing files refuse the entire build before publication.
Empty, stale, conflicting or invalid observations preserve the parent
with an explicit status. Coverage denominators include all parents.
The builder does not apply the strategy's size-ratio/spread signal.

The development plan must match every first event of the finished,
clean, registered price-control study, including identity, decision
minute and pre-open fields. Source manifest/events and windows hashes
are checked. Only saved candidate feature columns are read, never
forward returns or future entry prices. The downloader's `entry_price`
compatibility field contains prior close. Its value is not a fill.
Dates, windows, schema, target offsets and current data build must match.
Unknown parent identity or changed first-event time fails explicitly.

Declare `inputs = {"nbbo_replenishment": {"sessions": 1}}`.
This means the current session only. `view.book_pairs[symbol]` holds
immutable `BookPair(day, symbol, permaticker, minute, status, early,
late)` values. Available early/late fields are immutable
`QuoteSnapshot(sip_timestamp, bid_price, ask_price, bid_size, ask_size)`.
Unavailable snapshots are None. `DayView.upto(cut)` hides pairs whose
signal minute exceeds cut. The native loader requires the indexed
company and traded symbol to match the session universe. All ordinary
peers remain in that universe regardless of their quote eligibility.

If T is the completed signal bar's end, targets are T−5 seconds and
T−1 nanosecond. Latest SIP timestamp at or before each target is
selected **before** validity checks. An invalid latest quote never
revives an older quote. Identical feature duplicates collapse;
conflicting latest-timestamp feature ties are unavailable. Age must
be at most one second relative to its target, bid/ask finite and
positive, ask strictly above bid, and displayed sizes positive integers.
Sizes retain common vendor units; no absolute share depth is inferred.
Post-decision quote fields are not inspected for feature selection or
exposed, including the two post-decision raw seconds reserved for a
future separately registered execution audit.

The immutable index fingerprints parser version `nbbo-replenishment-1`,
source plan/control/candidate content, original strategy commit, build
and raw quote contents. A second source hash pass prevents publication
from files changed during parsing. The derived file also has a content
hash checked when opened. Each run records source, coverage and index
id; configuration hashes, resume, sweeps and spawned workers pin it.
New runs require strategy source identical to the registered control's
source. Workers also verify the strategy hash recorded at run creation.
Changing CURRENT cannot change a paused run. A period outside the
indexed candidate source range fails; absence of an index is never
observed absence of an event. This input has no unseal path.

Only after development qualifies, a future acquisition plan can use:

```sh
KINN_AGENT=gpt UV_NO_ENV_FILE=1 uv run --no-env-file --locked kinn inputs plan nbbo_replenishment --reference-run <original-development-control-id> --start <first-session> --end <last-session> --plan <new-processed-quotes_sample-directory>
```

The high-level runner checks clean/frozen source, enumerates identical
price-only triggers and replays their prefixes. It writes only candidate
features and acquisition windows, without calling the simulator or
forward study measurements. It does not create a performance result;
the preregistered validation still gets one performance run. The data
layer imports neither strategies nor research. No real validation plan
was generated during adapter implementation.

Synthetic native tests cover source/hash and all-parent checks, exact
nanosecond/DST boundaries, invalid latest quotes, ties, staleness,
empty versus missing files, post-decision perturbation, seal and window
rejection, identity conflicts, native replay with an intentional canary,
immutable plans, and index/strategy pinning through resume and workers.
These establish software contracts, not quote completeness, execution
latency or live profitability. Minute-bar execution and costs are unchanged.
