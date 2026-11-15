# Retired: market-neutral large-cap daily strategy

**Source (read-only):** `~/Desktop/QTS/quant-trading-system` — `docs/WORK_PLAN.md`,
`docs/notes/prefilter_lookahead_2026-11-14.md`, `docs/notes/midcap_check_2026-11-13.md`.
**Verdict (owner, 2026-11-14):** too weak to use anywhere.

## What it was

A machine-learning cross-sectional model (LightGBM + MLP + ridge, 60-day horizon) trading the
1,000 largest US stocks, industry-neutral, long-short at 2× gross, rebalanced every 5 days.
Sharadar daily data, 2003-06 to 2023-11.

## Honest result (net of costs, before the holdout)

| | Large caps | Mid caps (ranks 1,001–2,000) |
|---|---|---|
| Net Sharpe | 0.54 | 0.74 |
| Net return a year / volatility | 2.5% / 4.5% | 5.0% / 6.8% |
| Maximum drawdown | −16.9% | −16.5% |
| Deflated Sharpe | 0.29 at 10 trials: not convincing | passed its own pre-registered check |

Realised volatility ran about 1.3× the forecast. A Sharpe near 0.5 at 2.5% a year does not pay
for the effort at $10k–$100k.

## Lessons Kinn keeps

1. **A data-loading shortcut was lookahead.** The store was prefiltered to the 3,000 names with
   the largest *peak* market cap. Whether a 2002 stock could be traded then depended on how big
   it became by 2026; the full point-in-time universe was loaded on only 24% of dates, and the
   Sharpe was inflated by about 0.1. It was found only because the same config gave different
   results with a different end date.
   → Kinn: universes are built point in time from the full security master, and a canary checks
   that a universe on date *d* does not change when later data is added or removed.
2. **Count trials across the family.** The headline looked fine alone and failed once the nine
   earlier trials were counted. → Kinn: the registry counts every run by every agent.
3. **Identical configs must give identical results.** That check exposed the bug. → A canary.
4. **Daily cross-sectional work is deferred** (decision 0006). Kinn is intraday-first.
