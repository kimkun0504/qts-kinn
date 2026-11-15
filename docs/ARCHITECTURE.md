# Architecture

Kinn answers one question honestly: does an intraday strategy make money after costs, on data it
has not been tuned on? Everything below serves that.

## Shape

```
strategies/<name>  ──►  kinn (platform)  ◄──  apps/workbench
        thin              stable, tested         reads the run store only
```

Inside the platform, lower layers never import higher ones:

```
reporting   registry   validation
        engine.intraday
   features   costs   risk
            data
            core
```

Only the bottom line (`kinn.core` imports nothing else) is enforced by import-linter today. The
rest is the intended direction and gets a contract when the modules exist (Phase 2).

## Rules (each is enforced in code or by a test, not by good intentions)

1. **Imports go one way.** `strategies/` and `apps/` import `kinn`; `kinn` imports neither;
   nothing imports `research/`. Enforced by import-linter in pre-commit and in `tests/`.
2. **Every feature declares when it becomes available**, for example "known at bar close, usable
   from the next bar's open" or "known at the prior day's close". The engine refuses any use
   before that time. This structural guard is the main defence against lookahead.
3. **Execution is realistic by construction.**
   - A signal from bar *t* acts at bar *t+1*'s open at the earliest.
   - A limit order fills only if the price trades through the limit.
   - Stops honour gaps: a stop gapped through fills at the open, not at the stop price.
   - No fills during halts.
   - Participation is capped at a share of each bar's volume.
   - Positions go flat before the close, by a configurable cutoff.
4. **Strategies are thin.** A strategy defines its universe, signals and parameters. It owns no
   cost model, simulator or data loader.
5. **One entry point:** `kinn run <strategy> --config <name>`. Each run writes `runs/<run_id>/`:
   - `manifest.json`: strategy, config hash, git commit, dirty flag, data build ID, agent,
     branch, times;
   - trades, equity and metrics in versioned schemas.
   Runs from uncommitted code are refused unless `--scratch`; scratch runs stay out of reports.
   `run_id = <UTC timestamp>_<agent>_<strategy>_<short hash>`.
6. **Registry.** Each run's manifest is the source of truth. A DuckDB index over the manifests is
   rebuilt on demand, so two agents writing runs at once cannot corrupt shared state. Trial
   counts for Deflated Sharpe and PBO include every run from every agent in a strategy family.
7. **Holdout seal, two layers.**
   - Physical: holdout files live in `MarketData/sealed/`, which the owner keeps locked.
   - In code: the data layer raises on any date on or after `HOLDOUT_START = 2023-11-09`, for
     every source. The only way past is `--unseal` together with `KINN_UNSEAL_TOKEN`, which only
     the owner sets. Every unseal is logged. Later downloads dated on or after that day are
     holdout too. `HOLDOUT_START` is a constant in `kinn.core.settings`, with no setting for it.
8. **Cost model.** IBKR Pro tiered commissions (rates verified, source recorded in the
   calibration file), SEC fee and FINRA TAF on sells, spread and market-impact slippage with a
   conservative fallback when quotes are missing and higher slippage under $5. Every report
   shows results at 1× and 2× slippage.
9. **Settings.** All paths come from environment variables through `kinn.core.settings`:
   `KINN_RAW_DIR` (read-only), `KINN_DATA_DIR`, `KINN_RUNS_DIR`. Settings refuse a path inside a
   `sealed` folder and refuse writing inside the raw folder.
10. **Workbench.** Reads only the run store, through the schemas. Never imports strategy code.

## Where things live on disk

| What | Where | In git |
|---|---|---|
| Code, docs, configs | this repo | yes |
| Vendor data | `KINN_RAW_DIR` | no, read-only |
| Derived Parquet, by build ID | `KINN_DATA_DIR` | no, rebuildable |
| Run outputs | `KINN_RUNS_DIR` (default: `runs/` beside the repo) | no |
| Agent worktrees | beside the repo (`wt-claude/`, `wt-gpt/`) | they are checkouts |

The repo and its worktrees share a parent folder, so by default they share one run store.

## Seams for deferred work (no code yet; see decision 0006)

- **Daily cross-sectional engine and optimizer:** would sit at `kinn.engine.daily`, beside
  `kinn.engine.intraday`, sharing the core types and the cost model.
- **Paper book and monitor (`apps/paper`):** would consume the same `Order` / `Fill` types the
  simulator produces, so a strategy runs unchanged.
- **Broker adapters:** would implement the fill side behind the paper book. Live stays locked.
