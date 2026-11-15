# 0005 — Researcher-grade tools, built on the run store

**Status:** accepted, 2026-11-15 (owner).

**Decision.** The platform provides a signal lab (event studies), feature toggles and sweeps,
holdout and PBO controls, and capacity curves. All of them go through `kinn run` and the run
store, so every use is a counted trial.

**Consequences.** No tool may produce a number outside the run store. The Workbench (Phase 4)
only displays what the store holds.
