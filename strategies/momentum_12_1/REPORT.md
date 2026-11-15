# momentum_12_1: report

**Verdict (2026-11-15): parked. It failed two of its three validation bars. The daily engine
behaved as the literature says this signal should, which was the point of the test.**

All runs: $25,000 account, long and short, data build `6453bd3ec8`, costs `ibkr_pro_tiered`.

## Development, 2004-10-01 to 2016-12-30 (3 variants)

| Config | Return a year, 1× | Return a year, 2× | Sharpe 1× | Sharpe 2× | Worst drawdown | Turnover a year |
|---|---|---|---|---|---|---|
| `momentum_dev_monthly` (optimizer) | +2.5% | +1.5% | 0.23 | **0.18** | −59.5% | 8.0× |
| `momentum_dev_weekly` (optimizer) | +0.4% | −1.3% | 0.11 | 0.03 | −67.2% | 12.7× |
| `momentum_dev_ranked` (textbook, 15 a side) | +0.1% | −2.5% | 0.15 | 0.10 | −75.4% | 15.6× |

By the pre-set rule (highest Sharpe at 2× slippage) the monthly optimizer book was chosen.

## Validation, 2017-01-03 to 2023-11-08 (one run, `momentum_val_monthly`)

| Bar set in advance | Result | |
|---|---|---|
| Sharpe at 1× at least 0.5 | **0.25** | failed |
| Return a year at 2× above zero | +2.2% | passed |
| Worst drawdown at most 25% | **−33.6%** | failed |

Total +22.3% in under seven years (+$5,583), almost all of it in 2022 (+29.9%). t-statistic 0.65.

## Does the engine behave as it should? Yes.

| Expectation written beforehand | What happened |
|---|---|
| A sharp loss in 2009 (the momentum crash) | 2009: −37.7% (monthly), −61.5% (textbook book) |
| Good years when trends persist | 2007: +51.7%; 2015: +26.2%; 2022: +29.9% |
| Weak overall in large US stocks after 2000 | Sharpe about 0.2 in both periods |
| More trading costs more | Weekly rebalancing cost $8,600 against $6,000 monthly and earned less |
| The optimizer tames the textbook book | Volatility 17% against 30%; drawdown −60% against −75% |

Other checks: 146 rebalances with no failed optimization; 31 lookahead replays passed; the books
held about 28 names a side; average gross exposure 1.34 of equity.

## What the runs showed about the platform

- **Exposure drifts between rebalances.** Gross exposure reached 1.88 of equity in the monthly
  book and 3.23 in the textbook book during the 2009 crash, above the 1.5 limit. A real account
  would have had a margin call. The engine now has an optional early rebalance
  (`rebalance_if_gross_above`); it was off in these runs and is not yet tested on a strategy.
- **Costs on a $25,000 account:** about 21 bps of every dollar traded (10 bps modelled auction
  slippage, the rest commission minimums and fees), plus about $190 a year to borrow shorts.
- **Data problems found and fixed on the way** (docs/data/DATA_NOTES.md): dividend amounts were
  on the wrong share basis; some split dates were days off; spinoffs were missing.

## Trials

4 counted runs in family `momentum_12_1`. No further variants are planned.
