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

Not included yet: derivative transactions, footnotes, and typed 8-K earnings events.
