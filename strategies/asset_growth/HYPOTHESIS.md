# Hypothesis: companies that grow their assets slowly beat those that grow them fast

Written 2026-11-23 16:30 ET, before any return is measured. Why now: the same reason as
`seasonality` (closed an hour earlier): the rules that work are in companies under $2B, and a
rule with room for more money has to live in larger ones. A new family, `asset_growth`, with
its own holdout, which nothing has touched. No one has looked at this idea on this data before;
`seasonality` shares its monthly returns, eligibility and costs, not its signal.

## Why it might work

Cooper, Gulen and Schill (2008): firms whose total assets grew most over the past year earned
less over the following year than firms whose assets grew least, after size and value. It is
the "investment" factor in the Fama–French five-factor model (2015). The usual story: managers
build when their stock is dear, and buyers extrapolate growth that does not last.

## Why it might not

In print since 2008 and part of a standard factor model, so much of it may be priced. It has
been weaker in large companies and in the 2010s, and much of it lies in the short side (the
fast growers), which costs borrow. A monthly book turns over a good part of itself each month.

## Data

The build 447e58e098: the panel (as in `seasonality`: month returns from the open of the first
session to the close of the last, eligibility by the previous close, costs) and the vendor's
as-reported statements (`sharadar/sf1`, trailing-year dimension ART) through
`DataStore.fundamentals_as_of`, which uses only filings made before the day asked and never a
date from 2023-11-09.

## Signal

On the first session of month m: each company's latest trailing-year total assets filed before
that session, against the same company's figure for the fiscal period a year earlier; growth
= assets / assets a year ago − 1. Both must be positive, and the latest period must end no more
than 500 days before the session (as the screener requires).

## Trade

Stocks eligible that morning are put into tenths by growth. The book buys the **lowest** tenth,
equal weight, at the open of the first session and sells at the close of the last session of
the month. Costs as in `seasonality`: both ways every month, as if every position turned over;
2× doubles the spread part.

## Cells (4)

- **Large:** $2B or more, price $5 or more, 20-day dollar volume $5M or more.
- **Mid:** $300M to $2B, price $5 or more, 20-day dollar volume $1M or more.
- Each read two ways: the lowest tenth against the average eligible stock of its size, and the
  lowest tenth against the highest (long and short; the short side pays a borrow of 1% a year).

## Test

As in `seasonality`: chosen on 2010 to 2017 (96 months); tested on 2018 to 2022 and 2005 to 2009
(fundamentals reach back further than three years of returns, so the early test starts in
2005); 2023 January to October is a check; November 2023 is never read.

- **To be taken forward** a cell needs, where chosen, 0.40% a month or more after costs over its
  comparison, a monthly t of 2.5 or more and at least 6 of 8 years positive; where tested,
  0.25% a month or more after costs in 2018–2022, positive at 2× costs, at least 4 of 5 years
  positive, and a positive average in 2005–2009.
- If a cell passes it is fixed here and goes on to a monthly book and then this family's
  holdout. If none does, the family is closed, with the numbers.
- The other tenths and the rank correlation are reported as description; they choose nothing.

4 trials.
