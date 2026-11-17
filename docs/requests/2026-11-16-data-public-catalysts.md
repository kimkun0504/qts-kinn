# Point-in-time public catalysts for intraday research

Request for the Kinn data, intraday engine, features and manifest owners.
This is a read-only inventory and a proposed data interface. No alpha
returns were measured and no additional trial was registered.

## What is usable

| Input | Local and vendor coverage | Intraday research use |
|---|---|---|
| Prices and executions | The existing Massive SIP bars build is in use. Stocks Advanced documents historical stock trades and NBBO. The raw folder contains targeted quote samples. | Use the existing bars for candidate generation. Query targeted trades and quotes for timing, spread and size at the touch. Exact limit queue priority needs data beyond NBBO. |
| Public insider disclosures | `raw/sec/insiders` has complete quarterly SEC Form 3, 4 and 5 archives from 2006 Q1 to 2023 Q3. The submission header contains `FILING_DATE`, issuer CIK and accession. The transaction table carries purchase and disposal information, shares, price and footnote IDs. | Start from the SEC archives already downloaded. Use the first eligible session after the public filing date for date-only signals. Get original filing acceptance and dissemination timestamps for any same-session test. |
| Earnings and guidance | Kinn has Sharadar date-level 8-K item codes in its data store. The intraday session exposes a filing count. An earnings item identifies a disclosure and has no surprise sign. Massive documents structured Benzinga earnings and corporate guidance as separate expansions. I did not find Benzinga monthly downloads in the checked pre-seal location. | Build an earnings-event label from item 2.02 for a first release-tagged price test. A signed surprise needs as-released values and the last comparable consensus known before release. Massive's standard SEC-derived financial statements can contain repeated or restated figures. |
| General ticker news | `raw/massive/news` has complete monthly partitions through October 2023. The sampled schema includes publisher, headline, article ID and publication time. Massive describes materially denser coverage from 2021 and an hourly delivery process. | Use a conservative lag or a following-session design with a documented availability model. A publication timestamp is not the first time the vendor served the item. The vendor's sentiment series starts outside the research window. |
| Short positioning | The Massive short-interest archive contains settlement date and days-to-cover fields. The checked pre-seal short-volume partitions contain no rows. | Short interest can be a pre-open selector after the applicable publication lag. Neither field establishes borrow availability. |
| Reference and company data | Stocks Advanced documents financials and ratios, reference tickers, corporate actions and SEC filing endpoints. Kinn already has split-aware prices and other prior-panel fields. Massive's historical ticker listings use today's maintained records, and its free-float endpoint provides current data. | Use the existing point-in-time symbol history and as-filed disclosures. Avoid backfilling current free float, current ownership, the latest financial statement or a later restatement into older sessions. |

[Massive stock data catalog](https://massive.com/docs/rest/stocks/overview)
· [Stock history and NBBO](https://massive.com/knowledge-base/article/how-much-historical-stock-data-does-massive-have)
· [NBBO depth coverage](https://massive.com/knowledge-base/article/does-massive-offer-level-2-data)
· [SEC Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets)
· [Massive Form 4](https://massive.com/docs/rest/stocks/filings/form-4)
· [Benzinga earnings](https://massive.com/docs/rest/partners/benzinga/earnings)
· [Benzinga expansions](https://massive.com/docs/rest/partners/overview)
· [Massive ticker news timing](https://massive.com/knowledge-base/article/how-far-back-does-massives-news-and-sentiment-data-go)
· [Massive financial-statement vintages](https://massive.com/knowledge-base/article/does-massive-provide-the-filing-date-for-any-financial-reports)
· [Reference-data restrictions](https://massive.com/knowledge-base/categories/reference-data)

## First implementation

1. Add a versioned derived catalyst input. Start with original Form 4
   non-derivative acquisitions and typed 8-K earnings events, for which
   data exists locally. Retain source identifier, accession, original
   filing date, public timestamp if verified, issuer identity, availability
   time and amendment status. Resolve issuer and security on the event date.
   Separate transaction date from publication. SEC code P includes private
   purchases. Use transaction coding and footnotes before describing a
   purchase as open-market. Deduplicate accession-linked transactions
   without dropping legitimate purchases by different reporting owners.
   [SEC transaction codes](https://www.sec.gov/edgar/searchedgar/ownershipformcodes.html)
   · [EDGAR public dissemination](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
2. Expose an as-of slice in the standard session view. The first version
   can expose only disclosures carried forward from completed prior dates.
   Preserve the existing filing-count interface. Store the catalyst
   data version and availability rule in the run manifest. Keep the raw
   files read-only, enforce the cutoff on import and query, and make a
   missing date distinguishable from an observed date with zero events.
   Test late publication, weekends, early closes, amendments, duplicated
   accession joins, ticker reuse and future events hidden on prefix replay.
3. Add the existing Massive headline archive once the as-of contract
   exists. Use the earlier news-input proposal's distinction between
   publication time and actual receipt. Avoid a new date split based on
   what returned best. The news archive's early coverage is too sparse
   for a standard development test using that source alone.

## What to test first

Freeze a next-session intraday test of a publicly disclosed insider
purchase. The stock must show a positive opening price reaction on
substantial observed turnover. Buy only after that price confirmation
and exit before or at the same session's close. Use the existing Kinn
cost and risk rules. The prediction is follow-through after public
disclosure. Prior insider and earnings swing work is related research.
A multi-day result cannot establish this intraday effect. Thresholds,
chooser, periods and sample bars belong in a committed hypothesis
before the first `kinn run`.

Reuse the local filing data first. The SEC quarter archive ends in
September 2023. A date-filtered official Form 4 extract for October 1
through November 8, 2023 would complete the pre-seal window; the entire
next quarterly ZIP extends across the seal. If the account already
includes structured Benzinga earnings, a bounded export with timestamps,
reported values, consensus and revision metadata would enable the signed
earnings follow-up. An independent sample of releases can first verify
timing and revisions. Existing Massive quote plans can check execution
without a new subscription.

The requested adapter belongs to the platform lanes. Strategy code can
use it when the owner has assigned or shipped the integration. The
sealed holdout remains excluded.
