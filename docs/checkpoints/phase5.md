# Checkpoint: Phase 5 (multi-agent and CI), 2026-11-15 — and the build summary

## Phase 5

- **Two concurrent runs, one per worktree, register cleanly.** Worktrees `wt-claude` and
  `wt-gpt` (branches `agent/claude/…` and `agent/gpt/…`) each started
  `kinn run random_entry --config concurrency_check` in the same second, writing to the shared
  run store. Result: two run folders, `20261115T193231Z_claude_random_entry_ccd95090` and
  `20261115T193231Z_gpt_random_entry_ccd95090`, both complete, identical trade tables (208
  trades), both counted (the canary family went from 10 to 12 trials). The registry index
  rebuilt without conflict, because the manifests are the source of truth.
- **CI:** `.github/workflows/ci.yml` runs lint, import rules, unit tests, canaries and the
  pre-commit hooks (gitleaks, large files, data files) on every pull request.
- **Guide:** [docs/NEW_STRATEGY.md](../NEW_STRATEGY.md). **Owners:** [docs/OWNERS.md](../OWNERS.md).

**Not done by the agent, needs you (two commands).** The worktrees for the demonstration were
made in the agent's scratch space, because git needs to delete lock files and the agent may not
delete in your folders. On the Mac, from `~/Desktop/QTS/qts-kinn/qts-kinn`:

```bash
git branch main agent/claude/phase1-data        # create main (human-only)
git worktree add ../wt-claude -b agent/claude/next main
git worktree add ../wt-gpt -b agent/gpt/next main
```

Then in each: `uv sync && uv run pre-commit install`, and set `KINN_AGENT`.

## Summary of the build

| Phase | Outcome |
|---|---|
| 0 Foundation | Monorepo, locked env, import rules, AGENTS.md, decisions, retired pages |
| 1 Data | 5,077 sessions of bars as Parquet; security master; point-in-time panel; seal; audit |
| 2 Research core | Simulator, costs, sizing, `kinn run`, registry, tearsheet, validation statistics; four canaries pass |
| 3 First strategy | Rebound event study: gross +0.90%, net −0.09% at 1×, −0.72% at 2×. **Parked** |
| 4 Workbench | Run list, comparison, tearsheets, event studies, parameter map, trials and overfitting |
| 5 Multi-agent, CI | Concurrent runs register cleanly; CI workflow; guide |

85 tests. Five import contracts. Eleven decision records.

## Deferred (and where it is recorded)

- Daily engine, optimizer, paper book, broker adapters (decision 0006).
- Short selling, compounding, historical fee schedules, a sweep command, auction fill models
  (decision 0010).
- Launching runs from the Workbench, a front-end build chain (decision 0011).
- Sharadar fundamentals, insider and 13F tables (docs/data/DATA_NOTES.md).

## Open risks, most important first

1. **The holdout's physical seal is not in effect for agents.** `MarketData/sealed/` sits inside
   the folder connected to the agent session. It was not listed or read. Connect only
   `MarketData/raw`, `MarketData/processed` and the Kinn folder, or move `sealed/` away.
2. **No quotes.** Every cost-sensitive conclusion, including Phase 3's verdict, rests on a
   fallback spread table. A quote sample is the next purchase to make.
3. **The research window is spent for the rebound idea** (10 trials charged, plus about 2,300
   exploratory variants from the old build that are not yet charged). Only the holdout can
   confirm anything, and it works once.
4. **Decision 0009** (reading post-seal ticker-change events) needs your confirmation.
5. **`category` and `exchange` are 2026 labels**, and Sharadar's market cap is assumed point in
   time. Both could leak a little; neither is verified.
6. **Halts are invisible** in the data ("no bar, no fill").
7. **Lookahead replay is sampled.** Use `lookahead_check_rate: 1.0` for a new strategy's first runs.
8. **Day-trading rules.** The pattern-day-trader rule was replaced on 2026-06-04, with brokers
   given until 2027-10-20 to implement. Confirm how IBKR treats a $10k margin account today.
9. **gitleaks was run as a binary by the agent**, not through pre-commit, because the hook's Go
   download is blocked in the agent's environments. CI runs the real hook; watch its first run.
10. **Astra's delivery** (`~/Desktop/QTS/qts-intraday-astra`) has not been read or compared.

## Housekeeping

- `~/Desktop/QTS/qts-kinn/_transfer/` (bundles used to push) and
  `MarketData/processed/kinn/builds/07b6a77a41/` (superseded build, 1.2 GB) can be deleted.
- The nested folder name (`qts-kinn/qts-kinn`) can be changed by renaming the outer folder.
