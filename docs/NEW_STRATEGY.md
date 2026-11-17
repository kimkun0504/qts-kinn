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

11. **Keep the record.** Add a `record:` block to `strategy.yaml` when the first verdict is
    written, and update it with every later verdict (see below). The Workbench shows it.

Before trusting any number, go through the bias checklist in [AGENTS.md](../AGENTS.md).

## A daily alpha (multi-day holding)

1. Create `strategies/<name>/` with `strategy.yaml` (`kind: forecast`, a `family`) and
   `HYPOTHESIS.md`, written and committed before any run: signal, universe, periods, the
   variants, the selection rule and the validation bars.
2. Write `alpha.py`: a class with `name`, `lookback` and `scores(view)`, and `build(params)`.
   Read history with `view.history("ret", n)`; pre-open values with `view.today(...)`;
   fundamentals with `view.fundamental(...)` after declaring `fundamentals = (...)`.
3. Write the book configs in `books/` (`extends:` shares settings between them).
4. `uv run kinn book <config>`. Each counted run is a trial for the book's family.
5. Write `REPORT.md` with the verdict against the bars set in step 1.

`strategies/momentum_12_1/` is the worked example.

## The record in `strategy.yaml`

The Workbench's home page, strategy pages and Studies page are built from this block
(decision 0022). Write it in plain words; it is what the owner reads first.

```yaml
record:
  title: Earnings drift            # the page title
  idea: Earnings drift             # the row name in "everything tested"
  horizon: 40 sessions
  verdict: passed_holdout          # planned | passed_holdout | testing | weak | failed_holdout | parked | closed
  label: Passed holdout            # optional; overrides the verdict's default label
  result: "+$11,430 a year in the holdout"     # one line, the number that matters
  summary: >-                      # the rule in two sentences
    ...
  paper: earnings_drift            # the paper ledger's folder, if it has one
  periods:                         # the runs behind the page's numbers, oldest test first
    - {key: holdout, config: holdout}          # the latest complete run of each config is used
    - {key: search, config: research}
  weaknesses: ["..."]
  in_test:                         # variants being tested forward (their own row and verdict)
    - {idea: ..., verdict: testing, result: ..., stats: [...], settle: [...]}
  waiting: ["what only the owner can do next"]
  evidence:                        # what was found, in order
    - {when: 2026-11-16, title: ..., kind: found, text: "..."}   # found | passed | failed | running | open
  studies:                         # every search or test, with its trial count, scripts included
    - {name: ..., when: 2026-11-16, trials: 438, result: "...", verdict: lead}   # lead | passed | failed | note
```

`board: false` keeps a strategy off the board (a control, or a folder that only holds studies);
its `studies` still appear on the Studies page. Numbers in `periods` come from the runs; text
fields are not checked against them, so change both together.
