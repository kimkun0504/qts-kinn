# Larger prints at a narrow-range breakout

Status: implementation under test. Hypothesis commit `d52f235`
precedes every empirical run. One fixed-time primary and its
matched base-event control are registered. Only the primary can
advance, and it must beat the control's stressed mean in both
development blocks in addition to passing the return and sample
gates. No empirical result is available yet.

The price/print-size mathematics, fixed decision time, matched
control, prefix replays, missing-data rejection, next-minute
expiry and timed market exit pass synthetic tests. Repository
rules, strategy loading, Ruff and import contracts pass.

This is an adaptive follow-up with extensive prior looks. The
data limitations and earlier documentation-sample exposure are
preserved in HYPOTHESIS.md.
