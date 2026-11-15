# 0010 — Phase 2 scope: what the engine does not do yet

**Status:** taken by claude in Phase 2, 2026-11-15. Over-engineering guard.

Deferred, with the reason:

- **Short selling.** The first hypothesis is long only. Shorts need borrow cost and locate rules
  in the cost model; add them with the first strategy that needs them.
- **Compounding.** Sizes are fixed-dollar against a fixed account (decision 0003), which also
  makes sessions independent and runs resumable. Revisit when scaling capital.
- **Quotes in the cost model.** The half-spread is a stated fallback table by liquidity, because
  the data has no quotes. Replace it with measured spreads when a quote sample exists.
- **Historical fee schedules.** Costs use today's IBKR and regulatory rates for all history.
- **Sweeps and feature toggles as commands.** A sweep today is several configs run with
  `kinn run`; the registry counts each. A `kinn sweep` command waits for Phase 3's verdict.
- **Opening and closing auctions as separate fill models.** The 09:30 bar is treated like any
  bar; leftover shares at the end go to the official close with a fixed slippage.
- **Halts.** No halt data: "no bar, no fill".
