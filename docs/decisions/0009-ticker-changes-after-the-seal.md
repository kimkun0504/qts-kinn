# 0009 — One narrow exception to the seal: ticker-change events

**Status:** taken by claude in Phase 1, 2026-11-15. **Needs the owner's confirmation.**

**Problem.** Sharadar files a company's whole history under its newest ticker. If a company was
renamed after 2023-11-09, the only record of the symbol it traded under *before* the seal is the
rename event, which is dated after the seal. Example: Sharadar's `BNY` is the bank that traded
as `BK` throughout the research window; Massive's pre-seal `BNY` is an unrelated fund.

**Options.**
1. Never read the event. Every company renamed after the seal fails to match its own bars and
   silently leaves the research universe. That selects on the future (a survivorship-style bias).
2. Read only `tickerchangefrom` rows (date, ticker, old symbol), use them only to work out the
   symbol in force before the seal, and let nothing dated on or after the seal out.

**Decision.** Option 2. `kinn.data.sharadar.read_ticker_changes` is the single place that reads
holdout-dated rows. `kinn.data.master.symbol_history` clips every interval at the seal. A test
scans every processed file for dates on or after the seal.

**What leaks.** Nothing a strategy can see. No price, volume, date or flag from after the seal is
stored; a post-seal rename changes only which pre-seal symbol the company is matched to.
