# 0017 — Intraday first; what "good enough to paper trade" means

**Status:** set by the owner, 2026-11-15 (recorded by claude).

**Focus.** Intraday strategies only for now. The daily engine (`kinn book`) and `momentum_12_1`
are parked: kept, tested, not developed.

**Targets.** The earlier aim of 3–4% a trade is withdrawn. A strategy may go to paper trading
when, out of sample:

| | Bar |
|---|---|
| Net return per trade at 2× slippage | at least +1.0% |
| Sharpe (daily P&L, annualised) | above 1 |
| Worst drawdown | under half the account |
| Fills | confirmed against real trades (tick data), not only minute bars |

**Two agents, one repo.** Astra researches a separate intraday alpha in the `gpt` lane
(`agent/gpt/...` branches, its own strategy folders and runs). Neither agent edits the other's
strategy folders or runs. The run store and the trial counts per family are shared.

**Unchanged.** The holdout stays sealed until the owner says so. Every run is a trial. The plan
is written before the run.
