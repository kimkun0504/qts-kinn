# Insider buying: real, weaker than it was, and no cure for a falling market

Plan and every dated change to it: [HYPOTHESIS.md](HYPOTHESIS.md). Written 2026-11-16.

## Result

**Rule I.** A company worth $50M to $300M; insiders report open-market purchases of $100,000
or more on one filing date; buy at the next open, sell at the close 15 sessions later.

| Period | What it is | Trades | Auction basis | Spread crossed | Over other stocks | Weekly t | Years positive |
|---|---|---|---|---|---|---|---|
| 2010–2017 | where the cell was chosen | 2,909 | 3.18% | 2.05% | 2.94% | 5.68 | 7 of 8 (2015 flat) |
| 2006–2009 | test | 1,862 | 3.86% | 2.77% | 3.39% | 3.89 | 4 of 4 |
| 2018–2022 | test | 2,086 | 1.54% | 0.46% | 1.77% | 1.84 | 3 of 5 |
| 2023 to 29 Sep | check, read once | 275 | 1.73% | 0.65% | 2.41% | 1.58 | 1 of 1 |

It passed the test set beforehand (1% or more in each test period, a weekly t of 3 or more
over the two together: 3.84) and the 2023 check. Two things qualify that:

- **The edge has halved.** About 3% to 4% a trade until 2017, about 1.5% since; 2021 and
  2022 made nothing. With the spread crossed the recent years leave about half a percent.
- **It beats other stocks every year, 2006 to 2023,** but by less each time: 2% to 6% a
  trade before 2018, about 1% to 2.5% since.

It is a different trade from the earnings rule: about 400 signals a year against 80, spread
through the year, and only 92 of 7,132 come the session after an earnings filing. Half its trades are in
stocks that trade over $1M a day, where it does as well as in the thinner ones.

The search: 432 cells on 2010 to 2017; 68 reached 2% with a weekly t of 3; five were taken to
the test and three passed, all in the $50M to $300M band with $100,000 or more bought. The
two cells in companies of $300M to $2B failed (−0.2% in 2018 to 2022). 438 trials.

## In a book with the earnings rule (signals of 2006 to October 2023)

| Book of $20,000 | Costs | A year | Sharpe | Worst drawdown | Worst year | Losing years |
|---|---|---|---|---|---|---|
| Earnings rule alone, 10 × $2,000 | auction | $4,965 | 1.04 | $10,094 | +$202 | none |
| Earnings rule alone | spread crossed | $3,422 | 0.72 | $10,855 | | 2011, 2021 |
| Two sleeves, 10 × $1,000 each | auction | $5,954 | 1.08 | $11,628 | −$449 | 2008 |
| Two sleeves | spread crossed | $3,465 | 0.64 | $15,100 | −$2,824 | 2008, 2011, 2015 |
| One book, both rules, 10 × $2,000 | auction | $8,616 | 0.93 | $23,558 | −$1,633 | 2008 |

Adding rule I fills some of the earnings rule's weak years (2017: $6,995 against $1,632;
2021: $3,643 against $1,017) and adds about $1,000 a year on the auction basis, at the same
Sharpe ratio. It does not make the book safer: both rules are long small stocks, so they
fall together, and 2008 becomes a losing year. Run as one always-full book the profit
doubles and the drawdown exceeds the account.

## With the small-stock index sold short against each trade

Both rules beat other stocks nearly every year; the market is what makes a year flat. Each
trade re-read with the same dollars of IWM sold short for the hold, at 0.10% a trade:

| Mean a trade, auction basis | Years positive, 2006–2023 | Weakest year |
|---|---|---|
| Earnings rule | 17 of 18 | 2011, −0.4% |
| Earnings rule, hedged | 18 of 18 | 2014, +0.8% |
| Rule I | 15 of 18 | 2022, −0.7% |
| Rule I, hedged | 17 of 18 | 2021, −0.2% |

| Two sleeves, 10 × $1,000 each | A year | Sharpe | Worst drawdown | Worst year | Losing years |
|---|---|---|---|---|---|
| Not hedged, auction basis | $5,954 | 1.08 | $11,628 | −$449 (2008) | 2008 |
| Hedged, auction basis | $4,989 | 1.15 | $9,089 | +$1,633 (2021) | none |
| Hedged, spread crossed | $2,511 | 0.58 | $9,463 | −$755 | 2008, 2015, 2021 |

The hedge costs about $1,000 a year on average and removes the losing and flat years on the
auction basis: the worst of 18 years is +$1,633, 8% of the account. It does not shrink the
drawdown much, because that comes from single stocks falling, not from the market.

This is a measurement. Selling a fund short is outside the brief (long only) and needs a
margin account; it is the owner's decision.

## What is not done

- **The holdout** (from 2023-11-09) is untouched for this family. It needs the later SEC
  files, the rule written for `kinn swing`, and one run by the owner.
- **Fills** are assumed as for the earnings rule (measured there from ticks, in the same kind
  of stock); not measured for these trades.
- The hedge is priced from the fund's daily bars with an assumed cost.

## Stronger cells and the quality test (2026-11-16 night)

Four cells that were eligible on 2010–2017 but not among the five tested ($500,000 or more
bought; two or three insiders) were tested on 2006–2009 and 2018–2022. Two or more insiders
is about a point better than rule I since 2018 (2.5% against 1.5%); every cell lost in 2022
and none removes the fall-off after 2017. The quality test that fixes the earnings rule's
flat years does not carry over: insider purchases in fallen, cash-rich companies do no worse
than the rest. In the earnings rule's idle slots rule I adds dollars and brings back losing
years. Tables: `strategies/swing_search/REPORT.md`, "The flat years".

## Which insider signals fail (2026-11-17; plan in HYPOTHESIS.md, addendum of 00:01 ET)

The method that found the earnings rule's quality test, applied to rule I: its 7,132 trades
split on ten facts known at the signal, single splits in every span, then 161 pairs ranked
on 2010–2017 alone. Auction basis, a trade.

| Split | 2010–17 | 2006–09 | 2018–23 | Without 2020 |
|---|---|---|---|---|
| All of rule I | 3.18% | 3.86% | 1.56% | 1.24% |
| **Price under $5** | **5.42%** (929) | **7.05%** (660) | **2.93%** (988) | **2.51%** |
| Price $5 or more | 2.13% | 2.12% | 0.57% | 0.28% |
| Issued 10% or less in a year | 3.19% | 4.48% | 2.11% | 1.78% |
| Buyer not only a ten-percent owner | 3.32% | 4.58% | 1.61% | 1.33% |
| Under $5 and issued 10% or less | 5.63% (583) | 8.06% (473) | 3.06% (574) | 3.29% |

- Three splits hold in every span: the price, share issuance, and who the buyer is. The
  price matters most: **since 2018 almost all of what is left of the edge is in stocks under
  $5** (2.9% against 0.6%).
- Groups persist less than they did for the earnings rule: the ranking of 2010–2017 and of
  the other years correlate at 0.26 (earnings: 0.53); the best tenth of groups made 6.1%
  where ranked and 3.3% elsewhere.
- **No group meets the terms set for a refined rule.** The best, under $5 with little
  issuance, makes 3% or more in every span on 470 to 580 trades with 17 of 18 years
  positive, but it lost in 2022 (−1.0%), as did every other strong group. No rule is written.
- A caution on the under-$5 result: these are the stocks where the modelled costs are least
  trustworthy (a one-cent tick is 0.5% of a $2 stock, and the tick study covered the
  earnings rule's trades, not these). It would need its own fill measurement before it
  meant anything.

The insider rule stays what it was: a weak second sleeve, not a fix. 181 trials.

## Reproduce

```
uv run python tools/owner/download_insiders.py          # owner
uv run python research/claude/insider_events.py
uv run python research/claude/insider_study.py build
uv run python research/claude/insider_study.py choose
uv run python research/claude/insider_study.py test '$50M-$300M' 1e5 1 False False 15
uv run python research/claude/insider_book.py
uv run python research/claude/insider_hedge.py
cd research/claude && uv run python insider_quality.py
```
