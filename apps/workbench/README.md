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
| Overview | headline numbers, the latest backtest's curve, strategies, recent runs, trials by family |
| Runs | every run with filters; the selected run's tearsheet, event study or tick study |
| Compare | up to four backtests overlaid, with a side-by-side table |
| Parameters | a map of any result across one or two settings that differ between runs |
| Trials | trial counts by agent, Deflated Sharpe, probability of backtest overfitting |

## How it is built

- `api.py`, `__main__.py`: a small standard-library server with read-only JSON endpoints.
- `web/`: React, TypeScript, Tailwind and Vite (decision 0013).
  - `src/index.css`: the design tokens (colours for the dark and light themes). Components use
    the token names, never raw colour values.
  - `src/components/ui/`: the building blocks (Panel, StatStrip, DataTable, Badge, Button,
    Segmented, EmptyState). **Styling lives in these components.** Pages compose them and add
    layout only.
  - `src/components/charts/`: LineChart and Histogram, drawn as SVG.
  - `src/components/layout/AppShell.tsx`: the side rail and top bar.
  - `src/pages/`: one file per page.
  - `src/lib/`: API types, number formatting, data hooks.
