# Workbench

The research UI. It reads only the run store (`KINN_RUNS_DIR`), through the run schemas, and
never imports strategy code or touches market data.

```bash
uv run python -m apps.workbench            # http://127.0.0.1:8321
```

| View | Shows |
|---|---|
| Runs table | every run, newest first: kind, agent, trades, gross, net at 1× and 2×, flags |
| Left rail | trials charged to each family (counted runs here plus earlier looks) |
| Run | the tearsheet of a backtest, or the event-study curve with its intervals and splits |
| Compare | up to four backtests overlaid, with a comparison table |
| Parameters | a map of any result across one or two settings that differ between runs |
| Trials and overfitting | trial counts by agent, Deflated Sharpe, probability of backtest overfitting |

Built without a framework or build step: `api.py` (reads run folders), `__main__.py` (a small
standard-library server) and `static/` (one page of HTML, CSS and JavaScript). See decision 0011.
