# Checkpoint: Phase 3 (first strategy, event study only), 2026-11-15

**Verdict: not worth developing as defined.** Full report:
[strategies/intraday_rebound/REPORT.md](../../strategies/intraday_rebound/REPORT.md).

- Hypothesis written and committed (`ae137ee`) before the tool or the run existed.
- One counted run, no parameter search: `20261115T191143Z_claude_intraday_rebound_217e2dd7`.
- Result, held to the close: gross **+0.90%**, net **−0.09%** at 1× slippage (95% interval
  −0.42% to +0.25%), **−0.72%** at 2×. The pre-set bar was +0.5% with an interval above zero.
- The rebound is real but smaller than the round-trip cost (about 1.00% at $500 a position).
- The only bucket above zero is liquid names (ADV ≥ $10M): +0.32% net, interval includes zero.

Disclosure: before the counted run, the universe loader was timed on three sessions (2005,
2015, 2021) printing only symbol counts and timings, not signals or returns.

New platform pieces: `kinn run --study` (event studies through the run store), the panel's
`filings_prev` / `filings_today` columns (data version 2, build `77ff35f8b7`).

Housekeeping for the owner: the superseded build folder
`MarketData/processed/kinn/builds/07b6a77a41/` (1.2 GB) can be deleted.
