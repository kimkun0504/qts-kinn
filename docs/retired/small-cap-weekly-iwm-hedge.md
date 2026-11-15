# Retired: weekly small-cap long book with an IWM hedge

**Source (read-only):** `~/Desktop/QTS/qts-small-cap` — `docs/notes/2026-11-14_signal_results.md`,
`2026-11-14_decision_stop.md`, `2026-11-14_small_account_costs.md`.
**Verdict (owner, 2026-11-14):** stopped after nine pre-registered trials; none passed. The
holdout was never opened.

## What it was

A 28-name long book in small and micro caps, entered in four weekly batches, hedged with a short
in IWM, sized for a $10k account. Signals tested one by one, each pre-registered.

## Honest result

| Signal (holding period) | Excess per trade | t | Net per trade |
|---|---|---|---|
| Earnings-announcement return (20 d) | +0.11% | 0.9 | +0.03% |
| Earnings surprise (20 d) | +0.12% | 0.8 | −0.18% |
| Insider buying clusters (20 d) | −0.27% | −1.5 | −0.47% |
| Change in 13F ownership (20 d) | −0.17% | −1.3 | −0.47% |
| Reversal after news-free drops (5 d) | +0.12% | 3.2 | −0.18% |
| Same, micro caps (5 d) | +0.32% | 5.2 | −0.31% |
| Value + profitability + growth + momentum (63 d) | −0.20% | −0.7 | −0.44% |
| Combined 28-name book | CAGR −21%, Sharpe −1.18 | | |

## Lessons Kinn keeps

1. **Costs decide.** At $10k a round trip cost about 27 bp in ranks 1,001–3,000 and about 48 bp
   in micro caps, mostly the $0.35 per-order commission minimum on ~$320 positions. The one
   robust effect (reversal after news-free drops) lost money after costs, in micro caps even
   with zero price impact. → Kinn: the cost model is platform-owned and includes the per-order
   minimum, whole shares, and results at 1× and 2× slippage (decision 0004).
2. **A small book holds the extreme tail of a score**, where signals often reverse: the combined
   book bought falling knives. → Event studies report the distribution, not only the mean.
3. **Raw gain per trade is mostly the market's own rise.** Measure against a benchmark and net.
4. **Spread estimates from daily high/low overstate spreads several times** on this data (median
   half-spread of 18–37 bp for the 1,000 largest names). → Kinn does not use them as the base
   case; without quotes it uses a stated conservative fallback.
5. **The lead that survived:** news-free reversal, strongest in illiquid names, needs intraday
   execution. That became the intraday rebound hypothesis.
