# Hypothesis: buying after insiders buy

Written 2026-11-16 18:31 ET, after the SEC's insider files were downloaded and their columns
listed, and before any return is measured. A second rule beside the earnings drift
(`strategies/earnings_drift`), wanted because that rule has flat years and idle money
between earnings seasons.

## Why it might work

Officers and directors who buy their own company's shares in the open market, with their own
money, know more than outsiders, and the purchase is public within two business days on Form
4. In small companies few people read those filings. Studies going back decades find the
shares keep rising for weeks, more so when several insiders buy and in smaller companies.
Insiders may not trade around earnings, so these signals come between earnings seasons.

## Why it might not

It is one of the best-known effects there is, and services publish every Form 4 within
seconds. Purchases are often small and symbolic. The companies are small, so costs decide.

## Data

The SEC's Insider Transactions Data Sets, 2006 Q1 to 2023 Q3 (71 quarterly files, downloaded
by the owner to `raw/sec/insiders/`; the next file reaches past the holdout seal). A
purchase is a Form 4 non-derivative transaction with code P, acquired, with a positive price
and share count, dated within 10 days of its filing. Amended filings (4/A) are left out.
Companies are matched to the panel by the trading symbol on the filing.

## Trade

A signal is a company and a filing date with at least one purchase. The filing is public by
that evening, so the buy is at the first open after the filing date and the signal's
features are those of the last session on or before it. Sell at the close 5, 10 or 15
sessions after that session. Long only. Same stocks and costs as the earnings rule: common
stock, close of $1 or more, $250,000 or more traded a day; results on the auction basis and
with the modelled spread crossed. Within a cell a company gives one signal in any 21 days.

## Grid (432 cells), chosen on 2010 to 2017 only

- Company size: under $50M, $50M to $300M, $300M to $2B, over $2B.
- Dollars bought on the filing date, all insiders together: any, $100,000 or more, $500,000
  or more.
- Insiders who filed purchases in the 14 days to the filing date: at least 1, 2 or 3.
- Who: anyone, or at least one officer among them.
- The stock over the 20 sessions before: any, or down 10% or more.
- Hold: 5, 10 or 15 sessions.

Chosen: every cell with 300 or more trades, a mean of 2% or more on the auction basis and a
weekly t-statistic of 3 or more in 2010 to 2017, up to the five highest t.

## Test

On 2006 to 2009 and 2018 to 2022 together, which the choice does not read: a mean of 1% or
more on the auction basis in each period and a weekly t of 3 or more over the two. Then one
check on 2023 (signals to 29 September): above zero is "not contradicted".

## Holdout

From 2023-11-09, untouched for this family. It needs the later SEC files and one run by the
owner, for one frozen rule, only if a rule passes everything above.

## Addendum, 2026-11-16 18:36 ET: the rule taken forward, and the book question

Five cells were chosen on 2010 to 2017; three passed the test on 2006 to 2009 and 2018 to
2022, all in companies of $50M to $300M with $100,000 or more bought. The one with the
highest pooled t (3.84) is taken forward as **rule I**: any insider, hold 15 sessions. Its
2023 check has been read once (1.73% a trade, not contradicted).

Before any more is made of it, one question, set here: does adding rule I to the earnings
rule's book make the book better? On signals of 2006 to October 2023, 10 positions of $2,000:
the earnings rule alone; rule I alone; and both, the earnings rule taking a slot first and
rule I filling what is left, the largest purchase first. Measured by profit a year, Sharpe
ratio, worst drawdown and the number of losing years, on the auction basis and with the
spread crossed. Rule C was dropped at this step for making the book worse.

## Addendum, 2026-11-16 18:37 ET: the book result, and a hedged reading

**Book result:** rule I adds profit and fills some of the earnings rule's weak years, but both
rules are long small stocks and fall together. As two sleeves of 10 positions of $1,000, the
auction-basis book earns $5,954 a year against $4,965 for the earnings rule alone, with the
same Sharpe ratio (1.08 against 1.04), a larger drawdown and a loss in 2008; with the spread
crossed it earns the same as the earnings rule alone with a worse drawdown.

**A hedged reading, set before it is measured.** Both rules beat other stocks in nearly every
year; what makes years flat or losing is the market. So each trade is re-read with an equal
dollar amount of the small-stock index fund (IWM) sold short from the entry open to the exit
close, at a cost of 0.10% a trade for the fund's commission, spread and borrow. Reported: the
mean a trade by year for each rule, and the two-sleeve book's profit, Sharpe ratio, drawdown
and losing years, hedged and not. This is a measurement. Selling an index fund short needs
the owner's decision (the brief is long only) and a margin account.

## Addendum, 2026-11-17 00:01 ET: which insider signals fail (the method that found A50Q)

Written before anything is measured. Rule I's edge halved after 2017 and 2021 and 2022 made
nothing. The earnings rule's flat years turned out to come from one kind of signal, found by
splitting its trades on facts known at the signal and keeping only what held in every span.
The same is done here. Unlike the earnings rule, **this family's holdout is untouched**, so a
refinement that survives can still be tested properly, once, by the owner.

**Signals:** rule I ($50M to $300M, $100,000 or more bought on a filing date, hold 15, one
signal a company in 21 days), 2006 to September 2023, the auction basis. Spans: 2010–2017,
2006–2009, 2018–2023, and 2018–2023 without 2020.

**Ten facts, each known at the signal's close:** the stock is down over the past 250
sessions; the company holds net cash; it lost money last quarter; free cash flow is
negative; it issued over 10% more shares in a year; the price is under $5; the stock is not
at a 250-day high; an officer is among the buyers; the purchase is 0.2% or more of the
company's market value; the buyer is only a ten-percent owner.

1. **Single splits (20 groups).** A split counts only if one side beats all trades in every
   span, with and without 2020.
2. **Pairs (45 pairs, 180 groups),** ranked on 2010–2017 alone, groups of 150 trades or more
   there. Then how the best and worst tenth of groups did in the other spans, and the rank
   correlation, as for the earnings rule.
3. **A refined rule** is written down only if a group chosen by steps 1 and 2 makes 3% or
   more a trade in each span and without 2020, on 300 trades or more in each, with 2021 and
   2022 both positive and at least 16 of 18 years positive. It is then fixed and left for
   the holdout. If nothing meets that, the insider rule stays as it is: a weak second sleeve.

About 200 trials, in family `insider_buying`.

**Results, 2026-11-17 00:01 ET.** In REPORT.md. Three single splits hold in every span
(price under $5, issuance of 10% or less, a buyer who is not only a ten-percent owner). 161
pair groups had 150 trades or more; their ranking in 2010–2017 and elsewhere correlates at
0.26. No group meets step 3: the best (under $5 and little issuance: 5.63%, 8.06%, 3.06%;
3.29% without 2020; 17 of 18 years) lost in 2022, as every strong group did. No refined rule
is written. 181 trials.
