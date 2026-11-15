# 0004 — The cost model is central, and reports show 1× and 2× slippage

**Status:** accepted, 2026-11-15 (owner).

**Context.** The weekly small-cap search found one statistically robust effect and no trade that
survived costs (docs/retired/small-cap-weekly-iwm-hedge.md). At a $10k account the per-order
commission minimum alone is a large share of a small position.

**Decision.** One platform cost model, used by every run; strategies cannot bring their own.
IBKR Pro tiered commissions with the per-order minimum, regulatory fees on sells, spread and
impact slippage, a conservative fallback without quotes, and more slippage under $5. Every
report shows 1× and 2× slippage.

**Consequences.** A result is quoted net. One that fails at 2× is reported as fragile.
