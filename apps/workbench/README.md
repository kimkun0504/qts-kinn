# Workbench

The research UI. It reads the run store (`KINN_RUNS_DIR`) through the run schemas and never
imports strategy code. The one thing it starts is a Lab run: the owner's own algorithm, run in a
worker process of its own (decision 0023, [docs/LAB.md](../../docs/LAB.md)).

```bash
cd apps/workbench/web && npm install && npm run build   # once, and after UI changes
uv run python -m apps.workbench                         # http://127.0.0.1:8321
```

For UI work, run `npm run dev` in `web/` beside the Python server; Vite proxies `/api` to it.

| Page | Shows |
|---|---|
| Home | what passed its holdout with its profit curve, what is being tested forward, what waits on the owner, tonight's paper orders, the leads on paper, the latest Lab runs, and the first ideas tested with their verdicts (all of them on request) |
| Strategies | every idea with its verdict; each opens a strategy page |
| A strategy | Results (profit across its periods, the holdout marked, years, months, costs, weaknesses, the evidence in order), Trades, Paper book, Report (REPORT.md and HYPOTHESIS.md), Studies, Runs |
| Markets | index, sector, bond, commodity, foreign and volatility funds on the last session with their day, week, month, three months, year to date, year and three years; any four of them charted together over a month to three years; how they moved together over the last year (correlation of daily changes); and how many US stocks rose and fell each day, with the running total |
| Stocks | a watchlist with each stock's last session (day, month, year, distance from the high, market value, P/E), the largest rises and falls among US stocks above $2B that day, and each sector's median month; any company by ticker, old ticker or name: daily prices to the seal (split-adjusted, line or candles, volume, log scale, drag to zoom, 50- and 200-day averages), its 8-K days, its change beside SPY, QQQ, IWM or other stocks over the chart's range, and, in tabs, its financials by quarter and trailing year (as filed before the seal, any line charted), how it moved on each results 8-K and the 20 sessions after (beside SPY), its industry's largest companies side by side with the industry's medians, its beta to SPY, volatility, deepest falls and average month, every trade a strategy run, a Lab run or a paper ledger made in it (marked on the chart), its insiders' open-market purchases and sales from Form 4, and its 8-K filings |
| Screener | every stock that traded on a session from September 2003 up to the seal, filtered by kind, sector, industry, exchange and any range of market value, dollar volume, price, returns (1, 3, 6 and 12 months), distance from the 52-week high, volatility, P/E, P/S, P/B, free cash flow yield, revenue, revenue growth and net income; ready starting points, screens saved by name, the screen in the address, CSV, a breakdown by sector, picked stocks added to the watchlist or charted together, and, for a past day, what came next: each stock's change over the next month to year (up to the seal) and the medians of the stocks that pass against every stock and SPY. Valuations use only filings made before the session |
| Studies | every search and test, including those done by research scripts, with its trial count and verdict; a search box, outcome filters and ordering |
| Paper trading | every paper ledger: the earnings drift's books (tonight's orders, positions, the books side by side) and the big prints and after-hours short ledgers (signals, results, the alternative exit, the benchmark or borrow, the evenings read) |
| Runs | every run with a search box, filters (kind, period, strategy) and sortable columns; the selected run (in the address, `#/runs/<run id>`) with its tearsheet, event study, tick study or book |
| Compare | up to four backtests overlaid, with a side-by-side table, picked on the page or in the runs table; the choice is kept and in the address (`#/compare/<id>,<id>`) |
| Parameters | a map of any result across one or two settings that differ between runs |
| Trials | every family in a sortable table (trials charged, counted runs, best and deflated Sharpe, probability of backtest overfitting), one family's detail at a time, and the Lab algorithms' trial counts |
| Lab | the owner's algorithms in an editor; Run tests one over every stock in the universe and shows the book (beside SPY at the book's own exposure), the path after the signal, the best and worst stocks, months, every trade, the years, the lookahead check, the trial count, and any two runs compared |
| Guide | this README and the Lab's guide (`docs/LAB.md`) with their sections beside them, and the keyboard shortcuts |
| Data | what the research data holds: the build, its tables with rows and size, price bars by year, the versioned inputs, companies by kind and sector, every build kept, and the seal |

Search everything (pages, stocks, the watchlist, screens, strategies, paper ledgers, Lab
algorithms, runs) with the box
in the top bar, Cmd+K or `/`. `?` lists the keyboard shortcuts; G then a letter jumps to a page
(G S stocks, G F screener, G L Lab, G R runs). A Lab run going shows in the top bar from any
page, and a note appears when it ends. A page that fails shows its error in place of the page.

## Where the record comes from

The run store knows runs. It does not know which idea passed, what a research script found, or
what is waiting on the owner. That is written by hand in a `record:` block in each
`strategies/<name>/strategy.yaml` (decision 0022, and `docs/NEW_STRATEGY.md` for the fields).
`record.py` joins those blocks to the run store and to the paper ledger. The numbers on a
strategy page come from the runs the record names (`periods`), never from the text.

A strategy with no `record:` block still appears, under its owner, with its runs. Update the
block in the same commit as the REPORT.md verdict it summarises.

## The Lab

The Lab page edits Python files in the Lab folder (`KINN_LAB_DIR`, or `lab/` beside the run
store) and runs them. How to write an algorithm, what data it gets and how the results are
worked out: [docs/LAB.md](../../docs/LAB.md).

- Run saves the code, writes `lab/runs/<run_id>/` and starts `python -m kinn.lab.worker` in its
  own process. The server never imports or runs the owner's code. One run at a time.
- The page polls the run's status, then reads its results files.
- As the owner types, the page sends the code to `/api/lab/check`, which reads it with `ast`
  (`kinn.lab.check`) and never runs it; errors block Run, and the server refuses them too.
- Helper modules live in `lab/library/` (`/api/lab/library`); a run copies them into its folder.
- Changes (save, delete, run, cancel) need the session token the page reads from
  `/api/lab/session`, and come only from the Workbench's own page: the server checks the Host
  and Origin headers and the token. The Lab is off when the server listens beyond this machine
  (`--host 0.0.0.0`).
- `lab.py` holds the endpoints as plain functions; `__main__.py` does the checks and routing.

## How it is built

- `api.py`, `record.py`, `lab.py`, `ledgers.py`, `stocks.py`, `markets.py`, `screener.py`,
  `catalog.py`, `__main__.py`: a small standard-library server (large answers are sent
  gzipped). `api.py` reads runs; `record.py` reads the records, the documents and the earnings
  drift's paper ledger; `ledgers.py` reads the event ledgers (big prints, the after-hours
  short) into one shape (`paper-ledger-1`); `stocks.py` is the stock page and search (prices
  through the sealed `DataStore`, trades from the run store, the Lab and the ledgers);
  `markets.py` is the Markets page (fund bars as traded, split-sized jumps taken out, and the
  daily breadth); `screener.py` is the screener (one session's cross-section through the
  sealed `DataStore`, and what came after it up to the seal, cached per build and session);
  `catalog.py` is the Data page (file metadata and the sealed calendar only); `lab.py` is the
  Lab. Restart the server after changing any of them.
- `web/`: React, TypeScript, Tailwind and Vite (decision 0013).
  - `src/index.css`: the design tokens. Light is the default theme; dark is
    `data-theme="dark"`. Components use the token names, never raw colour values. The chart
    colours (`--series-1`, `--gain`, `--loss`) were checked for colour-blind separation in
    both themes; check any replacement the same way.
  - `src/components/ui/`: the building blocks (Card, Stat, Panel, StatStrip, DataTable, Badge,
    VerdictBadge, Button, Segmented, EmptyState). **Styling lives in these components.** Pages
    compose them and add layout only.
  - `src/components/charts/`: ProfitChart, YearBars, MonthGrid, LineChart and Histogram, drawn
    as SVG.
  - `src/components/CodeEditor.tsx`: the Lab's Python editor (CodeMirror 6, coloured from the
    tokens). It loads with the Lab page only, in a chunk of its own.
  - `src/components/layout/AppShell.tsx`: the side rail and top bar.
  - `src/pages/`: one file per page. `src/lib/route.ts` maps the address (`#/strategy/<name>`)
    to a page, so pages can be linked and the back button works.
  - `src/lib/`: API types, number formatting, data hooks.
