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

## Which stocks, and four positions at a time, 2026-11-16 (addendum of 01:40 ET)

**Verdict: choosing by relative volume does not concentrate the return, and holding only four
names halves the Sharpe. Share price matters for cost: the rule has the most room in $50 to
$100 stocks.** Same development trades, 34 more measurements (145 in the family).

Return per trade before slippage, VWAP exit (fixed stop in brackets):

| Relative volume rank | Trades | Gross per trade | Breaks even at |
|---|---|---|---|
| 1 to 4 | 10,379 | +0.24% (+0.15%) | 10.4 bp (6.0) |
| 5 to 10 | 15,689 | +0.22% (+0.18%) | 9.6 bp (7.5) |
| 11 to 20 | 26,318 | +0.19% (+0.16%) | 7.9 bp (6.7) |

- The most active four are a little better with the VWAP exit and no better with the fixed
  stop. Thresholds on relative volume (3, 5, 10 times normal) say the same.
- **Four positions:** the top four alone, at 5 bp, have a Sharpe of 1.2 against 2.3 for all
  twenty. The edge per trade is the same, so fewer trades only means more luck in each day.
  At $20,000 a position (four times the account) the worst drawdown is $23,000, more than the
  account.
- Long only is weaker in the top four (+0.16%, breaks even at 6.3 bp).

By share price, VWAP exit, with slippage in cents a share a side:

| Price | Trades | Gross per trade | Breaks even at | Sharpe at 1 / 2 / 3 cents |
|---|---|---|---|---|
| $5 to $20 | 11,370 | +0.36% | 1.9 cents | 1.35 / −0.16 / −1.67 |
| $20 to $50 | 27,230 | +0.18% | 2.5 cents | 2.45 / 0.77 / −0.90 |
| $50 to $100 | 11,804 | +0.14% | 3.8 cents | 1.86 / 1.19 / 0.51 |
| Over $100 | 1,953 | +0.06% | 2.7 cents | 0.25 / 0.11 / −0.04 |
| All | 52,386 | +0.21% | about 2.4 cents | 3.02 / 0.77 / −1.48 |

In cents the whole question is simple: at 1 cent a share each way the rule earns about
$15,900 a year on the account; at 2 cents about $4,100; at 3 cents it loses. The fill
measurement will say which.

## Three selectors, 2026-11-16 (addendum of 02:00 ET)

**Verdict: none clears the bar set in advance (twice the unchosen group in both halves). Two
are real improvements: a gap of 3% or more in the breakout's direction, and an earnings 8-K
since the prior session. The height of the opening range does nothing.** 24 more measurements
(169 in the family). Code: `research/claude/momentum_selectors.py`.

VWAP exit, $4,000 a position, slippage in cents a share each way:

| Group | Trades | Gross per trade | 2003–09 / 2010–16 | Breaks even at | Sharpe at 2 cents | Profit a year at 2 cents | Years positive |
|---|---|---|---|---|---|---|---|
| All trades | 52,386 | +0.21% | 0.23 / 0.19 | 2.3 | 0.77 | $4,057 | 10 of 14 |
| Gap with the breakout, 3% or more | 8,399 | +0.36% | 0.41 / 0.31 | 3.5 | 1.11 | $3,528 | 13 of 14 |
| Gap with, 1% or more | 18,015 | +0.24% | 0.28 / 0.22 | 2.6 | 0.74 | $2,752 | 12 of 14 |
| Flat open (under 1%) | 18,952 | +0.17% | 0.19 / 0.15 | 2.2 | 0.40 | $845 | 9 of 14 |
| Gap against, 1% or more | 15,419 | +0.20% | 0.21 / 0.19 | 2.1 | 0.16 | $461 | 8 of 14 |
| Earnings 8-K since the prior session | 4,803 | +0.30% | 0.35 / 0.26 | 3.6 | 1.03 | $1,729 | 13 of 14 |
| Any 8-K since the prior session | 9,784 | +0.26% | 0.30 / 0.22 | 2.9 | 0.89 | $2,122 | 12 of 14 |
| Narrow / middle / wide opening range | 17,462 each | 0.21 / 0.21 / 0.20 | | 2.3 to 2.4 | 0.64 / 0.48 / 0.36 | | |

- **Gap of 3% or more with the breakout:** 2.0 times the rest overall (+0.36% against +0.18%),
  2.2 times in 2003–2009 and 1.85 times in 2010–2016, so just short of the bar. It keeps most
  of the profit of the whole book on a sixth of the trades (about 2.5 a session) and has room
  for 3.5 cents of slippage instead of 2.3.
- **Earnings:** 1.5 times the rest, steady in both halves, about 360 trades a year. Filings
  dated the same morning are not counted, so this understates what a trader with a news feed
  would see.
- The fixed stop tells the same story at lower levels (gap 3%: +0.26%; earnings: +0.24%).
- Not tested: the two together, or any tuning of the 3%. Each would be another look at the
  same trades.

## Real fills, 2026-11-16 (addenda of 01:10 and 02:20 ET)

**Verdict: marginal, by the rule set before measuring (cost a side 7.9 bp; the line for
parking was 8, for going ahead 5). The price runs about 2 cents in the second after the
breakout, so the result depends on how fast the order arrives, and what profit survives is on
the short side, which is the hardest side to trade.**

Ticks for 630 development trades drawn at random (605 with a usable trigger; the trigger was
inside the entry bar in every one). Code: `research/claude/momentum_fill_cost.py`.

| | Mean | Median | In basis points |
|---|---|---|---|
| Entry, quote at the instant of the trigger, against the study's price | 1.9 cents | | 4 to 7 by price |
| Entry, quote one second later (the figure declared as the main one) | 3.8 cents | 2.0 cents | 10.5 |
| Half-spread during the next 20 minutes (the cost of a market exit) | 1.9 cents | 1.3 cents | 5.4 |
| **Cost a side** (mean of entry at one second and exit) | 2.9 cents | | **7.9** |
| Fixed stop, fill against the stop price | about 0 | | |

- Costs by price: $5–20, 11.1 bp a side; $20–50, 7.3; $50–100, 5.9; over $100, 9.4. By period:
  6.4 bp in 2003–2006 and 9.7 in 2013–2016. Later years cost more at one second, not less.
- The fixed stop was reached within 20 minutes in 65% of trades, and inside the entry bar,
  after the entry, in 12%. Bars cannot see those; the fixed-stop results above are too kind.

The development trades again with the measured costs (entry and exit basis points by price
bucket), VWAP exit, $4,000 a position:

| | Entry one second after the trigger | Entry at the trigger |
|---|---|---|
| All trades | Sharpe 0.60, $3,148 a year, 9 of 14 years | 2.21, $11,678, 14 of 14 |
| Long only | −0.09, −$331, 6 of 14 | 1.06, $3,984, 13 of 14 |
| Short only | 0.84, $3,479, 12 of 14 | 1.85, $7,694, 13 of 14 |
| Gap 3% or more with the breakout | 1.23, $3,925, 13 of 14 | 1.68, $5,347, 13 of 14 |
| Gap 3% or more, long only | 0.08, $161, 7 of 14 | 0.46, $918, 10 of 14 |
| Gap 3% or more, short only | 1.48, $3,764, 12 of 14 | 1.73, $4,429, 12 of 14 |

With the published fixed stop: −0.68 and −$3,329 a year at one second; 1.06 and $5,202 at the
trigger.

What this says:

- **Speed decides it.** A stop order resting at the broker fires within milliseconds and
  fills nearer the right-hand column. A program that reacts to a bar or a delayed feed fills
  nearer the left-hand one. Where a resting stop really lands between the two has not been
  measured.
- **The long side barely pays.** At one second it loses; at the trigger it makes about $4,000
  a year on the account.
- **The profit is in the shorts**, above all stocks that gap down 3% or more and then break
  their opening low. That side is flattered here: borrow cost and availability are ignored;
  before July 2007 a short could not be sold on a downtick at all; and since 2011 a stock
  down 10% on the day cannot be shorted at the bid. None of that is in these numbers.
- The gap selector was found after the first look, among several cuts; with the costs sample
  at 126 trades for it, its figures are the least certain in the table.
