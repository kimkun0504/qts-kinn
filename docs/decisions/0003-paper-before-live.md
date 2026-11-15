# 0003 — Paper trading before any real money; live stays locked

**Status:** accepted, 2026-11-15 (owner).

**Decision.** A strategy that passes validation and the holdout is paper traded through an
internal paper book before any live order. Live trading is locked in this build.

**Capital plan (context for sizing and capacity work).** Start with $10k; scale toward $100k+
only if the strategy works consistently; deploy and exit gradually, never all-in. Size research
as if only $10k exists. Account: IBKR Pro margin.

**Consequences.** The paper book, monitor and broker adapters are deferred (0006) until a
strategy earns them.
