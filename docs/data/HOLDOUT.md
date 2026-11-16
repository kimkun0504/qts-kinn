# The holdout: how it is unsealed, once

Decision 0002 seals every date from 2023-11-09. This is the owner's procedure for the one look.
Agents write and test these commands on synthetic data; they never run them on the real sealed
folder and never set the token.

## Before

- The strategy is frozen and its plan, with the rule for every outcome, is written and
  committed (for the rebound: `strategies/rebound_limit/HYPOTHESIS.md`, the holdout addendum).
- The working tree is clean, on the commit that holds that plan.

## The commands (owner, on the Mac)

```bash
cd ~/Desktop/QTS/qts-kinn/qts-kinn
git status                                   # must say: nothing to commit
export KINN_UNSEAL_TOKEN="any phrase you choose"   # only a fingerprint of it is logged

# 1. Build the unsealed data and check it. Can be interrupted and run again.
uv run kinn holdout build

# 2. Rehearsal: the validation run again, through the unsealed data. Not a trial.
uv run kinn holdout rehearse rebound_limit --config validation_s_l468

# 3. The one run. Only after steps 1 and 2 both say "passed".
uv run kinn run rebound_limit --config holdout_s_l468 --unseal --workers 4

unset KINN_UNSEAL_TOKEN
```

`uv run kinn holdout check` repeats step 1's check without rebuilding.

## What the steps print

**Step 1** ends with `check passed` or `check FAILED`. It compares the unsealed build with the
research build on every date before the seal, row by row and column by column:

| Line | Meaning |
|---|---|
| `holdout_sessions`, `last_session` | about 756 sessions from 2023-11-09 |
| `sharadar_reaches` | filings (`events`) and `actions` up to early November 2026 |
| `rows_missing_from_unsealed` | must be empty |
| `rows_only_in_unsealed` | allowed only for a stated reason (see below) |
| `columns_that_differ` / `columns_beyond_tolerance` | the second must be empty |

Two differences are expected and allowed:

- **Last digits of `ret60_prev`.** It is a running sum of logarithms. Its last digits depend on
  which other companies were computed beside it and on the machine, so two correct builds
  differ by about one part in 10^16. Decimal columns count as equal within one part in 10^9.
- **Companies delisted after the seal whose ticker has been reused since.** Sharadar renames
  them with a digit (`ABC1`). The research build cannot know they were delisted, so it looks
  for bars under `ABC1`, finds none and leaves them out. The unsealed build matches them.

**Step 2** runs the validation config through the unsealed data and compares every trade with
the research validation run. It must end with `rehearsal passed` (same trades, same prices,
same profit). It reads only dates before the seal and is a scratch run, not a trial.

**Step 3** refuses to start unless step 1 passed and the data reaches the end of the period.

If step 1 or 2 fails, run nothing else and paste the output to the agent. Neither output says
anything about how any strategy did on the holdout.

## What it leaves behind

- `MarketData/processed/kinn/holdout/`: the unsealed bars and tables, in their own folder.
  The research build, `builds/CURRENT` and the seal on every ordinary command are unchanged.
- `MarketData/processed/kinn/unseal_log.jsonl`: one line for every read of a holdout date.
- One run in the run store, marked `unsealed` in its manifest and "Holdout" in the Workbench.

## After

The holdout is spent for that strategy family. Nothing else is run on it: no second variant,
no sweep (the code refuses a sweep), no re-run after a change.
