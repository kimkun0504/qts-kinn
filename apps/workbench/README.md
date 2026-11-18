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
| Home | what passed its holdout with its profit curve, what is being tested forward, what waits on the owner, tonight's paper orders, and every idea tested with its verdict |
| Strategies | every idea with its verdict; each opens a strategy page |
| A strategy | Results (profit across its periods, the holdout marked, years, months, costs, weaknesses, the evidence in order), Trades, Paper book, Report (REPORT.md and HYPOTHESIS.md), Studies, Runs |
| Studies | every search and test, including those done by research scripts, with its trial count and verdict |
| Paper trading | each paper ledger: tonight's orders, positions, the books side by side |
| Runs | every run with filters (kind, period, strategy); the selected run's tearsheet, event study, tick study or book |
| Compare | up to four backtests overlaid, with a side-by-side table |
| Parameters | a map of any result across one or two settings that differ between runs |
| Trials | trial counts by agent, Deflated Sharpe, probability of backtest overfitting |
| Lab | the owner's algorithms in an editor; Run tests one over every stock in the universe and shows the book, the best and worst stocks, every trade, the years, the lookahead check and the trial count |

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
- Changes (save, delete, run, cancel) need the session token the page reads from
  `/api/lab/session`, and come only from the Workbench's own page: the server checks the Host
  and Origin headers and the token. The Lab is off when the server listens beyond this machine
  (`--host 0.0.0.0`).
- `lab.py` holds the endpoints as plain functions; `__main__.py` does the checks and routing.

## How it is built

- `api.py`, `record.py`, `lab.py`, `__main__.py`: a small standard-library server. `api.py`
  reads runs; `record.py` reads the records, the documents and the paper ledger; `lab.py` is the
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
