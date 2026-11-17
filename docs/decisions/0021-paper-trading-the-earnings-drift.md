# 0021 — Paper trading the earnings drift, before any live order

**Status:** owner's instruction, 2026-11-16 ("we can build a paper trading path first").

The earnings drift (`strategies/earnings_drift`) passed its holdout run on 2026-11-16. Before
any money moves it is paper traded: a nightly tool the owner runs,
`tools/owner/paper_earnings_drift.py`, keeps a ledger and sends no order.

- **Data, live:** Massive's grouped daily bars (45 sessions, adjusted to the night they are
  fetched), Massive's ticker details for type and market value, and the SEC's submissions
  file for 8-K items. The research used Sharadar for market value and 8-K items; the paper
  ledger is also the first check that the live sources give the same signals.
- **The rule** is the frozen one. `kinn.swing_paper` applies it to the live window; a test
  holds it to the engine's signals, and on research bars of 2016, 2020 and 2022 it found 165
  of the engine's 166.
- **Two books side by side,** 10 positions of $2,000 and 20 of $1,000, and every signal is
  followed whether or not a book has room, so the choice of position count can be made on
  what happens.
- **Added 2026-11-16:** two more books, the same sizes, that take only signals passing the
  quality test (rule A50Q: up over the past 250 sessions, or debt above cash). For each
  signal the tool fetches a year of the stock's daily bars from Massive and the company's
  XBRL facts from the SEC, and records the figures. The test was found after the holdout, so
  these two books are its forward test. A fifth book adds the 20-day-average exit to the
  10-position quality book (`ten_quality_trend`), the variant with the lowest drawdown.
- **Where it writes:** `paper/earnings_drift/` beside the run store (`state.json`,
  `report.md`). Nothing goes to the raw or processed data, and nothing in it is research
  data: it holds the prices of the rule's own trades only. Agents may read it.
- **Not done here:** a broker connection and orders (human-only by AGENTS.md until the owner
  says otherwise), and a screen in the Trader.
