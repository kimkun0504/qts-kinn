# Timed after-hours earnings discovery

Prepared; no empirical run. The hypothesis was committed before
implementation. A new declared timestamped input is required.
The owner has not yet authorized that platform adapter or the
new derived-input build from existing raw files.

Strategy tests use synthetic contract fixtures only. They do not
certify the unimplemented real loader, timestamp semantics,
identity mapping, input coverage or actual fills. No return,
sample size or risk estimate exists for this rule yet.

Focused strategy/repository tests, lint and import contracts passed.
Synthetic checks include winter/summer timezone conversion, the
availability delay, earliest-filing selection, a later filing unable
to rescue a failed event, deliberate future-filing cheating,
future-price perturbations and after-hours timed execution.
Additional synthetic checks cover the last permitted entry
minute, acceptance seconds, entry expiry after a cap rejection,
and failed liquidation retained as unresolved exposure with
no completed event return. An official regular close cannot
silently flatten that residual.
