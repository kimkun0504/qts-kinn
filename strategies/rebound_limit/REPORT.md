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
