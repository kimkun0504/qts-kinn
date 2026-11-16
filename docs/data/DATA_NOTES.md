# Data notes

What the raw data is, what Kinn does to it, and what to distrust. Numbers are from build
`07b6a77a41`; the generated audit is [AUDIT.md](AUDIT.md) (`kinn data audit`).

## Raw data (read-only, `KINN_RAW_DIR`)

### Massive (formerly Polygon.io), `us_stocks_sip` flat files

| | |
|---|---|
| Files | one `YYYY-MM-DD.csv.gz` per session, daily and 1-minute, 5,077 sessions each |
| Range used | 2003-09-10 to 2023-11-08 (later files are the holdout, kept elsewhere) |
| Columns | `ticker, volume, open, close, high, low, window_start, transactions` |
| Timestamp | `window_start`: nanoseconds since the Unix epoch, UTC, the **start** of the bar. The 09:30 New York bar covers 09:30:00–09:30:59 and is known at 09:31:00 |
| Timezone | UTC in the file; Kinn adds `minute_et` (minutes after midnight, New York), daylight saving handled |
| Adjustment | **None.** Prices and volumes are as traded (AAPL closes 499.23 then 129.04 across its 2020 split) |
| Extended hours | Included: bars from 04:00 to 19:59 New York (see the audit for the early years) |
| Quotes | **Not included.** Trades aggregated to bars only. No bid, ask or spread anywhere |
| Halts | No halt flags. A minute with no trade has no bar |
| Coverage | Exchange-listed securities (SIP): stocks, ETFs, funds, preferreds, warrants, units. No OTC |
| Symbols | The symbol in force on the day. Preferreds `ABCpA`, classes and warrants `ABC.B`, `ABC.WS` |

Daily bar semantics, checked against the minute bars: `open` and `close` are the regular
session's (the close is the official close, which can differ from the last minute bar by a
cent); `high` and `low` are regular-session; `volume` is larger than the sum of minute bars
(it includes prints the minute bars leave out).

### Sharadar Core US Equities Bundle, snapshot 2026-11-09 (zipped CSV)

| Table | Used for | Kept columns |
|---|---|---|
| TICKERS (SEP rows) | company identity, category, exchange, first and last price dates | see below |
| ACTIONS | ticker changes, splits, delistings | all |
| DAILY | market capitalisation per day | `ticker, date, marketcap` |
| SEP | cross-check of Massive closes | `ticker, date, closeunadj` |
| EVENTS | 8-K event codes by filing date (a "news" proxy) | all |
| SF1, SF2, SF3*, SFP, METRICS, SP500, INDICATORS | **not ingested yet** (no current use) | |

Sharadar identifies a company by `permaticker`, files its whole history under its newest ticker,
and renames delisted tickers that were later reused with a digit suffix (`FB1`).

## What the snapshot knows about the future, and what Kinn does about it

The Sharadar files were exported in 2026, so some fields describe the future as seen from any
research date. Each is handled at ingestion (`kinn.data.sharadar`):

| Field | Problem | Handling |
|---|---|---|
| Rows dated on or after 2023-11-09 | holdout | dropped while streaming; never written |
| `lastpricedate`, `isdelisted` | reveal delistings after the seal | last price date on or after the seal becomes null; `delisted` is recomputed |
| Companies first priced after the seal | did not exist yet | dropped |
| `scalemarketcap`, `scalerevenue`, `relatedtickers`, `lastupdated` | current-day facts | never read |
| SEP `close`, `closeadj`, `volume` | adjusted for splits and dividends through 2026 | never read; only `closeunadj` |
| Newest ticker as the key | hides the symbol traded at the time | `symbol_history` rebuilds it from ticker-change events (decision 0009) |
| `category`, `exchange`, sector labels | as of the snapshot, not of the date | **kept as is. Known weakness:** a company's category is its latest one |

## Processed data (`KINN_DATA_DIR`)

```
bars/<bars_id>/minute/year=YYYY/YYYY-MM-DD.parquet   symbol, bar_start (UTC), minute_et, OHLC, volume, transactions
bars/<bars_id>/daily/year=YYYY.parquet               date, symbol, OHLC, volume, transactions
bars/<bars_id>/calendar/year=YYYY.parquet            one row per session, with the closing minute
builds/<build_id>/master/                            security_master, symbol_history, splits
builds/<build_id>/panel/year=YYYY.parquet            the daily panel (below)
builds/<build_id>/sharadar/                          the ingested Sharadar tables
builds/<build_id>/build.json, audit.md, audit.json
builds/CURRENT                                       the build readers use
```

`bars_id` is a hash of the raw Massive file list and sizes; `build_id` adds the Sharadar
snapshot, the data-code version and the holdout date. Every run records `build_id`.
Code reads data only through `kinn.data.store.DataStore`, which applies the seal.

### The daily panel and point-in-time universes

One row per company per session. Columns known **before the open** of `date`: `prev_close`
(split-adjusted to today's share basis), `adv20_prev` (median dollar volume of the last 20
sessions), `marketcap_prev` (Sharadar market cap of the previous session), `ret60_prev` (from
build data-6: the price return over the 60 sessions ending at the previous close, split-adjusted,
dividends not added back; empty until a company has 60 sessions), `sessions_prior`,
`category`. A `Universe` may filter on these only (a test enforces it). The same-day columns
(`open` … `dollar_volume`) are outcomes.

## Findings from the audit

1. **Identity matching is sound; the unmatched days are OTC.** 85–94% of Sharadar common-stock
   company-days find a Massive bar, by year. Of the 2.48 million that do not, 99.95% have no
   Massive bar for that symbol on that day at all: Sharadar keeps pricing companies after they
   leave the exchange for OTC (FNMA, bankrupt "Q" tickers, sub-dollar names), and Massive's SIP
   feed has listed securities only. 1,252 days were dropped as ambiguous (two companies
   claiming one symbol; 10 such pairs). For Kinn this is the right universe: listed names only.
2. **Where both vendors have a price they agree.** Unadjusted closes are within 1% on
   98.2% of matched days in 2003, rising to 99.9%+ from 2018.
3. **Massive symbols without a company** are funds and ETFs (6,131 symbols known to Sharadar's
   fund table), other funds and test symbols (5,739, e.g. `ZVZZT`), preferreds, warrants and
   units. ETFs are readable by symbol through `DataStore.daily` / `minute`.
4. **Splits are applied correctly** on the checks (AAPL 2014 and 2020, GOOGL and TSLA 2022).
   Among 22.7 million common-stock days without a split on record, 8,372 have an overnight
   move above 40%: real gaps plus any splits Sharadar lacks. Not yet separated.
5. **Market cap is missing for 1–2% of common-stock days** (5–6% in 2021–2022, the SPAC years).
   A universe with a market-cap bound excludes those days.

## Open issues and things not verified

- **No quotes.** The cost model cannot measure spreads from this data (Phase 2 uses a stated
  conservative fallback). A quote sample is needed before trusting any limit-order result.
- **No halt data.** "No fills during halts" is implemented as "no bar, no fill"; a halt and a
  quiet minute look the same.
- **Sharadar's `marketcap` is assumed point in time** (price times the then-latest share count).
  Not verified against filings.
- **`category` is the latest label**, see above.
- **Daily `adv20_prev` uses the full-day volume**, which includes extended hours and auctions.
- Sharadar tables with fundamentals, insiders and institutions are not ingested.

## Daily research data (build `data-5`, 2026-11-15)

Found while testing the daily engine on a known signal. All fixed in the build; the panel used by
intraday strategies changed too (`prev_close` and `split_ratio` on the affected days).

| Problem at the source | Size | What Kinn does |
|---|---|---|
| Dividend and spinoff amounts are on today's share basis | every company with a later split | Restored to the day's basis with `unadjust` (decision 0015). `master/dividends.parquet` |
| Spinoffs were ignored, so a breakup looked like a crash | 489 `spinoffdividend` rows | The cash value of spun-off shares counts as a payout on its date |
| A split dated by its record or pay date, days from the price change | 142 of 3,686 checkable splits | Moved to the session whose price change matches the ratio (`master/splits_effective.parquet`) |
| A listed split with no matching price change within 20 days | 744 | Dropped. Mostly ADR ratio changes and pre-listing splits that never showed in traded prices |
| A hole in a company's bars (a halt, or a ticker change dated wrongly, e.g. Willis in 2015) | 165 company-days above $2 billion | For daily research: no return that day and not in any universe (`MAX_GAP_DAYS`) |
| A payout above 25% of the price with no matching price drop | 2 in the largest 1,000 names over 20 years | Cut to the size of the drop (`limit_suspect_distributions`) |

After these, of 5.0 million company-days in the largest 1,000 names, 361 have a one-day total
return beyond ±40%, and those checked are real (buyouts, trial results, March 2020, GameStop).

Not fixed: 1,474 small splits (under 18%) cannot be checked against daily noise and keep their
listed date; ticker-change dates are not checked against the symbols in the bars; 3,969 listed
splits have no bars nearby (before 2003-09 or never in the SIP data).

**Fundamentals (SF1).** Only the as-reported dimensions (ARQ, ART) are kept, dated by `datekey`,
the day the filing reached the SEC. A value is usable from the session after that day. The
restated dimensions and the price-based columns are not read.

## Build `447e58e098` (data-6, 2026-11-15)

Adds `ret60_prev` to the panel. Every other panel column, the security master, the split and
dividend tables and the Sharadar tables are identical to build `6453bd3ec8`, row for row (26.4
million panel rows compared), so runs on the two builds are comparable. `builds/CURRENT` points
to the new build; runs by any agent started after 2026-11-15 21:20 ET record it.
