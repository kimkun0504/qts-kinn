# Report: rebound with a limit-order entry

2026-11-15, claude. Plan, variants and rules: [HYPOTHESIS.md](HYPOTHESIS.md). Account $20,000,
positions $2,000, costs IBKR Pro tiered, exit in the closing auction.

## Verdict

**Worth developing, not ready to trade.** The variant chosen on 2003–2016 by the pre-set rule
passed its one validation run on 2017–2023: **+0.52% net per trade** at 1× slippage (bar: +0.5%),
daily-P&L t-statistic **2.62** (bar: 2), and **+0.41%** at 2× slippage (bar: positive). Two things
stop it there: **2022 and 2023 both lost money**, and the worst drawdown was **$20,763, more than
the whole $20,000 account**.

It is not a 3–4% a trade strategy. It is a +0.4% to +0.6% a trade strategy that trades about 2.6
times a day.

## The chosen variant: `base_o2`

After a stock's first close 10% below the prior close (no news, no gap-down open), rest a buy
limit **2% below that bar's close** for 10 minutes; if filled, sell in the closing auction.

| | Development 2003–2016 | Validation 2017–2023 |
|---|---|---|
| Run | `…202957Z_claude_rebound_limit_…` (`base_o2`) | `20261115T204157Z_claude_rebound_limit_9aa5ff68` |
| Trades | 7,269 | 4,490 |
| Gross per trade | +1.00% | +0.86% |
| Net per trade, 1× slippage | +0.66% | **+0.52%** |
| Net per trade, 2× slippage | +0.56% | **+0.41%** |
| t-statistic of daily P&L, 1× / 2× | 3.65 / 2.93 | **2.62 / 2.02** |
| Total net, 1× | +$65,939 | +$34,346 |
| Worst drawdown | −$10,467 | **−$20,763** |
| Sharpe, daily | | 1.00 |

Validation by year (net per trade at 1×, total):

| 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| +1.25%, +$8,207 | +0.96%, +$9,134 | +0.99%, +$7,793 | +1.37%, +$19,378 | +0.52%, +$5,843 | **−0.85%, −$14,500** | **−0.24%, −$1,509** |

In validation, of 47,655 signals 30,356 never filled, 12,809 were refused for lack of capital and
4,490 traded. Round-trip costs were 32 bps of notional (commission 18, fees 4, slippage 10).

## What the development sweep showed (2003–2016, 17 variants)

| Variant | Trades | Net 1× | Net 2× | t at 2× |
|---|---|---|---|---|
| `base_o2` (limit 2% lower) | 7,269 | +0.66% | +0.56% | **2.93** |
| `deep15_o1` (15% drop, 1% lower) | 4,302 | +0.90% | +0.80% | 2.70 |
| `deep15_o0` | 6,102 | +0.61% | +0.51% | 2.23 |
| `fast_o0` (5% in 15 minutes) | 7,024 | +0.62% | +0.52% | 2.08 |
| `deep20_o1` (20% drop) | 1,760 | +1.41% | +1.31% | 1.96 |
| `base_o1` | 11,366 | +0.41% | +0.31% | 1.60 |
| `base_o0` (limit at the bar's close) | 17,781 | +0.26% | +0.16% | −0.02 |
| `liquid_o0` / `liquid_o1` (ADV ≥ $10M) | 6,605 / 3,665 | +0.11% / +0.31% | +0.01% / +0.21% | 0.00 / 0.99 |
| `calm_o0` / `calm_o1` (calm sessions) | 16,017 / 8,791 | +0.24% / +0.35% | +0.14% / +0.25% | −0.26 / 0.84 |
| `early_o0` / `early_o1` | 9,340 / 6,288 | +0.26% / +0.35% | +0.15% / +0.25% | −0.34 / 0.51 |
| `rest30_o1` | 13,823 | +0.31% | +0.21% | 0.60 |
| `calm_liquid_o1` | 2,035 | +0.01% | −0.09% | −0.46 |

(`deep20_o0` and `fast_o1` are in the run store; they sit between the rows above.)

- **Where the limit sits matters most.** Each step lower (at the close, 1% lower, 2% lower)
  raised the net per trade: +0.26%, +0.41%, +0.66%. Buying lower beats being filled more often.
- **Deeper drops pay more per trade** (20% drop: +1.41%) but are rarer.
- **The filters I expected to help did not.** Liquid-only and calm-session variants were worse
  than no filter. Selloff days are where much of the profit is, not where it is lost.

## Why not to trust it yet

1. **The last two years lost money.** 2022 was the worst year in either period. One explanation
   is a regime change (the old build also saw the effect fade after 2020); another is noise.
   The validation cannot tell them apart.
2. **Drawdown is larger than the account.** With ten $2,000 positions, a bad stretch of days
   loses most of $20,000. Sizing and a loss limit are not optional.
3. **29 trials are charged to this family**, 17 of them this sweep. The validation run is the
   honest number (one pre-chosen variant, run once), but its period was not untouched: the
   market-order event study had already shown per-year results for those years.
4. **Fills are from minute bars.** A fill needs the price to trade a tick below the limit, which
   is conservative, but the queue at that price is invisible. The tick sample's passive test
   (limit at the bid) filled 62% of the time and earned +0.56% a fill, which is consistent.
5. **Auction exits and capacity are modelled.** Mean position was $1,761 because of the 5%
   participation cap; larger size would fill less.

## Trial count

Family `intraday_rebound`: 9 earlier + market-order event study + tick study + 17 development
runs + 1 validation run = **29**. Seventeen first-attempt runs at the old sizing were abandoned
before producing results and are not counted.

## What would change the verdict

- **Toward trading:** a written risk rule (a daily loss limit and a cap on same-day positions)
  tested on development, then validation once; then paper trading. The holdout is the final test
  and works once: use it only for the frozen version.
- **Toward parking:** if 2022–2023 turns out to be the new normal. The cheapest evidence is the
  holdout itself (2023-11 onward), which would settle exactly that question.

## Risk rules, 2026-11-15 (plan in HYPOTHESIS.md, risk addendum)

**Verdict: the risk rules failed validation. No risk rule tested here controls the drawdown.**

Seven risk variants of `base_o2` on the development period (2003–2016), sweep
`20261115T212122Z_rebound_limit_7`; dollars on a $20,000 account with $2,000 positions.

| Variant | Trades | Net/trade 1× | Total net 2× | Worst drawdown 2× | Net ÷ drawdown | Qualifies (≥ $36,940) |
|---|---|---|---|---|---|---|
| `base_o2` (no rule) | 7,269 | +0.66% | $52,772 | −$11,853 | 4.45 | reference |
| `risk_cap5` | 6,069 | +0.56% | $32,444 | −$10,940 | 2.97 | no |
| `risk_loss300` | 6,945 | +0.58% | $42,154 | −$15,008 | 2.81 | yes |
| `risk_loss600` | 7,165 | +0.62% | $46,903 | −$13,897 | 3.38 | yes |
| `risk_cap5_loss600` | 6,036 | +0.56% | $31,717 | −$11,226 | 2.83 | no |
| `risk_all` | 5,896 | +0.59% | $34,448 | −$11,226 | 3.07 | no |
| `risk_brk4000` | 7,029 | +0.71% | $56,726 | −$9,432 | 6.01 | yes |
| **`risk_brk2000`** | 6,695 | +0.73% | $58,651 | −$9,683 | **6.06** | yes, chosen |

- The entry cap and the daily loss limit **made things worse**: they removed more profit than
  loss. Days with many events, and entries made while the session was already down, were on
  average good trades.
- Only the circuit breaker helped in development, and only modestly.

**Validation, one run** (`20261115T213340Z_claude_rebound_limit_7bab3754`, 2017-01-03 to
2023-11-08, `risk_brk2000`):

| Bar set in advance | Result | |
|---|---|---|
| Worst drawdown at 1× ≤ $8,000 | **−$20,158** | **failed** |
| Net per trade at 1× ≥ +0.4% | +0.53% (2×: +0.43%) | passed |
| Daily-P&L t-statistic at 1× ≥ 2 | 2.59 | passed |

4,172 trades, total net +$32,664; 110 sessions paused. 2022: −$12,787; 2023: −$3,919. Without the
rule the drawdown was −$20,763, so the breaker removed about $600 of it. The 2022–2023 loss was a
slow decline over many months, never steep enough inside 20 sessions to keep the breaker tripped.

**What this means.** The strategy's problem is not a few bad days that a stop can cut; it is that
the edge was absent or negative for two years. Further risk-rule tuning on this signal would be
fitting to 2022. The honest options are a smaller position size (drawdown scales with it), a
regime condition stated as a new hypothesis, or leaving the strategy as "developing, not tradable".

The family now carries 37 trials.

## Entry depth, exits and price, 2026-11-15 (plan in HYPOTHESIS.md, third addendum)

**Verdict: a deeper limit is a clear improvement and passed validation on all four bars. Every
exit other than the close made results worse. Still not ready to trade: the fills are simulated
from minute bars and need checking against real trades.**

Ten variants on the development period (2003–2016), sweep `20261115T232205Z_rebound_limit_10`,
data build `6453bd3ec8` (corrected dividends and split dates), $20,000 account, $2,000 positions.

| Variant | Trades | Net/trade 1× | Net/trade 2× | t at 2× | Total net 1× | Worst drawdown | Qualifies |
|---|---|---|---|---|---|---|---|
| `x_ref` (limit 2% below, hold to close) | 7,268 | +0.66% | +0.56% | 2.94 | $66,187 | −$10,467 | yes |
| `x_o3` (limit 3% below) | 4,786 | +0.96% | +0.86% | 4.05 | $72,176 | −$7,033 | yes |
| **`x_o4` (limit 4% below)** | 3,200 | **+1.34%** | **+1.24%** | **4.55** | $68,085 | −$5,561 | yes, chosen |
| `x_o3_tp5` (3% below, sell 5% up) | 4,998 | +0.63% | +0.59% | 3.98 | $50,241 | −$9,663 | yes |
| `x_p5` (stocks of $5 or more) | 4,831 | +0.66% | +0.56% | 2.49 | $46,496 | −$8,853 | yes |
| `x_tp5` (sell 5% up) | 7,813 | +0.46% | +0.41% | 3.22 | $52,495 | −$12,947 | no |
| `x_tp3` (sell 3% up) | 8,059 | +0.04% | +0.01% | −0.50 | −$1,875 | −$25,113 | no |
| `x_t120` (sell after 120 minutes) | 7,899 | +0.30% | +0.01% | −0.40 | $32,014 | −$20,550 | no |
| `x_t60` (sell after 60 minutes) | 8,230 | +0.05% | −0.27% | −3.35 | $184 | −$27,339 | no |
| `x_sl7` (stop 7% down) | 7,787 | +0.11% | −0.10% | −1.87 | $969 | −$34,510 | no |

- **The corrected data changed nothing here:** `x_ref` matches the earlier `base_o2` to the dollar
  level (7,268 trades against 7,269, +0.66% both).
- **Depth of the limit is the lever.** 0%, 1%, 2%, 3%, 4% below the event bar's close gave
  +0.26%, +0.41%, +0.66%, +0.96%, +1.34% net per trade. Fewer orders fill, at better prices, and
  the drawdown halves.
- **Exits:** the rebound takes the rest of the day. Selling early by the clock pays the spread
  for nothing; a stop sells exactly the trades that recover; a profit target caps the winners
  while the losers run to the close.
- **A minimum price of $5** lowers costs (19 bps a round trip against 32) but does not raise the
  return per trade.

**Validation, one run** (`20261115T233007Z_claude_rebound_limit_eec4a69e`, 2017-01-03 to
2023-11-08, `x_o4`):

| Bar set in advance | Result | |
|---|---|---|
| Net per trade at 1× at least +0.5% | **+1.30%** | passed |
| Daily-P&L t-statistic at 1× at least 2 | **3.74** | passed |
| Net per trade at 2× above zero | **+1.20%** | passed |
| Worst drawdown at 1× at most $10,000 | **−$8,925** | passed |

1,789 trades (about 260 a year), total net +$38,133 on $20,000, Sharpe 1.43, 61% winners.

| Year | Trades | Net/trade | Net $ |
|---|---|---|---|
| 2017 | 156 | +1.48% | +$3,454 |
| 2018 | 275 | +2.10% | +$9,387 |
| 2019 | 219 | +1.37% | +$6,368 |
| 2020 | 395 | +2.85% | +$19,050 |
| 2021 | 225 | +1.21% | +$4,311 |
| 2022 | 305 | −0.80% | −$5,997 |
| 2023 | 214 | +0.31% | +$1,560 |

**What to hold against this result**

1. **The fill rule is the weak point.** Under 5% of orders fill (1,789 of about 38,650 placed),
   and each fill is inferred from a minute bar trading at least one tick through the limit. A
   resting order 4% below a falling stock fills on the sharpest prints; whether those prints
   were real, sized trades has not been checked against tick data.
2. **The validation years have now been used three times** in this family (48 trials in all).
   The pass is real but weaker evidence than a first look.
3. **2022 still lost** (−$5,997) and 2013–2015 lost in development. The edge is absent in some
   years; the deeper limit shrinks the damage and does not remove it.
4. **The trend continued past the tested range** (4% was the deepest variant and the best). The
   tempting next step, 5% and 6%, is a new search and must be registered as one.

**Next, in order:** check 4%-below fills against real trades on a tick sample of the events that
filled; then paper trading with the daily loss limit left off (it hurt in testing) and a smaller
position; the holdout stays sealed until then.

## Where `x_o4`'s profit comes from, 2026-11-15 (existing runs, no new run)

Script: `research/claude/x_o4_breakdown.py`. Market cap and price are the previous session's.
Net per trade is at 2× slippage; totals are at 1× and add up to the runs' totals.

| Market cap | Dev trades | Dev net/trade | Dev total | Val trades | Val net/trade | Val total |
|---|---|---|---|---|---|---|
| Under $300M | 1,852 | +1.07% | +$29,462 | 1,003 | +1.94% | +$35,279 |
| $300M–$2B | 1,053 | +1.27% | +$24,927 | 631 | +0.34% | +$3,199 |
| Over $2B | 250 | +2.83% | +$14,431 | 143 | +0.30% | +$923 |
| Unknown | 45 | −1.60% | −$735 | 12 | −5.40% | −$1,268 |
| All | 3,200 | +1.24% | +$68,085 | 1,789 | +1.20% | +$38,133 |

| Previous close | Dev trades | Dev net/trade | Dev total | Val trades | Val net/trade | Val total |
|---|---|---|---|---|---|---|
| $1–2 | 482 | +0.54% | +$3,066 | 242 | +1.66% | +$7,909 |
| $2–5 | 898 | +1.73% | +$28,331 | 489 | +1.83% | +$17,060 |
| $5–10 | 702 | +1.34% | +$14,227 | 432 | +0.93% | +$6,595 |
| $10–20 | 636 | +0.88% | +$10,528 | 325 | +0.65% | +$3,029 |
| $20 and over | 482 | +1.34% | +$11,933 | 301 | +0.78% | +$3,540 |

- **Micro-caps are 58% and 56% of the trades.** There is no market-cap floor in the universe.
- **The periods disagree.** In development every size group cleared +1% and the largest stocks
  paid most. In validation the under-$300M group made 93% of the profit; above $300M the
  strategy earned +0.3% a trade (774 trades, +$4,122), which fails the owner's +1% bar.
- **So the validation pass rests on micro-cap fills.** Whether those fills are real is what the
  fill check decides (HYPOTHESIS.md, fill-check addendum; plan `fillcheck_x_o4`, 5,828 windows).
- Round-trip costs: 44 bps under $300M, 18 bps over $2B; 80 bps for $1–2 stocks.

## The losing development years, 2026-11-15

2013–2015 lost $4,713 in development. They were quiet years (few broad selloff days), and the
whole loss was in stocks that had already fallen over the previous 60 sessions (−$11,462 on 282
trades); stocks that had risen made +$6,750 on 221 trades and were profitable in all 14
development years. Tables, the hypothesis that follows and the reasons to distrust it are in
HYPOTHESIS.md (addendum of 20:10 ET). **Not tested on any period.**

## Fill check against real trades, 2026-11-15 (plan in HYPOTHESIS.md, addendum of 19:50 ET)

**Verdict: passed all four pre-set bars. The minute-bar fills of `x_o4` are real trades, in the
order's size, at $2,000 a position.** Run `20261116T012801Z_claude_rebound_limit_0e3f2a2d`
(`fill_check.md` there has every table); vendor trades and quotes for 5,828 order windows
(owner download, plan `fillcheck_x_o4`); trade conditions from the vendor's own table.

| Bar set in advance | Result | |
|---|---|---|
| Tick data for at least 95% of traded orders | 99.9% (3 of 4,989 had no prints) | passed |
| At least 97% confirmed by a real trade below the limit, each period | 100%, 100% | passed |
| Validation net per trade at 2×, orders cut to real size, 5 s latency: at least +1.0% | **+1.17%** (simulated +1.19%) | passed |
| Keeps at least 80% of the simulated net at 2×, each period | 95% validation, 93% development | passed |

"Cut to real size": each order keeps the smaller of its simulated quantity and the shares that
printed at least a tick below the limit from 5 seconds after the event bar.

| | Val orders | Filled in full | Net/trade 2×: simulated → real | Kept | Dev orders | Filled in full | Net/trade 2×: simulated → real | Kept |
|---|---|---|---|---|---|---|---|---|
| Under $300M | 1,003 | 95.9% | +1.94% → +1.92% | 95% | 1,852 | 96.8% | +1.07% → +1.01% | 89% |
| $300M–$2B | 631 | 98.3% | +0.33% → +0.30% | 84% | 1,053 | 97.7% | +1.27% → +1.24% | 93% |
| Over $2B | 143 | 100% | +0.25% → +0.25% | 100% | 250 | 98.8% | +2.83% → +2.78% | 98% |
| All | 1,789 | 97.1% | +1.19% → +1.17% | 95% | 3,200 | 97.2% | +1.24% → +1.19% | 93% |

- **The price traded through.** The national best bid fell below the limit in 99.7% of the
  validation fills and 97.6% of the development fills.
- **Latency costs money.** Order in the book 0, 5, 30 seconds after the bar: validation +1.19%,
  +1.17%, +1.01% a trade and $34,013, $32,870, $28,304; development +1.24%, +1.19%, +1.04% and
  $60,647, $57,971, $47,889. Thirty seconds late loses about a fifth of the profit.
- **The bar rule leaves out touches.** Of sampled orders where the low touched the limit without
  trading through, 97–98% did print at the limit (64–76% in the order's full size), and a fill
  there would have earned +4.89% (validation, 160 orders) and +3.48% (development, 190) at 2×.
  Live trading gets some of these; the backtest counts none. Orders that came within 1% of the
  limit or stayed far from it had no print at or below it (240 sampled).
- **2003–2006**, before the trade-through rules: 100% confirmed, 98% of the net kept.
- **Size.** Share of under-$300M orders whose through-volume covers a larger order: 2× the
  order 92–93%, 5× 83–86%, 10× 72–75%, 25× 46–51%. Median dollars traded below the limit:
  $42,000–53,000 (over $1 million above $2B).

**Micro-caps (rule set before the data):** not excluded (100% confirmed; 95% and 89% of the net
kept). Their fills are real at $2,000 and would thin out by $10,000 a position. The two periods
disagree on whether they are the best size group or the worst, so market cap enters the next
search as a variant.

**Not covered by this check:** the exit. Selling in the closing auction is modelled at 10 bps,
not measured, and matters most in the smallest names.

The family now carries 49 trials.
