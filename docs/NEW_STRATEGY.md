# How to start a new strategy

1. **Claim it.** Add a row for `strategies/<name>` to [OWNERS.md](OWNERS.md) in your first pull
   request. Work in your own worktree on `agent/<claude|gpt>/<name>`.
2. **Copy the template.** `cp -r strategies/_template strategies/<name>` and fill in
   `strategy.yaml`: name, owner, cost calibration, and the `family` its trials are charged to.
   If anyone has looked at this idea on this data before, set `prior_trials`.
3. **Write `HYPOTHESIS.md` and commit it before any run.** Rationale, universe, the exact event,
   what counts as support and as failure, the risks, and prior looks. Later changes go in dated
   addenda.
4. **Write `strategy.py`.** Only a universe, features and `signals(view, features)`.
   - Use features from `kinn.features.library`; to add one, declare when it is available
     (`PRIOR_DAY` or `BAR_CLOSE`) and add it there (ask the owner of `kinn.features`).
   - A signal's `minute` is the last bar it used. The engine fills from the next bar.
   - A universe may filter only on pre-open columns.
5. **Test the definition** on hand-built sessions (see `tests/test_intraday_rebound.py`),
   including `check_no_lookahead`.
6. **Commit, then run an event study first:**
   `uv run kinn run <name> --config <config> --study`. One definition, no search.
   Uncommitted code is refused unless `--scratch`; scratch runs do not count and cannot be
   reported.
7. **Read it in the Workbench** (`uv run python -m apps.workbench`): the curve net of costs at
   1× and 2×, the intervals, and the trial count.
8. **Write `REPORT.md` with a verdict**: develop, park or retire, and what would change it.
9. Only after a "develop" verdict: backtests with exits (`kinn run` without `--study`), then
   sweeps. Every run is a counted trial; watch the Deflated Sharpe and PBO in the Workbench.
10. **Never** touch the holdout. Unsealing is the owner's decision, once, for a frozen strategy.

Before trusting any number, go through the bias checklist in [AGENTS.md](../AGENTS.md).
