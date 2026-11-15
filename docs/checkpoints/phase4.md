# Checkpoint: Phase 4 (Workbench), 2026-11-15

**Done.** `apps/workbench`: run list and comparison, tearsheets, event-study viewer, parameter
map, and the trial-count and overfitting panel. Start it with `uv run python -m apps.workbench`.
Design: a dense research ledger on a slate-blue ground, numbers in tabular figures, with the
trial count per family as the one loud element. Follows light or dark system setting.

Checked by loading it in a browser against the real run store (11 runs): no script errors;
the run, event-study, parameter and trials views render with the real numbers.

Test data for the parameter map and the overfitting panel: a 3×3 sweep of the random-entry
canary on 2019 (nine counted runs in family `canary_random_entry`). As it should, every cell
loses 0.26–0.30% a trade and the Deflated Sharpe is 0.

Not built (decision 0011): launching runs from the UI, authentication, a build chain.
Known gaps: the parameter map averages runs that share a cell; curves are compared only when
runs cover the same sessions.
