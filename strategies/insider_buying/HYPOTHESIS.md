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
