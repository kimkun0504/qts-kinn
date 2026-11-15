# momentum_12_1: 12-month momentum, skipping the latest month

**Written 2026-11-15, before any run.** Family `momentum_12_1`. First alpha on the daily engine.

## Why this one

It is the most replicated published signal (Jegadeesh and Titman, 1993; Asness, Moskowitz and
Pedersen, 2013), it needs only prices, and its behaviour is well known. That makes it the right
first test of the daily engine: if the engine is correct, the results should look like the
literature, including the 2009 momentum crash. It is not chosen because I expect it to make
money on a $25,000 account.

## Signal

For each stock, the total return (dividends included) over sessions t-252 to t-22: twelve months,
skipping the latest month. At least 200 daily returns are required. Known before the open of t.

## Book

| Setting | Value |
|---|---|
| Account | $25,000, long and short |
| Universe | US common stocks: the 1,000 largest by the previous session's market cap among those with a previous close of at least $5, median daily dollar volume of at least $5 million and at least 273 prior sessions |
| Limits | 75% long and 75% short at most (gross 1.5); net within ±2%; at most 5% of the account per stock; portfolio beta within ±0.05; each sector within ±10% net |
| Shorts | market cap at least $1 billion; borrow fee 1% a year (an assumption: there is no borrow data) |
| Risk model | single-index, 252 sessions |
| Construction | mean-variance optimizer; information coefficient 0.03, risk aversion 10, horizon 21 sessions. These are fixed, not tuned |
| Execution | closing auction, sized before the open from the previous close |
| Costs | `ibkr_pro_tiered`, auction slippage 10 bps (1×) and 20 bps (2×) |

## Periods

- **Development:** 2004-10-01 to 2016-12-30 (the first year of data is history for the signal).
- **Validation:** 2017-01-03 to 2023-11-08, one run.
- The holdout (from 2023-11-09) is not touched.

## Variants on the development period (3)

| Config | Construction | Rebalance |
|---|---|---|
| `momentum_dev_monthly` | optimizer | first session of each month |
| `momentum_dev_weekly` | optimizer | first session of each week |
| `momentum_dev_ranked` | equal weight, best 15 long and worst 15 short (the textbook book) | monthly |

**Selection rule:** the highest Sharpe ratio at 2× slippage. If none is above zero, nothing is
validated and that is the finding.

## Validation bars (set now)

The chosen variant passes if, on 2017–2023: Sharpe at 1× slippage is at least **0.5**, the
annual return at 2× slippage is **above zero**, and the worst drawdown is at most **25%**.

## What I expect

- **Engine check:** the long side earns roughly what the market earns and the short side loses
  roughly that; 2009 shows a sharp loss (winners lag the rebound, losers surge).
- **As a strategy:** probably fails. Momentum in large US stocks has been weak since the early
  2000s, and a $25,000 account pays the $0.35 minimum commission on small orders.

Each of the three development runs and the validation run is a counted trial (4 in all).
