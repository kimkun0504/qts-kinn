# Earnings drift ($50M to $300M)

No holdout result yet. Plan and the rule: [HYPOTHESIS.md](HYPOTHESIS.md). How the rule was
found and tested: [`strategies/swing_search/REPORT.md`](../swing_search/REPORT.md).

## The engine reproduces the research (2026-11-16)

`kinn swing` finds the same trades as the research scripts: of the 1,488 research trades of
2005 to 2022, 1,479 are found with gross returns equal to 15 decimal places. The nine it
drops are stocks back from a halt or relisting, which the rule now excludes; one trade is
added at the 15% boundary by rounding.

| Run | Period | Signals | Trades taken | A trade, 1× | A trade, 2× | Spread crossed | Total, 1× | Sharpe, 1× / 2× | Worst drawdown, marked daily |
|---|---|---|---|---|---|---|---|---|---|
| `…_71f5b45c` (`research`) | 2010–2022 | 1,059 | 833 | 3.56% | 3.18% | 2.39% | $59,246 | 1.30 / 1.17 | $8,880 |
| `…_f50069e4` (`early`) | 2005–2009 | 430 | 343 | 4.60% | 4.23% | 3.46% | $31,463 | 1.94 / 1.79 | $9,734 |

1× is the auction allowance (25 bp a side under $1M a day), 2× doubles it. The book is
$20,000 in 10 positions; a signal without a free slot is skipped. Trades are booked on the
exit day, so the Sharpe ratios here are a little higher than the research report's, which
marks positions every day.

These two runs are the same rule on the same years as the research and add no evidence.

## Next

The holdout, 2023-11-09 to 2026-11-06, once, by the owner:
`uv run kinn swing earnings_drift --config holdout --unseal` (see `docs/data/HOLDOUT.md`).
What passes and what fails is set in HYPOTHESIS.md.
