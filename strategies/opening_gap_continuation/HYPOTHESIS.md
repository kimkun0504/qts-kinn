# Opening gap continuation

Preregistered by GPT on 2026-11-15. New family `opening_gap_continuation`, with zero prior
trials for this signal. The hypothesis is that a large positive overnight repricing followed
by further buying through the opening rotation can leave demand to be executed later that
session. The price and turnover conditions are proxies for that demand. Opening overreaction
and sellers taking advantage of the initial move could instead make the trade lose.

## Frozen definition

- Universe: Kinn's listed domestic common stocks, including names that subsequently delist.
  Use the split-adjusted prior close of at least $5, trailing median daily dollar volume of
  at least $2 million, and at least 20 prior sessions. Use the pre-open panel for membership.
- At 09:45 ET, require a bar starting at 09:30 and one starting at 09:44. The 09:30 open must
  be 5% to 25% above the prior close, inclusive. The 09:44 bar must close at least 1% above the
  09:30 open. Approximate turnover (sum of minute close times volume) from 09:30 through
  09:44 inclusive must be at least $100,000. Each symbol can signal once a day.
- Buy at market in the 09:45 bar, with any unfilled quantity expiring after that bar. Start
  liquidating at market five minutes before the exchange session closes, with Kinn's closing
  auction or forced exit fallback. All positions end on the entry date. Use no stops or targets.
- Use $20,000 equity and buying power, $2,000 target per position, at most ten simultaneous
  reservations, 5% bar participation and `ibkr_pro_tiered`. Kinn sizes whole shares using
  the signal close. When buying power is scarce, Kinn's equal-weight tie-break is symbol order.

## Runs and selection

There is one signal variant and no parameter search. The only planned runs are listed below.

| Order | Config and mode | Period | Rule |
|---|---|---|---|
| 1 | `development --study` | 2003-09-10 to 2016-12-30 | First look, judged on `r_close` only. Develop if there are at least 250 measured events and mean net per event at 2× slippage is positive. Otherwise park and stop. |
| 2 | `development` backtest | 2003-09-10 to 2016-12-30 | Run only after a develop verdict, to measure portfolio fills, costs and risk. The sole registered variant is selected when the event study clears its gate. The development backtest cannot change that selection. |
| 3 | `validation` backtest | 2017-01-03 to 2023-11-08 | Run the selected variant exactly once with identical trading settings. |

The event study prices independent market-order events through the official close and can
enter on the first later print. It approximates both sides' costs from the entry bar. The
portfolio backtests apply expiry, position sizing, capital limits, participation and the
actual exit rule. Each completed run is a separate family trial. Read the development study
in the Workbench and record its develop or park decision before any portfolio backtest.

## Validation bars

Pass only with at least 250 completed trades, arithmetic mean net return per trade of at
least **+3.00%** at 1× slippage (the lower end of the owner's 3–4% target), daily net P&L
t-statistic of at least **2.0** at 1× and 2×, and worst end-of-day drawdown no larger than
**$8,000** at 1×. Use Kinn's daily t-statistic over all sessions including days without trades.
Report trade counts, mean returns, t-statistics, drawdowns, and annual results at both cost
levels. A miss parks the strategy. Annual results are descriptive. The holdout begins
2023-11-09 and is excluded from every phase.

## Risks

Minute opens and the participation model approximate a market fill. There are no quotes or
halt flags. The 2× case doubles modelled slippage on the same fills. Opening and closing
liquidity can differ sharply from the ADV-based spread assumption. The prior close can be
stale after a trading interruption, split records are imperfect, and common-stock labels
come from the latest Sharadar snapshot. A gap is a price observation rather than a verified
news timestamp. Results by year may reveal regime dependence, and the usual daily
t-statistic does not adjust for serial correlation.
