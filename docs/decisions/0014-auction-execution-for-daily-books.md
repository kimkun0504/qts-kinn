# 0014 — Daily books trade in the opening or closing auction

**Status:** accepted, 2026-11-15 (claude).

**Context.** The design proposed simulating a book's fills on minute bars, including a policy
that spreads an order through the day.

**Decision.** A daily book trades market-on-open or market-on-close (`execution.at`). Order sizes
are fixed before the open from the previous close. A fill takes the session's official open or
close from the daily bar and pays the cost model's auction fee and auction slippage (10 bps at
1×), capped at 1% of the 20-day median dollar volume.

**Why.** At $25,000 a position is about $1,250, a negligible part of any auction in the 1,000
largest stocks. The auction is the cheapest real way to trade that size and the daily bar holds
its price, so nothing is gained by reading 20 years of minute bars. `ExecutionPolicy` stays a
separate model, so an intraday policy can be added when an account or a universe needs it.

**Consequence.** Auction slippage is a stated assumption, not a measurement. It should be
measured against the quote data before any book is traded.
