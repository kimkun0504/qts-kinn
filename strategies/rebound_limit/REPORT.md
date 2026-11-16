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
  limit or stayed far from it had no print at or below it (480 sampled).
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

## Deeper limits and ladders, 2026-11-15 (plan in HYPOTHESIS.md, addendum of 20:30 ET)

**Verdict: a ladder of three limits (4%, 6% and 8% below) was chosen on development and passed
its one validation run on all three of the owner's targets. It earns more per trade than `x_o4`
with half the drawdown and less total profit, because it puts less money to work. It is a
candidate for paper trading once its own fill check is run.**

Twelve variants on the development period (2003–2016), sweep `20261116T013106Z_rebound_limit_12`.
No order under $1 in any of them. `_m`: market cap under $300M only. For ladders each filled
rung is a trade. Net per trade, t, Sharpe, total and drawdown are at 2× slippage.

| Variant | Trades | Net/trade | t | Sharpe | Total net | Worst drawdown | Eligible |
|---|---|---|---|---|---|---|---|
| `s_o4` (4% below) | 3,136 | +1.28% | 4.67 | 1.28 | $63,460 | −$6,105 | yes |
| `s_o5` | 2,132 | +1.64% | 4.71 | 1.29 | $56,822 | −$5,241 | yes |
| `s_o6` | 1,528 | +2.12% | 4.90 | 1.34 | $53,498 | −$4,337 | yes |
| `s_o8` | 828 | +2.54% | 3.66 | 1.00 | $32,929 | −$5,218 | no (trades) |
| `s_l48` (half at 4%, half at 8%) | 4,049 | +1.60% | 5.07 | 1.39 | $57,191 | −$3,659 | yes |
| **`s_l468` (thirds at 4%, 6%, 8%)** | 5,653 | +1.74% | **5.30** | 1.45 | $60,201 | −$3,661 | yes, chosen |
| `s_o4_m` | 1,952 | +1.21% | 3.35 | 0.92 | $32,123 | −$7,012 | yes |
| `s_o5_m` | 1,313 | +1.44% | 2.89 | 0.79 | $24,753 | −$7,510 | yes |
| `s_o6_m` | 949 | +1.70% | 2.79 | 0.77 | $22,588 | −$8,092 | no (trades) |
| `s_o8_m` | 521 | +1.98% | 1.84 | 0.50 | $12,084 | −$4,144 | no (trades) |
| `s_l48_m` | 2,514 | +1.30% | 3.37 | 0.92 | $26,793 | −$5,094 | yes |
| `s_l468_m` | 3,493 | +1.40% | 3.51 | 0.96 | $28,913 | −$5,333 | yes |

- **Deeper still pays more per trade** (4%, 5%, 6%, 8%: +1.28%, +1.64%, +2.12%, +2.54%) and
  fills less often, so total profit falls. The best single limit by the rule is 6%.
- **A ladder beats any single limit:** it takes the frequent 4% fills at a third of the size and
  adds to the position only when the price falls further. The losing years 2012–2015 come out
  flat (−$492, −$365, +$84, −$331) where `x_o4` lost $4,713 in 2013–2015.
- **Under-$300M only is worse than all stocks in development** in every pairing: about half the
  profit, a Sharpe under 1, a larger drawdown. Development gives no reason to drop larger stocks.
- **No order under $1** cost nothing: `s_o4` earns +1.28% a trade against `x_o4`'s +1.24%.

**Validation, one run** (`20261116T014043Z_claude_rebound_limit_437947d4`, 2017-01-03 to
2023-11-08, `s_l468`):

| Bar set in advance (the owner's targets) | Result | |
|---|---|---|
| Net per trade at 2× at least +1.0% | **+1.56%** | passed |
| Sharpe at 2× above 1 | **1.37** (1.46 at 1×) | passed |
| Worst drawdown at 2× under $10,000 | **−$4,485** (−$3,978 at 1×) | passed |

3,001 rung trades from 1,852 events (1,084 filled one rung, 387 two, 381 all three); total net
+$31,160 at 1×, +$29,201 at 2×; daily-P&L t-statistic 3.59 at 2×; 61% winners.

| Year | Trades | Net/trade 1× | Net $ | `x_o4` net $ |
|---|---|---|---|---|
| 2017 | 254 | +1.67% | +$2,665 | +$3,454 |
| 2018 | 461 | +2.07% | +$5,999 | +$9,387 |
| 2019 | 345 | +1.43% | +$3,340 | +$6,368 |
| 2020 | 714 | +3.98% | +$17,729 | +$19,050 |
| 2021 | 383 | +1.16% | +$2,717 | +$4,311 |
| 2022 | 523 | −0.19% | −$884 | −$5,997 |
| 2023 | 321 | −0.26% | −$406 | +$1,560 |

Against `x_o4` on the same years: total +$31,160 against +$38,133; worst drawdown $3,978
against $8,925; Sharpe 1.46 against 1.43. The ladder invests $1,037 an event on average against
about $1,800.

**What to hold against this result**

1. **Fifth use of the validation years** in this family, which the registry now puts at 65
   trials (62 by claude, 3 by Astra's rebound strategies). The Workbench's figures for the
   family: deflated Sharpe 0.98, probability of backtest overfitting 0.34.
2. **One year carries it.** 2020 made $17,729 of the $31,160. 2022 and 2023 both lost a little.
   The edge is still absent in some years; the ladder makes those years cheap, not profitable.
3. **In validation the profit is again micro-caps:** under $300M +2.45% a trade at 2× and
   $27,023; $300M–$2B +0.63% and $4,568; over $2B +0.28% and $495. In development the
   under-$300M versions were the weaker ones. The periods still disagree.
4. **Its fills are checked only in preview.** The ticks downloaded for `x_o4` cover 96% of the
   ladder's validation rung trades (`research/claude/ladder_fill_preview.py`): 100% confirmed,
   98% in full size, +1.33% simulated against +1.30% real at 2×, 96% of the net kept (82% with
   30 seconds of latency). The 4% of rung trades without ticks are events `x_o4` had no capital
   for, on the busiest days, and they earn more than average. The registered check needs the
   order listing to handle ladders and a small extra download.
5. **The exit is still modelled** (closing auction, 10 bps), not measured.

**Next, in order:** the registered fill check for `s_l468`; then paper trading, with orders in
the book within seconds of the bar. The holdout stays sealed.

## Fill check for the ladder, 2026-11-15 (plan in HYPOTHESIS.md, addendum of 21:05 ET)

**Verdict: passed all four pre-set bars. `s_l468` now meets every one of the owner's targets:
+1.56% a trade at 2×, Sharpe 1.37 at 2×, worst drawdown $4,485, and fills confirmed against
real trades.** Run `20261116T022546Z_claude_rebound_limit_6ab9ac2c`. The order listing rebuilt
both runs exactly (139,441 and 180,869 rung orders; all 8,654 filled rungs). Ticks: 5,085
windows already downloaded for `x_o4` and 818 new ones (owner download, plan `fillcheck_s_l468`).

| Bar set in advance | Result | |
|---|---|---|
| Tick data for at least 95% of traded rungs | 99.97% (3 of 8,654 had no prints) | passed |
| At least 97% confirmed by a real trade below the limit, each period | 100%, 100% | passed |
| Validation net per trade at 2×, cut to real size, 5 s latency: at least +1.0% | **+1.53%** (simulated +1.55%) | passed |
| Keeps at least 80% of the simulated net at 2×, each period | 97% validation, 96% development | passed |

| | Val rungs | Filled in full | Net/trade 2×: simulated → real | Kept | Dev rungs | Filled in full | Net/trade 2×: simulated → real | Kept |
|---|---|---|---|---|---|---|---|---|
| 4% rung | 1,852 | 98.5% | +1.45% → +1.43% | 97% | 3,359 | 98.3% | +1.43% → +1.38% | 96% |
| 6% rung | 768 | 98.2% | +1.85% → +1.82% | 98% | 1,500 | 98.3% | +2.06% → +2.01% | 96% |
| 8% rung | 381 | 98.4% | +1.45% → +1.39% | 96% | 794 | 98.1% | +2.41% → +2.42% | 99% |
| Under $300M | 1,656 | 97.6% | +2.45% → +2.42% | 97% | 3,256 | 97.6% | +1.35% → +1.30% | 94% |
| $300M–$2B | 1,091 | 99.4% | +0.62% → +0.61% | 97% | 1,869 | 99.2% | +1.88% → +1.85% | 98% |
| Over $2B | 233 | 99.6% | +0.25% → +0.25% | 88% | 454 | 99.6% | +4.43% → +4.38% | 98% |
| All | 3,001 | 98.4% | +1.55% → +1.53% | 97% | 5,653 | 98.2% | +1.74% → +1.69% | 96% |

- The deeper rungs are as real as the 4% rung. Each rung is a third of the position, so the
  median rung had over 140 times its size trade below the limit.
- Latency, validation: order in the book 0, 5, 30 seconds after the bar gives +1.55%, +1.53%,
  +1.36% a trade and $28,900, $28,240, $24,825. Thirty seconds late keeps 85%; the single 4%
  limit kept 82%.
- Touched-only orders (refused by the bar rule): 97–98% printed at the limit, 85% in full size;
  a fill there would have earned about +5.1% at 2× in both periods.

Still not covered: the exit in the closing auction (modelled at 10 bps).

## The prior-trend filter, 2026-11-15 (plan in HYPOTHESIS.md, addendum of 21:22 ET)

**Verdict: rejected. The filter looked strong in development and failed validation. `s_l468`
without it stays the candidate.**

The rule: take the event only if the stock's return over the 60 sessions before the day
(`ret60_prev`, new in build `447e58e098`) is zero or more. Figures at 2× slippage.

| | Trades | Net/trade | Sharpe | Total net | Worst drawdown | 2022 (1×) |
|---|---|---|---|---|---|---|
| Development: `s_l468` (no filter) | 5,653 | +1.74% | 1.45 | $60,201 | −$3,661 | |
| Development: **`t_l468`** (filter) | 2,248 | +2.64% | **1.64** | $37,118 | −$1,682 | |
| Development: `t_o4` (4% limit, filter) | 1,319 | +2.26% | 1.77 | $52,580 | −$2,389 | |
| Validation: `s_l468` (no filter) | 3,001 | +1.56% | 1.37 | $29,201 | −$4,485 | −$884 |
| Validation: **`t_l468`** (filter) | 1,505 | +1.22% | **0.94** | $11,818 | −$4,913 | −$2,641 |

- **Development** (sweep `20261116T022246Z_rebound_limit_2`): every one of the 14 years was
  profitable with the filter, and the gate (Sharpe above 1.45) was passed.
- **Validation, one run** (`20261116T022925Z_claude_rebound_limit_0976d236`): net per trade
  +1.22% (bar +1.0%, passed), **Sharpe 0.94 (bar: above 1, failed)**, drawdown $4,913 (passed).
  It also fails both conditions for replacing `s_l468`: lower Sharpe, and 40% of its profit.
- **What happened:** in 2017–2023 the stocks the filter removes were the profitable ones. The
  ladder made $31,160 with them and $12,811 without. The pattern that held in all 14
  development years did not carry over.
- This is the result the plan warned about: the rule was found by inspecting development
  trades after seeing which years lost, and development flattered it.

The `min_ret60` setting and the `ret60_prev` column stay in the code and the build; nothing
uses them. Using a different threshold or window now would be fitting to the validation years.

The family now carries 69 trials (66 by claude, 3 by Astra) and the validation years have been
used six times.

## Where `rebound_limit` stands, 2026-11-15

**Candidate for paper trading: `s_l468`.** A third of a $2,000 position each at 4%, 6% and 8%
below the event bar's close, resting 10 minutes, no order under $1, all market caps, sold in
the closing auction.

| Owner's target | Validation 2017–2023 | Checked how |
|---|---|---|
| Net per trade at 2× at least +1.0% | +1.56% (+1.53% on real fills) | one validation run; fill check |
| Sharpe above 1 | 1.37 at 2× | one validation run |
| Worst drawdown under half the account | $4,485 of $20,000 | one validation run |
| Fills confirmed against real trades | 100% confirmed, 98% in full size | registered fill check |

What it still rests on: one strong year (2020) for more than half the validation profit;
micro-caps for most of it; a modelled exit; orders placed within seconds of the bar; and
validation years that have been looked at six times. The holdout has not been touched and is
the one clean test left.

## The holdout, 2026-11-15 (plan in HYPOTHESIS.md, holdout addendum and the two after it)

**Failed. `rebound_limit` is parked.** One run of `s_l468` exactly as validated, on
2023-11-09 to 2026-11-06, run by the owner (`20261116T042612Z_human_rebound_limit_2fae870b`,
unsealed build `bc35c2693c`, commit `694b2d5`). The rule was written before the run: net per
trade at or below zero at 2× slippage is a fail, with no change and no re-test.

| At 2× slippage | Validation 2017–2023 | Holdout 2023-11 to 2026-11 | Target |
|---|---|---|---|
| Net per trade | +1.56% | **−0.86%** | at least +1.0% |
| Sharpe | 1.37 | **−1.04** | above 1 |
| Worst drawdown | $4,485 | **$9,392** | under $10,000 |
| Total net | +$29,201 | **−$8,842** | |
| Trades | 3,001 | 1,368 | |

Before the run, the unsealed data was checked against the research data on every earlier date
(equal apart from rounding and three named vendor cases), and the validation run was
reproduced through it trade for trade. The mechanics in the holdout match validation: 79
orders a session against 81, the same position size ($631 against $640) and the same costs
(0.37% to 0.41% of the position). Nothing points to a data or engine fault.

Gross return per trade by year, validation then holdout: 2017 +2.0%, 2018 +2.4%, 2019 +1.8%,
2020 +4.4%, 2021 +1.5%, 2022 +0.2%, 2023 (to the seal) +0.1% | late 2023 −1.4%, 2024 +0.1%,
2025 +0.8%, 2026 −2.1%. The edge had gone by 2022; the two weak years at the end of
validation were the signal, and 2020 hid them in the totals. The losing tail also grew: the
worst 5% of trades lost 22.6% or more against 17.0%, and the worst single trade 81% against
51%. All three rungs lost.

What this says about the process, not the strategy:

- The validation years were looked at six times, and the candidate was the best of twelve
  variants in development. A Sharpe of 1.37 after that much choosing was worth less than it
  looked.
- More than half the validation profit came from one year. A result that needs one year
  should have been held to a bar on the other years too.
- The fill check was right about fills and said nothing about whether the rebound still
  existed.

These breakdowns are a record of the failure. They are holdout results and must not be used to
design another variant of this family: the holdout is spent for `intraday_rebound`.

## Reversal confirmation, 2026-11-16 (plan in HYPOTHESIS.md, addendum of 2026-11-15 23:50 ET)

**Verdict: no reversal signal passed, and none beat buying without one. Every exit rule was
worse than holding to the close. One condition on the fall itself, its speed, carries a real
effect; whether it can be traded depends on a cost that has not been measured.**

Development years only (2003-09-10 to 2016-12-30), 61,387 events, one-minute bars with trade
counts (`research/claude/reversal_events.py`, `reversal_study.py`). Buys are at the open of the
bar after the signal. Net is gross minus an assumed 1.0% round trip. No holdout data.

| Entry, sold at the close | Trades | Gross per trade | Net | t (daily) | Years positive |
|---|---|---|---|---|---|
| E0 no signal, buy after the event bar | 61,379 | +0.80% | −0.20% | 2.5 | 7 of 14 |
| E2 climax bar that closes strong | 8,073 | +0.89% | −0.11% | 0.2 | 6 of 14 |
| E3 higher low, then break of the bounce high | 44,875 | +0.52% | −0.48% | −5.0 | 3 of 14 |
| E4 close above the last 5 highs | 59,748 | +0.62% | −0.38% | −4.0 | 3 of 14 |
| E5 estimated buying takes over | 49,529 | +0.62% | −0.38% | −3.2 | 4 of 14 |
| E6 back above the average price since the event | 48,067 | +0.52% | −0.48% | −3.4 | 4 of 14 |
| E7 buy 30 minutes before the close | 27,922 | −0.06% | −1.06% | −22.9 | 0 of 14 |

- **Waiting for confirmation costs more than it saves.** Each signal buys later and higher,
  and the stocks that trigger it do no better afterwards than the ones that do not.
- **Exits.** On E0, a stop under the low, a trailing stop, an average-price stop and a
  30-minute failed-bounce rule gave +0.39%, +0.39%, +0.28% and +0.63% gross against +0.80% at
  the close. The same on every other entry. A one-minute stop in a stock that has just fallen
  10% is hit by noise; this repeats the earlier result on fixed stops.
- **Speed of the fall is what separates the events.** Gross return to the close by how far the
  stock fell in the 15 minutes before the event: 10% or more +3.0%; 7 to 10% +2.0%; 5 to 7%
  +1.65%; 3 to 5% +1.0%; under 3% +0.09%. Three quarters of events are slow falls with no
  rebound in them.
- **Fast falls (5% or more in 15 minutes), no signal:** 13,745 trades, gross +2.02%, median
  +2.3%, positive gross in all 14 years, similar under $300M and over $2B, under $2 and over
  $20. Net +1.02% at the assumed cost, t 5.5. **Without the flash crash of 2010-05-06 (457
  trades at +8.2%) it is +1.81% gross, +0.81% net**, which is under the 1.0% bar.
- **Other splits:** market direction, trade size and time of day did not separate events
  reliably across years.

Against the bars set before the study: no signal met any of them. The fast-fall condition was
registered as a split, not as a candidate, and clears the 1.0% net bar only with one
exceptional day, so it does not go forward under this plan.

What the fast-fall result is and is not. The speed filter was tried at the start with a resting
order at the event bar's close and earned little (`fast_o0`, +0.62%, t 2.1). The difference
here is buying at once: a resting order at the close fills only when the stock comes back
down, and misses the ones that bounce straight away. So the return belongs to whoever buys in
the first seconds after a fast flush, and the price paid then (the ask, in a stock whose book
has just been emptied) is the whole question. The 1.0% cost here is an assumption.

Trials: 35 entry and exit combinations, 63 context cells and about a dozen further cuts
(years, size, price, speed buckets). `prior_trials` rises from 9 to 107.
