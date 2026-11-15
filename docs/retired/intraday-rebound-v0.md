# Prior work: intraday rebound, first build (code retired, hypothesis continues)

**Source (read-only):** `~/Desktop/QTS/qts-intraday-rebound` — `docs/notes/2026-11-14_stage1_results.md`,
`2026-11-14_stage2_results.md`, `2026-11-15_exploration_open_sweep.md`, `runs/trial_ledger.jsonl`.
**Status:** the standalone repo is retired with the rest of the old build. The hypothesis is
Kinn's first strategy. This page exists so the new work starts with the old trial count and the
old doubts, not from a blank slate.

## What was tested (all on 2003-09-10 to 2023-11-08; holdout never opened)

A resting buy limit below the prior close in micro caps with no news; sold at the close; $500
positions.

| Stage | Trials | Result |
|---|---|---|
| 1, daily bars | 3 pre-registered | micro caps +0.93% net (suspected overstated); small caps and news drops failed |
| 2, minute bars | 3 pre-registered | micro caps, no news: **+0.74% net** a trade (t 16); with ADV ≥ $1M: +0.15% (fail) |
| Exploration | about 2,300 variants tabulated, **not trials, chosen after looking** | "opening sweep" rule: +3.4% as modelled, about +2% conservative (2017–2023) |

## Why the numbers are not yet believable

1. **Fragile to queue position.** If the price must trade 2% through the limit before the order
   counts as filled, the stage-2 rule earns 0.00%. The profit sits in shallow touches, where a
   real order may be behind others. Minute bars cannot settle this; quotes and ticks can.
2. **Fill assumptions made half the opening-sweep profit**: price improvement at the open and
   selling at the last print. An independent review removed both: about +2% a trade, and
   little or nothing under the harshest exit.
3. **It has faded.** Stage-2 net per trade: −0.07% in 2020, +0.21% in 2022, −0.19% in 2023.
4. **It lives in the thinnest names** and shrinks with liquidity; the liquid version fails.
5. **Capital, not return per trade, is the constraint.** About 670 resting orders a day for
   1.6 fills; roughly 2.5–4.5% a year on the money tied up, unless the broker lets orders rest
   beyond buying power (untested).
6. **The research window is used up.** Every rule above was shaped on it.

## What Kinn must carry over

- **Trial count.** The `intraday_rebound` family starts with these prior looks on the same data:
  6 pre-registered trials plus the exploration (about 2,300 variants). Deflated Sharpe and PBO
  in Kinn must not start from zero. How to count the exploration is an open owner decision
  (docs/checkpoints/phase0.md).
- **Fill realism as a first-class parameter:** trade-through margin, auction participation, and
  exit price are engine settings shown in every report, not strategy choices.
- **No code yet.** Anything reused from that repo goes through docs/SALVAGE.md.
