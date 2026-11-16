# 0018 — The trading app is separate from research, and starts as a replay

**Status:** started at the owner's request, 2026-11-15 (claude). Supersedes the deferral of
`apps/paper` in 0006 for the paper book; broker adapters stay deferred.

**Decision.** Trading lives in its own app, `apps/trader` (`uv run python -m apps.trader`,
port 8322). The Workbench stays read-only research. The two share the strategy code, the
simulator's fill function and the cost model, and nothing else.

**How a strategy gets there.** Its `strategy.yaml` names a `candidate` config. The Workbench
shows whether that config's validation run met the owner's targets (0017). The trader runs
exactly that config; there is no other way to choose what it trades.

**The engine is the backtest run a minute at a time** (`apps/trader/engine.py`). Each closed
minute: the strategy's own `signals` on the bars known so far; the simulator's own
`simulate_signal` for every resting order; capital admitted by the simulator's rule. So a
replayed past session gives exactly the backtest's trades for that day. A test holds it to
that on every session of a synthetic backtest, and it matched the validation run to the cent
on six real sessions, including capital-constrained days and a half day.

**Built so far.** The session engine, a replay tape (past sessions from the research store, so
the holdout seal applies), an internal paper book (decision 0003), a halt that cancels resting
orders and keeps positions to the close, saved session records under `<repo parent>/paper/`,
and a local HTTP API with controls that only this computer and this page can use.

**Not built yet.** The screen; the live tape (vendor real-time stream: the owner confirmed the
plan includes it); the daily data the live universe needs; a broker adapter.

**Live data and the seal.** A live session needs about 20 recent days of daily data, which lie
inside the sealed window. The trader will have its own live data path, written by the trader
and never read by research code, so the seal on research stays intact.

**Never.** Real orders. Live trading stays locked (0003).
