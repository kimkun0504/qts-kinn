# Smaller-print selloff exhaustion

Status: implementation under test. Hypothesis commit `55b62c7`
precedes any empirical run. The primary and its fixed base-event
control are registered; only the primary can advance, and its
stressed mean must exceed the control in both development blocks.

Both policies use the identical first base event per stock. The
primary requires smaller average share size and higher transaction
activity; it cannot wait for a later, more favorable classification.
The signal uses completed bars and the tested count view.

Signal mathematics, the subset and no-later-rescue rules, missing
data rejection, both prefix replays and execution tests pass.
Repository rules, strategy loading and Ruff pass. No empirical
result is available yet. The limitations and earlier
documentation-sample exposure are preserved in HYPOTHESIS.md.
