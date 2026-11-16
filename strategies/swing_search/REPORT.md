# Swing search: one rule survives, earnings drift in the smallest stocks

Plan and every dated change to it: [HYPOTHESIS.md](HYPOTHESIS.md). Written 2026-11-16.

## Result

One rule passed a test it could have failed. Everything else failed.

**Rule A.** When a company worth under $300M reports earnings, and by the close of the
session after the 8-K its two-day return is 15% or more on at least five times normal volume,
buy at the next open and sell at the close 15 sessions after the signal day.

| Period | What it is | Trades | Gross | Auction basis | Spread crossed | Spread doubled | Weekly t | Years positive |
|---|---|---|---|---|---|---|---|---|
| 2005–2009 | never read before the rule was fixed | 452 | 4.53% | **4.04%** | 2.92% | 1.43% | 4.42 | 5 of 5 |
| 2010–2022 | search years, where the rule was found | 1,144 | 3.44% | **2.92%** | 1.75% | 0.21% | 3.49 | 11 of 13 |
| 2023 to 13 Oct | the one check, read once | 68 | 5.36% | **4.81%** | 3.74% | 2.33% | 2.10 | 1 of 1 |

Figures are the mean return a trade. The four cost columns are explained under
[Costs](#costs-decide-how-much-of-it-is-kept).

The rule was written on the first day as one cell of family 2. It did not pass the search's
own test on the declared costs. It was picked out after 12,000 cells because it was the
largest effect that held in both halves of the search years, so the search years alone prove
nothing. The evidence is the two periods the choice did not use:

- **2005 to 2009** (test set before reading: 1% or more, weekly t of 2.5 or more, four years
  of five positive). It made 4.04% with a weekly t of 4.42 and every year positive, 2008
  included (+1.54%).
- **2023** (set before reading: above zero is "not contradicted", below −3% is
  "contradicted"). It made 4.81%. With 68 trades that is known only to about ±3%.

The holdout from 2023-11-09 is sealed and has not been touched.

## What a trade looks like

Across all 1,664 trades (auction basis): mean 3.30%, median 1.29%, and one trade swings by
23%. Half the trades lose.

| Worst 1% | Worst 5% | Lower quarter | Median | Upper quarter | Best 5% | Best 1% |
|---|---|---|---|---|---|---|
| −47% | −28% | −8% | +1% | +13% | +37% | +70% |

The profit is in the large winners: without the best 1% of trades the mean is 2.12%; without
the best 5% it is 0.17%. A year with few large winners loses (2011: −0.40%, 2022: −0.18%).

Companies under $50M lost 5.5% a trade (113 trades). I have not changed the rule for this,
because a cut chosen after seeing it would not be tested.

## Costs decide how much of it is kept

The effect is in stocks that trade under $1M a day (3.5% to 5.2% a trade), where the quoted
spread is about 1% a side. Above $1M a day it is 1.5% to 1.8%.

- **Auction basis** assumes the order joins the opening and closing auctions and pays
  commission plus 0.25% a side for its own effect on the price (0.10% above $1M a day). The
  allowance is my assumption, not a measurement.
- **Spread crossed** pays the modelled half-spread each way, as a market order would.
- **Spread doubled** is the search's declared cost, twice the modelled spread.

Two checks so far, both from minute bars:

- **The result does not rest on single prints.** Buying at the volume-weighted price of
  09:30 to 10:00 and selling at that of the last 30 minutes gives 3.90% (2005–2009), 2.77%
  (2010–2022) and 4.40% (2023) on the auction basis, against 4.04%, 2.92% and 4.81%.
- **There is room for a small order.** The median trade sees about $600,000 change hands in
  the first 30 minutes of the entry day, and $120,000 or more in nine trades of ten. A $2,000
  order is under 2% of that.

Not yet measured: what an on-open or on-close order actually pays. A sample of 150 trades
(300 tick windows) is planned in
`MarketData/processed/kinn/quotes_sample/swing_auction/windows.csv` for the owner to download.

## As a book of $20,000

Signals of 2005 to 2022, no leverage, a slot must be free at the open.

| Book | Costs | Profit a year | Of $20,000 | Sharpe | Worst drawdown | Losing years |
|---|---|---|---|---|---|---|
| 10 positions of $2,000 | auction basis | $4,314 | 21.6% | 0.87 | $10,723 | 3 of 18 |
| 10 positions of $2,000 | spread crossed | $2,683 | 13.4% | 0.55 | $11,721 | 6 of 18 |
| 10 positions of $2,000 | spread doubled | $535 | 2.7% | 0.11 | $20,217 | |
| 20 positions of $1,000 | auction basis | $2,768 | 13.8% | 0.94 | $6,076 | 1 of 18 |
| 20 positions of $1,000 | spread crossed | $1,746 | 8.7% | 0.59 | $7,237 | 4 of 18 |

The 10-position book skips 365 of 1,596 signals because earnings come in clusters; it earns
more a year and can lose half the account. The 20-position book takes nearly every signal
and is steadier, but most of its money sits idle between earnings seasons. In 2023 the
10-position book made $5,022 with the spread crossed.

This is a profitable rule with a weak risk profile: a Sharpe ratio under 1, about 90 trades
a year, and results that depend on a few large winners.

## What failed

| Tried | Cells | Outcome |
|---|---|---|
| Families 1–8: reversal, earnings drift, breakouts, pullbacks, volume shocks, yearly lows, short interest, fundamentals at earnings | 2,505 | None passes. Large returns sit in falls during sell-offs and are not steady |
| Families 10–15: market state, technical state (averages, strength index, overnight against daytime), calendar, fundamental state, 8-K items, industry | 7,299 | None passes. Single conditions beat other stocks by 0.5% to 1% over 15 sessions, less than the cost of the small stocks they are found in |
| The same cells on the auction basis | | One qualifies: pullbacks in small winners, 2.0% a trade. Not followed up |
| Combined model, stocks over $10M a day | 39 | Top pick 1.5% a trade in 2018–2022, −0.2% in 2014–2017, −3.0% in 2022. Top against bottom tenth: 0.7% |
| Combined model, stocks under $10M a day (scored 2014–2021) | 21 | Top tenth beats other small stocks by 0.5% over 10 sessions, steadily (excess t 7.7), which is 0.4% a trade on the auction basis. Top picks lost in 2021 |
| Family 17: earnings drift refined on 2010–2017, tested on 2018–2022 | 1,944 | Chosen cell made 2.00% (t 4.44) where chosen and 0.76% (t 0.34) where tested. Failed |
| Rule B: buy stocks down 20% in a market sell-off | 1 | 5.35% a trade in 2010–2022, −0.10% in 2005–2009 with 2008 at −1.09% on 3,307 trades. Failed |

About 11,800 cells in all.

## What is still open

- **The tick sample**, to replace the auction allowance with a measurement. Owner's download.
- **The holdout.** Rule A is not a Kinn strategy yet; it has to be written for the engine
  before the owner can run it on the sealed years. One run.
- **Idle money.** The rule uses about a third of the account on average. A second rule of
  the same kind would need its own test.

## Reproduce

```
uv run python research/claude/swing_wide.py            # the table, 2010 on
uv run python research/claude/swing_wide.py --early    # 2005 to 2009
uv run python research/claude/swing_search.py prep
uv run python research/claude/swing_search.py family 2 --basis auction --sort auct
uv run python research/claude/swing_early.py A early   # or search, check; B likewise
uv run python research/claude/swing_reprice.py A early
uv run python research/claude/swing_book.py A early search 10 20
uv run --with lightgbm python research/claude/swing_model.py fit --small --no-market --name small
```
