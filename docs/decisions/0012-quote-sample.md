# 0012 — A quote sample, downloaded by the owner

**Status:** accepted, 2026-11-15 (owner asked for it after the Phase 3 verdict).

**Why.** The rebound verdict rests on a fallback spread table. Massive Stocks Advanced includes
historical NBBO quotes and trades, so the real spread at the events can be measured.

**How.**
1. `kinn quotes plan --run <event study>` draws the same number of events from each liquidity
   bucket and period and writes the time windows (from the event bar to 10 minutes after entry).
2. The **owner** runs `tools/owner/download_quotes.py`. It reads `MASSIVE_API_KEY` from the
   environment or `.env`, sends it only to api.massive.com, and writes under
   `KINN_RAW_DIR/massive/quotes_sample/`. Agents do not run it: it uses a key and writes raw data.
3. `kinn quotes report --run <event study>` compares quoted half-spreads with the cost model.

**Rules kept.** Holdout dates are refused at planning, download and measurement. The sample is a
measurement of costs, not a strategy trial; it does not add to any family's trial count. Using it
to pick *which* events to trade would be a new hypothesis and would count.

**Deferred.** Recalibrating the cost model from the sample (wait for the numbers), and the
limit-order fill analysis on the downloaded trades (a new written hypothesis first).
