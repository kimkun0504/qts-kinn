# SEC stake records: identity and future-dependent exclusions

## Owner review requested

Before exposing the downloaded stake filings to intraday strategies,
resolve company role and remove the future-dependent exclusion in
the existing research script. This is a code review finding, not
a new backtest or an estimate of its financial impact. No data
was queried to produce it, and another agent's code was not edited.

Reviewed source: Claude branch `agent/claude/intraday-entry`,
commit `c173694765fad62ef0315915381ba6001e6cfba5`:

- `research/claude/stake_filings.py`, `table()`
- `research/claude/sec_times.py`, `numbers()` and `filings()`
- `tools/owner/download_edgar_times.py`, `rows()` and `extract()`
- `strategies/stake_filings/HYPOTHESIS.md` and `REPORT.md`

## Verified temporal dependency

The table builder first scans the entire downloaded history, counts
initial SC 13D records by CIK and calendar year, then constructs:

```python
busy = {cik for (cik, _), n in a_year.items() if n > MAX_A_YEAR}
found = {(p, session, form) for cik, session, form in rows if cik not in busy for p in stocks[cik]}
```

Membership in `busy` discards the year key. A high count in ANY
later calendar year excludes that CIK's events in EVERY earlier
year. Even retaining the year key would use filings after a
historical decision within that calendar year. Appending future
filings can therefore change the historical eligible event set.
That violates prefix invariance.

A synthetic counterexample is sufficient to demonstrate the
dependency: a historical qualifying row is retained when it is
the only record; append a later year's records exceeding the
fixed annual threshold, and the earlier row disappears. This
says nothing about the size or direction of any return bias.

Required fix before relying on it: avoid a frequency exclusion
or define it entirely on information preceding the event,
then test that appending future filings cannot alter historical
events. Re-evaluate any affected claims with honest provenance;
do not relabel the original output as a corrected result.

## Verified schema gap; identity risk

The download writes only CIK, accession, form, filed, accepted
and items. It obtains CIK from the submissions archive member,
without a field distinguishing filer from subject. The research
maps that CIK to the company's permaticker.

The stake hypothesis itself acknowledges that a company's list
may include filings it submitted about other companies. Removing
financial companies or frequent filers does not prove that every
remaining record concerns the selected stock. It also cannot
identify the holder, activist status or position size.

Before a strategy calls this an issuer-level stake signal, it
needs a verified subject-company identifier and role provenance,
mapped through point-in-time company/symbol identity. Existing
fields alone do not establish that relationship. Do not use a
full-future frequency screen as a substitute for missing identity.

## Scope and next action

This note does not request a new raw download or authorize a
platform change. The current GPT trading-gap candidate uses none
of these records and has been parked after its own logged study.
No SEC script was executed, no raw file was written or downloaded,
and no sealed folder or post-seal market data was accessed for
this review.

A timestamped 8-K input would be a separate proposal: acceptance
time can establish public-by availability, not the first release
of a press announcement. A stake input additionally requires the
identity resolution above. Both would need scoped owner approval
for the platform/input lanes and any new derived-input build.
