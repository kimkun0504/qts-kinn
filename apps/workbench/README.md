# Workbench

The research UI. It reads only the run store (`KINN_RUNS_DIR`), through the run schemas, and
never imports strategy code or touches market data.

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

## Where the record comes from

The run store knows runs. It does not know which idea passed, what a research script found, or
what is waiting on the owner. That is written by hand in a `record:` block in each
`strategies/<name>/strategy.yaml` (decision 0022, and `docs/NEW_STRATEGY.md` for the fields).
`record.py` joins those blocks to the run store and to the paper ledger. The numbers on a
strategy page come from the runs the record names (`periods`), never from the text.

A strategy with no `record:` block still appears, under its owner, with its runs. Update the
block in the same commit as the REPORT.md verdict it summarises.

## How it is built

- `api.py`, `record.py`, `__main__.py`: a small standard-library server with read-only JSON
  endpoints. `api.py` reads runs; `record.py` reads the records, the documents and the paper
  ledger. Restart the server after changing either.
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
  - `src/components/layout/AppShell.tsx`: the side rail and top bar.
  - `src/pages/`: one file per page. `src/lib/route.ts` maps the address (`#/strategy/<name>`)
    to a page, so pages can be linked and the back button works.
  - `src/lib/`: API types, number formatting, data hooks.
