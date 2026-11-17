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

The holdout from 2023-11-09 was sealed throughout this search. It was run afterwards, once; see the end of this report.

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

Measured since from a tick sample of 150 trades: the bar's open and close are auction prints
in 99% of entries and 93% of exits, the cross is within 0.1% of the quotes beside it, and
market orders instead cost 1.2% a round trip. See
[`strategies/earnings_drift/REPORT.md`](../earnings_drift/REPORT.md).

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

| Rule C: a pullback in a small winner ($300M to $2B, up 50–100% in 120 sessions, down 5–10% in 5), to fill the idle slots | 1 | Passed its test on 2005–2009 (1.78% a trade on the auction basis, weekly t 3.22, four years of five; 2008: −3.9%), but only 0.8% of that is over the market, and adding it to the book lowers the Sharpe ratio (1.07 to 0.81) and raises the drawdown. With the spread crossed the combined book earns less than the earnings rule alone. Not taken forward |

About 12,000 cells in all.

## What happened next

The rule became `strategies/earnings_drift` and the owner ran it once on the holdout
(2023-11-09 to 2026-11-06): 266 trades, 5.04% a trade at 1× and 4.67% at 2×, $26,716.
**Passed.** Details, the tick measurement and the caveats (2026 was flat) are in
[`strategies/earnings_drift/REPORT.md`](../earnings_drift/REPORT.md).

## Sliding windows and market cycles (after the holdout, on years already read)

**Re-fitting the thresholds each year does worse than leaving them alone.** For each year
from 2010 to 2023 the best cell of family 18's grid on the five years before (or on all years
before) was traded in that year.

| 2010 to Oct 2023 | Trades | A trade, auction basis | Years positive |
|---|---|---|---|
| Fixed rule A50 | 1,118 | 3.84% | 13 of 14 |
| Chosen each year on the five years before | 1,293 | 2.81% | 11 of 14 |
| Chosen each year on all years before | 1,380 | 2.77% | 11 of 14 |

Two readings. The fixed rule's thresholds carry some hindsight, and the walk-forward 2.8% is
the figure with none. And every year, from any window, the choice was an earnings cell with
thresholds near A50's: the effect did not have to be known in advance to be found.

**By market cycle** (signal date; holds run up to three weeks past each end date):

| Stretch | Trades | A trade | Winners | All stocks, same holds |
|---|---|---|---|---|
| 2005 to Oct 2007, rising | 206 | 5.96% | 64% | 0.65% |
| Oct 2007 to Mar 2009, financial crisis | 110 | 0.61% | 48% | −2.15% |
| Mar 2009 to Apr 2011, recovery | 224 | 5.16% | 56% | 1.88% |
| May to Dec 2011, sell-off | 45 | −4.98% | 40% | −4.77% |
| 2012 to mid-2015, rising | 260 | 3.17% | 56% | 0.31% |
| Aug 2015 to Feb 2016, sell-off | 32 | 2.81% | 50% | −1.14% |
| Feb 2016 to Sep 2018, rising | 221 | 5.44% | 57% | 1.36% |
| Oct to Dec 2018, sell-off | 18 | −9.08% | 44% | −4.23% |
| 2019 to Feb 2020, rising, then into the crash | 94 | 0.64% | 45% | −2.11% |
| Feb to Mar 2020, pandemic crash | 11 | −24.14% | 9% | −23.17% |
| Mar 2020 to 2021, boom | 186 | 8.83% | 61% | 3.31% |
| 2022, falling | 81 | 1.56% | 51% | −1.29% |
| 2023 to Oct, recovery | 63 | 5.95% | 49% | −1.27% |

In rising and recovering markets it makes 3% to 9% a trade. In slow declines (2008, 2022) it
stays a little above zero, about 3% ahead of other stocks. In sharp sell-offs (2011, late
2018, March 2020) it falls with the market or further. There are few signals in a crash, so
those stretches are a small part of the trades, but they are where the drawdowns come from.

## Entries and exits (after the holdout, on signals of 2005 to October 2023)

The frozen rule buys at the next open and sells at the close 15 sessions later. Twenty-three
alternatives, on the same 1,551 signals (`research/claude/swing_exits.py`; auction basis; the
book is 10 positions of $2,000 over 2005 to 2023):

| Variant | A trade: 2010–17 / 2005–09 / 2018–23 | Book a year | Sharpe | Drawdown |
|---|---|---|---|---|
| **Plain rule** | 3.25% / 4.48% / 4.27% | $5,105 | 1.09 | $10,094 |
| Hold 5 sessions | 1.64% / 1.52% / 2.14% | $2,858 | 1.30 | $5,454 |
| Hold 10 | 2.41% / 2.61% / 3.53% | $4,178 | 1.25 | $6,794 |
| Hold 20 | 4.64% / 6.13% / 4.50% | $5,709 | 1.08 | $11,656 |
| Hold 30 | 5.57% / 7.61% / 3.95% | $6,015 | 1.13 | $15,385 |
| Stop 8% under entry | 2.67% / 2.16% / 2.53% | $3,739 | 0.92 | $11,338 |
| Stop 12% | 2.82% / 2.95% / 2.94% | $4,013 | 0.95 | $10,122 |
| Stop 20% | 3.09% / 3.97% / 4.63% | $5,010 | 1.10 | $10,431 |
| Stop at the signal day's low | 2.30% / 1.49% / 3.23% | $3,680 | 1.10 | $6,815 |
| Target 15% | 1.93% / 3.97% / 2.34% | $3,634 | 1.26 | $5,921 |
| Target 25% | 2.85% / 4.28% / 3.42% | $4,831 | 1.47 | $7,502 |
| Target 40% | 3.32% / 4.44% / 3.84% | $5,148 | 1.45 | $8,464 |
| Stop 12% with target 25% | 2.56% / 2.65% / 2.58% | $3,841 | 1.42 | $4,621 |
| Trailing stop 20% under the highest close, to 30 sessions | 4.92% / 6.93% / 3.84% | $6,671 | 1.36 | $8,750 |
| **Exit under the 20-day average, to 30 sessions** | 3.34% / 5.83% / 4.36% | $6,328 | 1.37 | $7,428 |
| Exit under the 9-day average, to 30 | 2.73% / 2.54% / 2.16% | $3,731 | 1.02 | $6,361 |
| Entry only if the open gaps up 5% at most | 3.66% / 4.68% / 4.68% | $5,137 | 1.12 | $10,307 |
| Entry on a limit 3% under the signal close | 2.53% / 5.70% / 4.39% | $3,771 | 0.90 | $9,550 |
| Entry at the next close instead of the open | 2.36% / 3.95% / 2.44% | $3,567 | 0.79 | $10,611 |

- **Tight stops hurt.** A stop 8% or 12% under the entry lowers the mean in every period and
  does not reduce the drawdown: these stocks swing that much before the winners run.
- **Waiting a day costs a quarter to a half of the edge.** The first session after the signal
  is part of the drift, and waiting for a pullback misses the best trades.
- **The drift used to run 30 sessions and now runs about 15 to 20.** Longer holds beat the
  plain rule before 2018 and not since.
- **Profit targets give up a little return for a much steadier book** (Sharpe 1.45 against
  1.09 with a 40% target) by selling the most volatile positions once they have run.
- **One variant beats the plain rule on every measure set beforehand** (the mean in all
  three periods, the book's Sharpe ratio and its drawdown): hold until the close falls under
  its 20-day exponential average, 30 sessions at most. Its margins on the mean are small in
  two periods (0.09%), it is one of 23 tried, and its holds run past the three weeks the
  owner set. It cannot be confirmed on the holdout, which is spent; the frozen rule stays
  the reference and this exit is a candidate for the paper ledger.

Limits: a stop or target is judged from each day's high and low, so the order within the day
is assumed (the stop first), and a target is assumed to fill as a limit order, which is
generous in thin stocks.

## The flat years: which signals fail (after the holdout, on signals of 2005 to October 2023)

The owner's question: some years are flat, and a flat year is no better than a bank account.
2020 is treated as an outlier; every figure is also given without it, and nothing below was
chosen because of 2020. Plan and the checks: HYPOTHESIS.md, addenda of 2026-11-16 22:53 and
23:08 ET. All of this is on years already read. The holdout is spent, so none of it is proof;
see [what it is worth](#what-this-is-worth).

**The finding.** A50's signals in companies that hold **net cash and whose stock is down over
the past year** make nothing. Skipping them leaves a rule that made money in every year.

| A50 signals (auction basis, a trade) | 2010–17 | 2005–09 | 2018–23 | 2018–23 without 2020 |
|---|---|---|---|---|
| All | 3.25% | 4.48% | 4.27% | 3.79% |
| Up over the year, net debt | 6.67% (132) | 4.72% (84) | 9.91% (114) | 11.11% |
| Up over the year, net cash | 2.32% (201) | 6.88% (122) | 1.96% (117) | 1.27% |
| Down over the year, net debt | 4.14% (114) | 4.62% (107) | 4.55% (160) | 4.68% |
| **Down over the year, net cash** | **0.56%** (117) | **−0.44%** (93) | **−0.32%** (104) | **−3.01%** |
| **Kept: up over the year, or net debt** | **4.10%** (464) | **5.58%** (319) | **5.35%** (394) | **5.49%** |

"Up over the year" is the stock's return over the 250 sessions to the signal's close; "net
debt" is debt above cash at the last quarterly report filed before the signal. The kept
trades are positive in each of the 19 years 2005 to 2023; the lowest is 1.9% (2011). Over all
years the mean rises from 3.93% to 4.92% (4.91% without 2020) and 374 of 1,551 signals are
skipped.

The group that fails is half technology and health care, 71% loss-making, down 38% over the
year at the median, with cash of about a fifth of its market value. Its jump gains 0.6% in
three sessions and then stops; the other signals keep rising to 5.5% by the fifteenth.

**Eight splits were looked at to find it.** Three beat all trades in every span: net debt,
at a 250-day high, and up over the year. Share issuance (the idea the plan began with),
profit, free cash flow, price and short interest did not split the trades the same way twice.

**Checks, set before they were run.**

- *Chance.* Of 5,000 random filters dropping the same number of trades, none reached the
  filter's mean without 2020 (4.91%; the best was 4.81%). Dropping the same number in each
  year, one in 5,000 did.
- *Would 2010–2017 alone have found it?* Of 75 groups made from pairs of seven facts, "net
  cash and down over the year" is the sixth worst of 2010–2017 (0.56%), and the only one of
  the eight worst that also lost in the other years (−1.66% without 2020). Four of the eight
  worst hold net cash. The worst group of 2010–2017 (heavy issuers priced over $5, −0.98%)
  made 4.19% elsewhere, so a single span would have misled. Across all groups the ranking in
  2010–2017 and in the other years correlates at 0.53.
- *Cut-offs.* Moving the year's return between −30% and +20% and net cash between −10% and
  +25% of market value (24 combinations) leaves every year positive in all 24, with a mean
  without 2020 of 4.0% to 5.0%. It is not a knife edge.
- *Other universes.* In jumps of 10% to 15% the same group loses (−0.66%, 5.40%, −9.89% by
  span) and the kept trades make 2.0% to 2.9%, under the 3% set for adding them, so they are
  not added. In companies of $300M to $2B the rule has no edge with or without the filter.
- *Insider buying.* The filter does not carry over: rule I's "down, net cash" trades do no
  worse than the rest (2.94%, 4.12%, 1.52%). The insider rule stays unfiltered.

**As a book** (10 positions, $20,000, 2006 to 2023; each cell is dollars a year, Sharpe
ratio, worst drawdown, worst year):

| Book | Auction basis | Spread crossed | Losing years |
|---|---|---|---|
| A50 as it is | $4,974, 1.05, $10,113, +$209 | $3,459, 0.73, $10,896, −$1,440 | 0 and 2 |
| **A50, filtered** | **$5,097, 1.13, $10,366, +$1,929** | **$3,808, 0.84, $11,638, +$700** | **0 and 0** |
| A50, filtered, 20-day-average exit | $5,783, 1.30, $7,601, +$1,161 | $4,529, 1.02, $8,066, +$236 | 0 and 0 |
| A50 with the inverse fund bought beside every position | $2,334, 1.12, $4,765, +$207 | $1,576, 0.76, $4,842, −$581 | 0 and 1 |
| A50, no new trades while the index is under its 200-day average | $2,776, 0.79, $11,488, −$2,542 | $1,683, 0.48, $12,162, −$2,869 | 2 and 5 |
| A50 filtered, plus insider rule I in idle slots | $8,279, 1.08, $16,013, −$2,752 | $4,821, 0.63, $21,037, −$6,050 | 1 and 4 |

The filtered book by year, auction basis: 2006 $6,973, 2007 $6,496, 2008 $1,929, 2009 $8,630,
2010 $7,973, 2011 $2,254, 2012 $3,705, 2013 $8,134, 2014 $2,792, 2015 $2,337, 2016 $4,164,
2017 $2,163, 2018 $4,156, 2019 $2,523, 2020 $5,090, 2021 $9,323, 2022 $6,126, 2023 $6,112.
With the spread crossed the worst are 2011 ($700), 2008 ($950) and 2017 ($1,000). Without
2020 the book averages $5,046 a year, so 2020 is an ordinary year for it.

It meets what the plan set as "solving the flat years": the worst year gains at least 5% of
the account on the auction basis (9.6%) and no year loses with the spread crossed.

What did not help: standing aside in a downtrend (the rule's best trades come then), and the
purchased hedge (it halves the drawdown and more than halves the profit). The insider rule
adds dollars and brings back losing years, so it is not a fix for them. With 20 positions
the filtered book makes $2,984 a year (worst year +$1,068), and with rule I added $7,835
(worst +$2,246 on the auction basis, two losing years with the spread crossed).

**Stronger insider signals** (step 5; companies of $50M to $300M, hold 15, auction basis):

| Cell | 2006–09 | 2018–22 | 2022 | 2023 check |
|---|---|---|---|---|
| $500,000 or more, one insider | 3.43% | 2.17% | −1.8% | 2.71% |
| $500,000 or more, two or more | 4.50% | 2.49% | −4.4% | 2.49% |
| $100,000 or more, two or more | 4.98% | 2.53% | −1.5% | 2.92% |
| $100,000 or more, three or more | 5.49% | 1.43% | −1.2% | 4.34% |

Two or more insiders is about one point better than rule I since 2018. Every cell lost in
2022, and none removes the fall-off after 2017.

**Does the test rescue other jumps? (families 19 and 20, plan of 23:40 ET; 7 cells.)**
Companies of $50M to $300M, hold 15, the auction basis, the test as fixed.

| Jump | With the test: 2010–17 | 2005–09 | 2018–23 | Without 2020 | The fallen, cash-rich group |
|---|---|---|---|---|---|
| Earnings 8-K dated the same day, 15% on 5× volume | 5.19% (211) | 8.20% (168) | 4.01% (195) | 3.81% | −0.81%, 0.05%, −4.74% |
| Another 8-K item, 15% on 5× | 0.03% | −0.90% | −2.73% | −5.29% | −3.83%, −4.12%, −2.69% |
| Another filing, 15% on 5× | −0.87% | −3.53% | −0.98% | −3.68% | all negative |
| No filing, 15% on 5× | −3.79% | −2.26% | −3.41% | −4.59% | all negative |
| Earnings, next day, 15% on 2× to 5× | 1.23% | 0.20% | 0.69% | −0.29% | |
| Earnings, next day, 10% to 15% on 5×, up and net debt | 2.57% (63) | 4.05% (42) | 4.74% (40) | 5.31% | |

- The test is about **earnings**. Jumps on other news lose money with or without it, so the
  idea that it marks a general "bounce that holders sell into" is wrong, or at least not
  enough: without earnings there is no drift to protect.
- **One cell clears the bar on the trade: the earnings 8-K dated the day of the jump.** A50
  waits a session after the 8-K, because the filing has a date and no time; these are the
  releases filed that morning, read at that day's close and bought a session earlier. With
  the test they make 3.8% to 8.2% in every span; the fallen, cash-rich group fails here as
  well. Two thirds of them (378 of 574) are A50 events entered a day sooner; 196 are events
  A50 never takes, because the stock gave some back the next day.
- **It fails the last term set for adding it.** With one position a company (the earlier
  signal wins), the book makes $6,044 a year against $5,097 (Sharpe 1.24, worst year +$936)
  on the auction basis, but with the spread crossed two years lose a little (2011 −$404,
  2019 −$456). So it is **not added to the rule**. With the 20-day-average exit the combined
  book is the best seen ($7,227 a year, Sharpe 1.51, drawdown $6,484, worst year +$1,405;
  spread crossed $5,860, worst year +$26, none losing), but that is a second choice stacked
  on a first and was not the term set, so it is a lead, not a result.
- Weaker earnings jumps do not pass: lower volume has no edge, and the 10% to 15% jumps
  pass only under a stricter test on 40 to 60 trades a span.

**The drawdown (family 21, plan of 23:45 ET; 4 trials).** No losing calendar year is not
the same as never being under water. A50Q's book has two drawdowns of about $10,000 on the
$20,000 account: June to November 2007, not made back until August 2009, and December 2019
to April 2020, made back by August. Its longest spell under its own high is 445 sessions
(21 months). That is over the half of the account decision 0017 allows.

| A50Q's book, auction basis | A year | Sharpe | Worst drawdown | Longest under water | Worst year |
|---|---|---|---|---|---|
| 15-session exit | $5,097 | 1.13 | $10,366 | 445 sessions | +$1,929 |
| Smaller positions in wilder stocks | $4,095 | 1.10 | $9,938 | 581 | +$1,487 |
| Pause 20 sessions after a $3,000 loss | $5,301 | 1.19 | $10,193 | 429 | +$1,929 |
| At most two new positions a day | $5,336 | 1.17 | $10,507 | 443 | +$1,675 |
| **20-day-average exit** | **$5,783** | **1.30** | **$7,601** | **247** | **+$1,161** |
| 20-day exit, smaller in wilder stocks | $4,301 | 1.43 | $4,149 | 309 | +$1,848 |
| 20-day exit, pause after a $3,000 loss | $5,472 | 1.32 | $5,211 | 239 | +$1,161 |

- **None of the three controls passes** the term set (drawdown of $7,800 or less on the
  15-session exit). The losses come from positions already held when the market breaks, so
  a rule about what to open next arrives too late, and scaling down the wilder stocks trims
  profit as much as risk.
- **The exit is what moves the drawdown.** The 20-day-average exit sells a position when its
  own price breaks, which is the only control here that acts on what is held. It had already
  passed the terms set for it in the exit study; with the quality test it gives the best
  book that rests on tests set beforehand: $5,783 a year, Sharpe 1.30, drawdown $7,601 (38%
  of the account), no losing year on either cost basis.
- On top of that exit, smaller positions in wilder stocks bring the drawdown to $4,149 with
  no losing year on either basis ($3,285 a year with the spread crossed). That row is
  description, a third choice stacked on two, and is a lead only.
- The first version of the pause never resumed (a book that opens nothing cannot make its
  loss back, so the pause re-armed for good); the row above resets the high when a pause
  ends. Both are counted.

**How much money the rule can carry (description, no trial).** The owner finds $1,000 to
$2,000 positions small. The stocks set the limit: the kept signals trade a median of $861,000
on a normal day (a tenth of them under $344,000), and the tick study found a median opening
cross of $36,000 in stocks under $1M a day. A $2,000 order is about 6% of that cross; a
$10,000 order would be over a quarter of it.

A50Q with the 20-day exit, 10 positions, when a position may be at most 1% of the stock's
normal daily dollars (about a quarter of a typical opening cross), costs left as modelled:

| Account | Signals cut down | Mean position | A year, auction basis | Of the account | Spread crossed |
|---|---|---|---|---|---|
| $20,000 | none | $2,000 | $5,733 | 28.7% | $4,490 |
| $50,000 | 25% | $4,665 | $13,222 | 26.4% | $10,395 |
| $100,000 | 57% | $7,534 | $19,695 | 19.7% | $15,529 |
| $250,000 | 86% | $11,208 | $23,333 | 9.3% | $17,942 |
| $500,000 | 95% | $13,097 | $26,469 | 5.3% | $20,515 |

The rule stops growing at about $20,000 to $25,000 a year however large the account, and
past $100,000 a losing year returns, because the money then sits mostly in the larger
stocks, where the edge is thinner. With orders allowed up to 5% of normal daily dollars the
ceiling is about four times higher, but orders that size would be larger than most opening
crosses and the modelled costs would no longer hold. **It is a rule for an account of about
$20,000 to $100,000.**

### What this is worth

The filter was found by looking at years already read, among eight splits, their pairs and
24 cut-offs, then seven more cells on other jumps and four risk controls (about 225 trials added). The checks say it is unlikely to be chance and is not
a knife edge, and the failing group shows up in a second universe. It is still a finding
from data that has been seen. Two honest tests remain:

1. **Forward.** The paper ledger, with the filtered rule as its own books.
2. **The holdout, a second time.** The rule is now fixed in writing: skip an A50 signal when
   the stock's 250-session return is zero or less and cash is at least debt, or when either
   fact is missing and the other does not qualify it. The holdout's 460 signals have never
   been split this way. Running it is the owner's decision; it would be a second look at a
   spent holdout and should be read as such.

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
cd research/claude && uv run python swing_overnight.py quality   # then: books, cross, filtered, chance,
                                                              # pairs, cutoffs, who, wider, insider, final
```
