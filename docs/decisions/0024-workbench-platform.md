# 0024 — The Workbench as a research platform: stocks, every ledger, data, search

**Status:** owner's instruction, 2026-11-19 ("it still falls short of becoming a truly
professional research platform in terms of functionality … keep fixing it through the night
until it feels like a proper company-made platform").

**Context.** The Workbench showed strategies, studies, runs and the Lab. It could not show a
single company, it showed one of the three paper ledgers the owner runs each day, the Lab's
results stopped at a profit line beside SPY fully invested, nothing could be found without
knowing where it was, and nothing said what the data holds.

**Decision.**

1. **A stock page** (`#/stock/<ticker>[/<permaticker or date>]`, `apps/workbench/stocks.py`).
   - Prices are read through the sealed `DataStore` (`panel_of`, and the new `events_of` and
     `symbol_history`), so they end the session before the holdout start. Nothing post-seal is
     drawn; trades after the seal (the paper ledgers) are listed without a chart point.
   - Prices are split-adjusted back from the last close, for a chart only: the factor uses
     later rows, which is right for looking and wrong for a signal. The Lab and the engine keep
     their own forward-only adjustment.
   - A ticker can belong to several companies over time. Without a hint the current holder is
     shown, then the most recent; `?on=<date>` picks the company that held it that day (what a
     Lab trade links to), `?pt=<permaticker>` picks one exactly.
   - Every trade in the company is listed and marked: strategy runs (by permaticker, abandoned
     runs left out, net divided by the trade's own money), Lab runs (by the ticker held on the
     trade date), and the paper ledgers (by symbol).
2. **Every paper ledger** on the Paper page, the big prints and after-hours ledgers read from the
   owner tools' state files into one shape (`paper-ledger-1`, `apps/workbench/ledgers.py`), never
   written. Home lists them; their strategy pages get a Paper book tab.
3. **Lab results a researcher can act on.** Each run writes `path.json` (the average move from
   the signal day's close, 20 sessions before to past the exit, against the universe, with a 95%
   band; at most 20,000 trades sampled with a fixed seed) and `spy_matched` in `equity.json`
   (SPY on the money the book actually had invested each day). The page adds drawdown and
   positions views, profit by month, and a comparison of any two runs (metrics, settings that
   differ, both curves, a diff of the code). Runs from before this change show neither.
4. **A Data page** (`apps/workbench/catalog.py`): the build, its tables (row counts from Parquet
   metadata), bars by year, the versioned inputs, companies by kind and sector, every build, and
   the seal with the number of owner reads in the unseal log (not the token fingerprint).
5. **One search** (Cmd+K, `/`, or the top bar) over pages, strategies, ledgers, Lab
   algorithms, runs and stocks; runs have their own address (`#/runs/<run id>`).

**Consequences.** The server gains `/api/stock/<symbol>`, `/api/stocks?q=`, `/api/ledgers`,
`/api/ledgers/<name>`, `/api/data` and the Lab's `path` part; it needs a restart to serve them,
and the page shows a plain message until it has one. The stock page costs about a second (a
scan of the panel's permaticker column); the catalog is worked out once per build.
