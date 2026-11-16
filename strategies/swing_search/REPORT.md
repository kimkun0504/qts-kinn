# Swing search: one rule survives, earnings drift in the smallest stocks

Plan and every dated change to it: [HYPOTHESIS.md](HYPOTHESIS.md). Written 2026-11-16.

## Result

One rule passed tests it could have failed. Everything else failed.

**The rule (A50).** A company worth $50M to $300M reports earnings. If, by the close of the
session after the 8-K, its two-day return is 15% or more on at least five times normal
volume, buy at the next open and sell at the close 15 sessions after the signal day.

| Period | What it is | Trades | Gross | Auction basis | Spread crossed | Spread doubled | Weekly t | Years positive |
|---|---|---|---|---|---|---|---|---|
| 2005–2009 | test years | 428 | 4.97% | **4.49%** | 3.38% | 1.91% | 4.18 | 5 of 5 |
| 2010–2022 | search years | 1,060 | 4.11% | **3.60%** | 2.45% | 0.92% | 4.08 | 12 of 13 |
| 2023 to 13 Oct | check | 63 | 6.51% | **5.95%** | 4.88% | 3.46% | 2.07 | 1 of 1 |

Figures are the mean return a trade. The cost columns are explained under
[Costs](#costs-decide-how-much-of-it-is-kept). Over all 1,551 trades the mean is 3.94% on the
auction basis and 18 of 19 years are positive (2011: −0.4%).

## How it was found, and what counts as evidence

1. **Rule A** (the same rule without the $50M floor) was one cell of family 2, written on
   the first day. It did not pass the search's test on the declared costs. It was picked out
   after 12,000 cells because it was the largest effect that held in both halves of the
   search years. The search years therefore prove nothing by themselves.
2. **Rule A was fixed and run on 2005 to 2009,** which the search had not read. Test set
   beforehand: 1% or more, weekly t of 2.5 or more, four years of five positive. Result:
   452 trades, 4.04%, weekly t 4.42, five years of five (2008: +1.54%). **Passed.**
3. **Rule A was run once on 2023.** Set beforehand: above zero is "not contradicted", below
   −3% is "contradicted". Result: 68 trades, 4.81%. With so few trades that is known only to
   about ±3%.
4. **The $50M floor** came from family 18, a grid of 180 cells of "jump on news" chosen on
   2010 to 2017 only. The five cells it chose are all rule A with the floor and nearby
   thresholds. Tested on 2005–2009 and 2018–2022: all five pass, and all ten test years are
   positive for each. The floor was put in the grid because I had seen companies under $50M
   lose in every period (−5.5% a trade), so it is hindsight in that sense; the choice of it
   on 2010–2017 and its test are clean. For A50 the 2023 figure is a second look at months
   already read.
5. **No other kind of news works.** Jumps on other 8-Ks, on other filings or with no filing
   do not drift: none of those cells reached 2% with a weekly t of 3 in 2010–2017.

The holdout from 2023-11-09 is sealed and has not been touched.

## What a trade looks like

Across all 1,551 trades (auction basis): mean 3.94%, median 1.78%, 55% win, and one trade
swings by 23%.

| Worst 1% | Worst 5% | Lower quarter | Median | Upper quarter | Best 5% | Best 1% |
|---|---|---|---|---|---|---|
| −46% | −26% | −7% | +2% | +13% | +37% | +69% |

The profit is in the large winners: without the best 1% of trades the mean is 2.76%; without
the best 5% it is 0.86%. A year with few large winners is flat or down.

## Costs decide how much of it is kept

The effect is strongest in stocks that trade under $1M a day (5.3% a trade, 890 trades),
where the quoted spread is about 1% a side. Above $1M a day it is 2.1% (661 trades).

- **Auction basis** assumes the order joins the opening and closing auctions and pays
  commission plus 0.25% a side for its own effect on the price (0.10% above $1M a day). The
  allowance is my assumption, not a measurement.
- **Spread crossed** pays the modelled half-spread each way, as a market order would.
- **Spread doubled** is the search's declared cost, twice the modelled spread.

Two checks so far, both from minute bars:

- **The result does not rest on single prints.** Buying at the volume-weighted price of
  09:30 to 10:00 and selling at that of the last 30 minutes gives 4.35% (2005–2009), 3.37%
  (2010–2022) and 5.68% (2023) on the auction basis, against 4.49%, 3.60% and 5.95%.
- **There is room for a small order.** The median trade sees about $680,000 change hands in
  the first 30 minutes of the entry day, and $126,000 or more in nine trades of ten. A $2,000
  order is under 2% of that.

Not yet measured: what an on-open or on-close order actually pays. A sample of 150 trades
(300 tick windows) is planned in
`MarketData/processed/kinn/quotes_sample/swing_auction/windows.csv` for the owner to download.

## As a book of $20,000

Signals of 2005 to 2022, no leverage. A slot must be free at the open; when several signals
arrive together the one with the most volume against normal goes first.

| Book | Costs | Profit a year | Of $20,000 | Sharpe | Worst drawdown | Losing years |
|---|---|---|---|---|---|---|
| 10 positions of $2,000 | auction basis | $5,005 | 25.0% | 1.07 | $10,094 | 0 of 18 |
| 10 positions of $2,000 | spread crossed | $3,452 | 17.3% | 0.74 | $10,855 | 2 of 18 |
| 20 positions of $1,000 | auction basis | $3,099 | 15.5% | 1.11 | $5,891 | 1 of 18 |
| 20 positions of $1,000 | spread crossed | $2,141 | 10.7% | 0.77 | $6,638 | 1 of 18 |

The 10-position book skips about a fifth of the signals because earnings come in clusters;
it earns more and its worst drawdown is half the account. The 20-position book takes nearly
every signal and is steadier, but most of its money sits idle between earnings seasons.
In 2023 the 10-position book made $5,011 with the spread crossed.

Against the targets of decision 0017: a trade clears +1% on every basis except the doubled
spread in the search years (0.92%); Sharpe is above 1 only on the auction basis; the
10-position drawdown is just over half the account; fills are not confirmed.

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

| Family 18: jumps on other news (other 8-Ks, other filings, no filing), under $300M | 108 | No cell reaches 2% with a weekly t of 3 in 2010–2017 |

About 12,000 cells in all.

## What is still open

- **The tick sample**, to replace the auction allowance with a measurement. Owner's download.
- **The holdout.** The rule is not a Kinn strategy yet; it has to be written for the engine
  before the owner can run it on the sealed years. One run.
- **Idle money.** The rule uses under half the account on average, and family 18 found no
  second kind of news to fill it.

## Reproduce

```
uv run python research/claude/swing_wide.py            # the table, 2010 on
uv run python research/claude/swing_wide.py --early    # 2005 to 2009
uv run python research/claude/swing_search.py prep
uv run python research/claude/swing_search.py family 2 --basis auction --sort auct
uv run python research/claude/swing_early.py A50 early  # or search, check; rules A, B likewise
uv run python research/claude/swing_reprice.py A50 early
uv run python research/claude/swing_book.py A50 early search 10 20 --by-volume
uv run python research/claude/swing_news.py choose     # family 18; then: test <cell>
uv run --with lightgbm python research/claude/swing_model.py fit --small --no-market --name small
```
