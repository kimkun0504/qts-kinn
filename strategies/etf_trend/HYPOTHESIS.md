# ETF trend: holding asset classes only while they are rising

Written 2026-11-17 17:20 ET, before anything is measured. The owner's instruction today:
"we can't just wait and test this one strategy and hope for the best, we need to find a
different working strategy", with the worry that a bear market is starting.

## Why

Everything tested so far picks stocks, and everything that worked is long small companies,
which fall with the market. A rule of a different kind is to hold whole asset classes
through index funds and to leave each one for cash when it is falling. It is old and widely
used, so no large edge is expected. What it offers is that it has tended to be out of stocks
in long declines, it takes any amount of money, it trades once a month, and it could work
the two-thirds of the account the earnings book leaves idle. Whether it is worth having
here is measured, not assumed.

## Data

Sharadar's fund prices (SFP), with closes adjusted for distributions, read only for dates
before 2023-11-09. Nine funds: SPY, IWM, EFA, EEM (stocks), TLT, IEF (Treasuries), GLD
(gold), DBC (commodities), VNQ (property). Cash is SHY (1 to 3 year Treasuries). DBC starts
in February 2006, so decisions start at the end of February 2007 and results run from
March 2007 to September 2023.

## Two rules, fixed now (no search)

Decided on the last session of each month from closes; traded at the close of the next
session. Cost 5 basis points a side on what is traded.

- **T1, each on its own trend.** A ninth of the money for each fund. Hold the fund if its
  adjusted close is above the average of its last ten month-end closes; otherwise hold SHY
  with that ninth.
- **T2, the strongest three.** Rank the nine by their return over the last twelve months.
  Hold the top three, a third each; any of them that did not beat SHY over the twelve
  months is replaced by SHY.

Beside them, for comparison only: the nine held equally all the time, and 60% SPY with 40%
IEF.

2 trials, family `etf_trend`.

## What is measured, and what counts

On $20,000 by itself, for the whole period and for 2007–2014 and 2015–2023: return a year,
Sharpe ratio over cash, worst drawdown, worst calendar year, and the years 2008 and 2022.
Then beside the earnings book (the 10-position A50Q book, 2007 to 2023, by month): the
correlation of the two, and the two together with the sleeve run on $13,000 (the average
idle money).

The owner's per-trade target does not fit a monthly allocation rule and is not applied. A
rule goes forward only if **all** of these hold:

- Sharpe over cash of 0.5 or more in each half;
- worst drawdown of 15% or less;
- not down in 2008, and not down more than 8% in 2022;
- correlation with the earnings book of 0.3 or less by month;
- together with the earnings book, a higher Sharpe ratio and a worst year no lower than the
  earnings book has alone.

A rule that goes forward is a candidate for the paper ledger and for one run on the
holdout, which this family has not read. One that does not is closed.

## Known before starting

Not measured here. Generally reported: rules like T1 made 2008 a small loss or a gain and
have been mediocre since 2015, with whipsaws in 2015, 2018 and 2022, when stocks and bonds
fell together.
