# Earnings drift ($50M to $300M): passed the holdout

Plan and the rule: [HYPOTHESIS.md](HYPOTHESIS.md). How the rule was found and tested before
the holdout: [`strategies/swing_search/REPORT.md`](../swing_search/REPORT.md).

## The holdout (2026-11-16, run by the owner)

Run `20261116T193948Z_human_earnings_drift_4e47e374`, config `holdout`, 2023-11-09 to
2026-11-06, on the unsealed build, at commit `f0c6c76`. One run. The owner's rehearsal on the
search years through the unsealed build printed the research run's figures exactly (833
trades, 3.56%).

| | Holdout | Search years (2010–2022) | 2005–2009 |
|---|---|---|---|
| Signals | 460 | 1,059 | 430 |
| Trades taken (10 positions of $2,000) | 266 | 833 | 343 |
| A trade, auction allowance (1×) | **5.04%** | 3.56% | 4.60% |
| A trade, allowance doubled (2×) | **4.67%** | 3.18% | 4.23% |
| A trade, modelled spread crossed | 3.91% | 2.39% | 3.46% |
| Median trade, winners | 1.0%, 52% | | |
| Total, 1× / 2× | $26,716 / $24,765 | $59,246 / $52,868 | $31,463 / $28,929 |
| Sharpe, 1× / 2× (booked on exit day) | 1.47 / 1.37 | 1.30 / 1.17 | 1.94 / 1.79 |
| Worst drawdown, marked daily | $6,784 | $8,880 | $9,734 |

**Verdict by the rule set before the run** (mean a trade at 2× of 1% or more and a positive
total at 2×): **passed.**

By year (1×): 2023 from 9 November, +7.3% (10 trades); 2024, +9.8% (85); 2025, +4.9% (87);
2026 to 6 November, +0.1% (84). Three things to keep in view:

- **2026 was flat.** 84 trades made nothing (−0.3% at 2×). Flat years have happened before
  (2011, 2022), and the rule's profit has always come from a few large winners, but the most
  recent year is the weakest of the three.
- **2024 carries the total:** $16,581 of the $26,716.
- **Signals came almost twice as often** as before the seal (about 150 a year against 80),
  so the 10-position book skipped 182 of 460. The skipped signals are not in the run's
  files; the per-trade figures are for the trades taken, chosen by volume.

The holdout is now spent for the family `swing_search`.

## Fills, measured from ticks (2026-11-16)

150 trades of 2015 to 2023 at random; quotes and trades around the open of the entry day and
the close of the exit day (`research/claude/swing_fill_measure.py`; plan in HYPOTHESIS.md).

| | Under $1M a day (93 trades) | $1M a day and over (57) |
|---|---|---|
| Opening cross printed | 99% | 100% |
| Closing cross printed | 88% | 100% |
| A cross on both sides | 87% | 100% |
| Dollars in the opening / closing cross, median | $36,000 / $27,000 | $115,000 / $93,000 |
| The same, smallest tenth | $3,500 / $2,400 | $30,000 / $10,000 |
| Opening cross against the midpoint 30 s later | +0.08% | +0.20% |
| Closing cross against the midpoint 30 s earlier | −0.02% | +0.03% |
| Market order instead, both sides, against the bar's prices | 1.61% | 0.52% |
| Modelled spread crossed, both sides | 2.0% | 0.86% |

- **The bar's open and close are auction prints.** The cross price is the bar's price in 86%
  of entries and 96% of exits.
- **The auction price is fair.** A buyer in the opening cross pays about 0.1% more than the
  midpoint half a minute later; a seller in the closing cross gives up nothing. The auction
  allowance (0.50% a round trip under $1M a day, 0.20% above) is larger than this under $1M
  and about equal to it above.
- **Market orders cost less than modelled:** 1.2% a round trip on average, against the 1.6%
  the "spread crossed" column assumes. Most of it is the entry: the quote is wide just after
  the open (half-spread 1.3% under $1M a day) and narrow before the close (0.3%).
- **Limits.** One exit in eight under $1M a day had no closing cross; there an on-close
  order does not fill and the position has to be sold in the market before the close. In a
  tenth of trades the cross is about the size of a $2,000 order, and such an order would
  move it. The ticks cannot show by how much.

By the rule written before reading the ticks (a cross on both sides in nine trades of ten,
and the cross within the allowance of the midpoint), **the auction allowance stands**: 92% of
trades have both crosses, and the cross costs 0.06% a round trip under $1M a day and 0.23%
above. This is not a `kinn fill-check` run, so the Workbench does not show fills as confirmed.

## The engine reproduces the research

`kinn swing` finds the same trades as the research scripts: of the 1,488 research trades of
2005 to 2022, 1,479 are found with gross returns equal to 15 decimal places. The nine it
drops are stocks back from a halt or relisting, which the rule excludes; one trade is added
at the 15% boundary by rounding. Runs `…_71f5b45c` (`research`) and `…_f50069e4` (`early`).

## Against the targets of decision 0017, on the holdout

| Target | Result |
|---|---|
| Net a trade of +1.0% at 2× | 4.67% |
| Sharpe above 1 | 1.37 at 2× (trades booked on the exit day) |
| Drawdown under half the account | $6,784 of $20,000, marked daily |
| Fills confirmed | Measured from ticks as above; not yet traded live |

## What it is not yet

It has not traded. Nothing sends on-open and on-close orders today: the Trader has no broker
connection, and the rule needs each evening's earnings 8-Ks, which the live data feed does
not yet supply. Position count (10 or 20) and what to do with the signals a full book skips
are the owner's choices.
