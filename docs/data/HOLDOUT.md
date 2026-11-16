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

# 1. Build the unsealed data. Converts the sealed bars, builds the tables, prints a check.
#    It can be interrupted and run again; finished files are skipped.
uv run kinn holdout build

# 2. The one run.
uv run kinn run rebound_limit --config holdout_s_l468 --unseal --workers 4

unset KINN_UNSEAL_TOKEN
```

## What step 1 prints, and what to do with it

| Line | Should be |
|---|---|
| `holdout_sessions`, `first_session`, `last_session` | about 756 sessions from 2023-11-09 |
| `sharadar_reaches` | filings (`events`) and `actions` up to early November 2026 |
| `same_before_seal` | `True`: the unsealed build equals the research build on every earlier date |

If `same_before_seal` is `False`, do not run step 2. Paste the output to the agent: the two
counts say how many rows differ, and nothing about any strategy.

Step 2 refuses to start if the data does not reach the end of the run's period.

## What it leaves behind

- `MarketData/processed/kinn/holdout/`: the unsealed bars and tables, in their own folder.
  The research build, `builds/CURRENT` and the seal on every ordinary command are unchanged.
- `MarketData/processed/kinn/unseal_log.jsonl`: one line for every read of a holdout date.
- One run in the run store, marked `unsealed` in its manifest and "Holdout" in the Workbench.

## After

The holdout is spent for that strategy family. Nothing else is run on it: no second variant,
no sweep (the code refuses a sweep), no re-run after a change.
