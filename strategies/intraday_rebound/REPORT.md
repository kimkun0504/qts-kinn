# Report: intraday rebound after a no-news drop

2026-11-15, claude. Event study only (Phase 3). Definition and criteria: [HYPOTHESIS.md](HYPOTHESIS.md).

## Verdict

**Not worth developing as defined. Park it.** Buying at market after a no-news 10% intraday drop
and holding to the close earns **−0.09% a trade net of costs** (95% interval −0.42% to +0.25%)
at 1× slippage and **−0.72%** at 2×. The bar set in advance was +0.5% with an interval above
zero. The owner's 3–4% target is not in sight for this form of the trade.

The rebound itself is real: **+0.90% gross** to the close (interval +0.58% to +1.24%). It is
smaller than the cost of getting it, about **1.00% a round trip** at $500 a position in these
stocks.

## Evidence

Run `20261115T191143Z_claude_intraday_rebound_217e2dd7` (event study, counted), 2003-09-10 to
2023-11-08, data build `77ff35f8b7`, commit `822eabad`. 108,945 events on 4,980 sessions, about
22 a session. Median entry price $6.77; median 20-day dollar volume $2.7M. Full tables and the
curve: `study.html` / `study.md` in the run folder.

| Held | Gross | Net, 1× slippage (95% interval) | Net, 2× slippage |
|---|---|---|---|
| 5 min | +0.17% | −0.82% (−0.85% to −0.79%) | −1.45% |
| 30 min | +0.53% | −0.47% (−0.56% to −0.34%) | −1.09% |
| 60 min | +0.70% | −0.30% (−0.42% to −0.15%) | −0.92% |
| 120 min | +0.83% | −0.17% (−0.34% to +0.01%) | −0.79% |
| to the close | +0.90% | **−0.09% (−0.42% to +0.25%)** | −0.72% |

Against the three criteria:

| Criterion | Result | Met? |
|---|---|---|
| Net to the close at 1× is at least +0.5%, interval above zero | −0.09% (−0.42% to +0.25%) | No |
| Positive in 2017–2023 alone | +0.04% (−0.31% to +0.42%) | Barely, not distinguishable from zero |
| Positive at 2× slippage | −0.72% | No |

### What the pre-declared splits show (for reading, not for selection)

- **The bounce builds slowly.** About a fifth of it comes in the first 5 minutes and most of it
  within 90 minutes. There is no quick snap-back to capture.
- **Liquidity cuts the other way from the earlier build.** Thin names (ADV under $1M) bounce most
  gross (+1.25%) but net **−0.46%** because they cost most. Liquid names (ADV $10M and over)
  bounce less (+0.73%) but net **+0.32%** (interval −0.18% to +0.84%), and stay positive at 2×
  (+0.14%). That is the only bucket above zero, and its interval includes zero.
- **By year it is unstable**: positive in 2003–2004, 2010, 2020–2021; clearly negative in 2009,
  2012, 2022 and 2023 (−0.70%, interval −0.92% to −0.47%). The two most recent years are the
  worst of the last ten.
- **Events cluster in market-wide selloffs**: 20,335 events in 2008 and 13,509 in 2020, against
  1,400–4,000 in a quiet year. On those days the "no-news" label means little.

## Why the number may be wrong, in both directions

- **Costs are a fallback, not a measurement.** 0.62% of the 1.00% round trip is modelled
  slippage from a liquidity table, because the data has no quotes. If real spreads after a 10%
  drop are narrower, the net is better; after a sharp drop they are more likely wider.
- **Fees are real and large here**: 0.37% a round trip. At $500 a position the $0.35 minimum
  applies to both orders, and stocks under about $2 pay per-share commission and exchange fees
  on many shares.
- **Capacity**: 40% of entries are larger than 5% of the entry bar's volume, so even $500 would
  often not fill at the bar's open.
- **The news filter is weak** (8-K filings only), as the hypothesis warned.

## Trial count

Family `intraday_rebound`: 9 prior trials from the earlier build plus this run = **10**. Nothing
here was selected among alternatives, so no Deflated Sharpe or PBO applies yet; any follow-up
below adds to the count.

## What would change the verdict

Each of these is a new hypothesis with its own written definition, not a tweak to this one:

1. **A quote sample** for a few hundred of these events. If the real round trip in liquid names
   is near 0.3% instead of the modelled 0.4–1.0%, the liquid bucket becomes interesting.
2. **Liquid names only** (ADV $10M and over), as a pre-registered test. It is the one bucket
   that survived 2× slippage here, but it was read off this study, so it must be confirmed on
   data it was not read from. Only the holdout qualifies.
3. **Passive entry** (a resting limit order below the market, earning the spread instead of
   paying it). This is the earlier build's lead; it depends on queue position, which minute
   bars cannot settle.
4. **Excluding market-wide selloff days** (a condition known at the event minute, such as the
   index's move so far).

Recommendation: do not spend the holdout on this definition. Get quotes first (item 1); it is
the cheapest way to learn whether items 2 and 3 are worth a pre-registration.
