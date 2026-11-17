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
