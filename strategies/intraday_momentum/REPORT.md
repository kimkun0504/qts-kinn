# Intraday momentum and VWAP

**Verdict so far (development, 2003-09-10 to 2016-12-30): by the bars set in advance nothing
passes, because every result is negative at 10 basis points of slippage a side. One rule has a
real return before slippage: the opening range breakout on stocks in play, best with a VWAP
or moving-average exit. It breaks even at 6 to 9 basis points a side, so its real fills are
being measured before anything is built. VWAP trend and moving-average rules on QQQ and SPY do
not work.**

Plan: [HYPOTHESIS.md](HYPOTHESIS.md). Code: `research/claude/momentum_data.py`,
`momentum_study.py`. 111 rules measured, counted against the family. No validation or holdout
data.

## A. Opening range breakout on stocks in play

$4,000 a position, up to 20 at once on a $20,000 account. 52,386 trades, about 16 a session,
median stock $34, median stop 0.32% of the price.

| | Sharpe at 0 / 5 / 10 bp a side | Profit a year at 5 bp | Years positive at 5 bp | Worst drawdown at 5 bp | Breaks even at |
|---|---|---|---|---|---|
| A1 as published (fixed stop, long and short) | 4.3 / 1.15 / −2.0 | $5,675 | 11 of 14 | −$18,236 | 6.8 bp |
| A2 long side only | 2.7 / 0.47 / −1.8 | $1,615 | 10 of 14 | −$11,601 | 6.0 bp |
| A3 15-minute range | — / −0.27 / −3.4 | −$1,267 | 6 of 14 | −$28,709 | |
| A4 VWAP exit | 5.3 / 2.30 / −0.7 | $12,152 | 14 of 14 | −$5,020 | 8.9 bp |
| A5 exit on 1-minute EMA 9 | 7.2 / 2.64 / −1.9 | $9,048 | 14 of 14 | −$3,297 | 7.9 bp |
| A6 exit on 1-minute EMA 20 | — / 2.15 / −1.6 | $9,034 | 13 of 14 | −$6,449 | |
| A7 exit on 1-minute SMA 20 | — / 2.37 / −1.7 | $9,217 | 13 of 14 | −$4,631 | |
| A8 exit on 5-minute EMA 9 | — / 1.78 / −1.6 | $8,316 | 13 of 14 | −$11,329 | |
| A9 exit on 5-minute EMA 20 | 4.9 / 1.88 / −1.1 | $9,824 | 13 of 14 | −$9,804 | 8.1 bp |

- **The published result replicates before slippage.** With commissions only, as in the paper,
  A1 has a Sharpe of 4.3 on years that come before the paper's own sample. The gross return is
  +0.17% of the position a trade (0.44 of the amount risked); 18% of trades win.
- **It is a thin edge on many trades.** About 3,900 trades a year earn $4 to $7 each before
  slippage. Two or three cents a share each way decides everything.
- **A VWAP or moving-average exit beats the fixed stop.** Win rate rises from 18% to about 40%
  and the drawdown falls by two thirds. The exits are close to each other; none stands out
  enough to prefer on this evidence.
- **Long only** (what the engine can do today, and free of borrow problems): A4 long only has
  a Sharpe of 1.95 at 3 bp, 1.11 at 5 bp, and breaks even at 7.6 bp.
- **What flatters these numbers.** Fills are at the stop price; a real stop order fills after
  the trigger. Bars cannot see a stop touched inside the entry bar. Short-sale availability is
  ignored. The 5 bp was a guess.

## B, C and D on QQQ and SPY

One $20,000 position, flat at the close. Sharpe before costs / at half a cent a share / at one
cent a share:

| | QQQ | SPY |
|---|---|---|
| B VWAP trend, long and short | −3.0 / −6.8 / −9.5 | −1.2 / −3.4 / −5.3 |
| B VWAP trend, long only | −2.0 / −5.2 / −7.8 | −0.7 / −2.3 / −3.8 |
| C noise-area momentum | 0.37 / −0.16 / −0.68 | 1.01 / 0.77 / 0.54 |

- **B loses before any cost** in 2003 to 2016, on about 19 orders a day. The published result
  (2018 to 2023) does not hold out of its sample.
- **C on SPY is real but small:** $824 a year at one cent a share, 9 of 14 years, drawdown
  $2,450. Under the bar (Sharpe 1.0, $2,000 a year).
- **D, moving averages (96 variants):** 19 are positive before costs, 1 at one cent a share
  (Sharpe 0.01). One-minute rules place about 80 orders a day and lose heavily. The best are
  5-minute 20/50 crossovers on SPY, long only: Sharpe about 0.5 before costs, zero after. None
  is near the bar of 1.5.

## Against the bars

| Bar (at 2×, which is 10 bp a side for A) | Best A | Best ETF rule |
|---|---|---|
| Sharpe at least 1.0 (1.5 for D) | −0.7 | 0.54 |
| Positive in 11 of 14 years | 3 | 9 |
| Drawdown under $10,000 | −$53,213 | −$2,450 |
| At least $2,000 a year | −$3,521 | $824 |

Nothing passes. For A the 10 bp level is an assumption like the 5 bp one; the measured figure
replaces both (HYPOTHESIS.md, addendum of 01:10 ET). 630 trades have been drawn for it.
