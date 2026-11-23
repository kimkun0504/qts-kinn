# Hypothesis: stocks repeat their own calendar months

Written 2026-11-23 16:10 ET, before any return is measured. Why now: the rules that work (the
earnings drift, big prints, the after-hours short) all live in companies under $2B and stop
growing at a few tens of thousands of dollars a year. This is a test of an idea that would
work in large companies, where size is not the limit. A new family, `seasonality`, with its
own holdout, which nothing has touched. No one has looked at this idea on this data before.

## Why it might work

Heston and Sadka (2008) found that a stock's return in a calendar month is higher when its
returns in the same month of earlier years were high, for up to twenty years back, and
Keloharju, Linnainmaa and Nyberg (2016) found the same in other markets and other assets.
Things that recur on a stock's own calendar would do this: its results season, its dividend
months, its fiscal-year end, the funds that hold it and their own year-ends, index changes.

## Why it might not

It has been in print since 2008. A large part of it is the results month (stocks rise into
their reports), which this platform has looked at in other forms (`before_report`). The
ranking changes every month, so the whole book turns over every month and pays costs twelve
times a year. Our data starts in September 2003, so the signal uses at most five earlier
years, far fewer than the published twenty.

## Data

The panel of the current build (447e58e098), sessions 2003-09-10 to 2023-11-08 only. US common
stock (categories starting "Domestic Common Stock"). A month's return is the sum of the daily
log returns close to previous close (the panel's `prev_close` is adjusted for splits;
dividends are left out), over the sessions of the month.

## Signal

For month m of year Y, a stock's score is the average of its returns in month m of the years
Y−1 to Y−5, using the years in which it traded on every session of that month; at least three
such years are needed.

## Trade

On the first session of month m, stocks eligible that morning (by the previous close) are put
into tenths by score. The book buys the top tenth, equal weight, at the open of the first
session and sells at the close of the last session of the month. Cost: the platform's research
approximation (commission and fees by price, half-spread by 20-day dollar volume), both ways,
every month, as if every position turned over; 2× doubles the spread part.

## Cells (4)

- **Large:** market value $2B or more, price $5 or more, 20-day dollar volume $5M or more.
- **Mid:** market value $300M to $2B, price $5 or more, 20-day dollar volume $1M or more.
- Each read two ways: the top tenth against the average eligible stock of its size (a long
  book measured against its own market), and the top tenth against the bottom tenth (long and
  short; the short side pays a borrow of 1% a year).

## Test

Chosen on the months of 2010 to 2017 (96 months). Tested on 2018 to 2022 (60 months) and 2007 to
2009 (36 months; the first months with three earlier years). 2023 January to October is a check.
November 2023 reaches into the holdout and is never read.

- **To be taken forward** a cell needs, where chosen, 0.40% a month or more after costs over
  its comparison, a monthly t-statistic of 2.5 or more, and at least 6 of 8 years positive;
  and where tested, 0.25% a month or more after costs in 2018–2022, positive at 2× costs, at
  least 4 of 5 years positive, and a positive average in 2007–2009.
- If a cell passes it is fixed here and goes on to a monthly book (`kinn book`) and then this
  family's holdout. If none does, the family is closed, with the numbers.
- Tenths 2 to 10 and the rank correlation of score and return are reported for every cell as
  description; they choose nothing.

4 trials.
