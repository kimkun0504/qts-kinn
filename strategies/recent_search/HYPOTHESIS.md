# Hypothesis: a search for new intraday rules on recent years

Written 2026-11-16 02:55 ET, before any measurement. The owner's instruction, left for the
night: keep generating and testing new intraday ideas, weighting 2022 onward, using news and
stock-selection features, until one averages 3% a trade or the session ends. Well-known rules
are assumed to be crowded; the rebound and the published momentum rules have been tested and
are in their own reports.

## What "3%" means here

The mean net return of all trades, after costs at twice the modelled slippage. The mean of
winning trades alone is reported beside it but is not the target.

## Periods (decision 0019)

- **Search:** 2018-01-02 to 2022-12-30. Every result is shown by year, and 2022 must hold.
- **Check:** 2023-01-03 to 2023-11-08, looked at once, for the rules shortlisted from the
  search.
- **Holdout:** from 2023-11-09, sealed, the owner's one run for this family.

The years 2017 to 2023 were validation years for earlier families. Using them to search is
the owner's instruction and applies to this family only.

## Data and trades

One row per stock per session: what was known before the open (prior close, size, liquidity,
sector, 8-K filings by item type dated before today, prior returns), the premarket, and the
state at ten times of day (09:35, 09:45, 10:00, 10:30, 11:00, 12:00, 13:00, 14:00, 15:00,
15:30): price, volume, trade count, VWAP, high and low so far.

A trade buys at the first print at or after one of those times and sells at the official
close. Long only (the engine cannot short; short-side results are shown for information).
Full sessions only.

## Costs

Per side: commission ($0.0035 a share, $0.35 minimum, on a $2,000 position) plus half the
spread. Half-spreads are the means measured in the quote sample of 2026-11-15, by 20-day
dollar volume: under $1M, 1.00%; $1M to $10M, 0.43%; $10M to $100M, 0.18%; over $100M, 0.05%.
At 2× the spread is doubled. The rebound work showed that right after an extreme move the real
cost can be twice this again, so any rule that survives still needs a check against quotes.

## Idea families (each a small grid of conditions, declared here)

1. **Gap, news and premarket.** At 09:35: size of the gap, by 8-K type since the prior
   session, by premarket dollar volume against the 20-day norm, by company size.
2. **Opening drive.** At 10:00: move from the open, by relative volume, by mean trade size
   against its norm (large prints or small), by size.
3. **Later in the day.** At 11:00, 13:00 and 15:00: move from the prior close, by relative
   volume, by size.
4. **Day two.** After a session up or down 10% or 20%: by where it closed in its range and
   by today's gap.
5. **News type.** Each common 8-K item (earnings, agreements, officer changes, financing,
   delisting notices and others), by today's gap direction and size.
6. **VWAP and range position** at 11:00 among active stocks.
7. **New listings:** the first 20 sessions of a stock.
8. **Trade-size signature:** stocks whose mean trade size is far above or below normal in the
   first half hour.
9. **Stock-selection features** (owner's hint), used as a second cut on whatever the first
   eight turn up: price, size, sector, exchange and category, share turnover, volatility,
   60-session trend, age.

Further families may be added during the night; each is written here, dated, before it is
measured.

## Selection, set now

A cell (one combination of conditions) is shortlisted from the search years only if:

1. at least 300 trades in 2018–2022;
2. mean net return at 2× of at least 3.0% (cells between 1.5% and 3.0% are listed as
   near misses, not candidates);
3. a t-statistic of at least 4 on daily means (hundreds of cells are examined);
4. positive net at 2× in every year 2018 to 2022.

A shortlisted cell may be refined once, by one further feature. Then the check: on 2023 it
must be positive at 2× and at least half its search-period mean. Whatever passes is written
up with the owner's holdout command and a quote sample to download. Nothing is called found
on the search years alone.

## Risks

The number of cells examined; prices at the first print flatter illiquid stocks; one row per
stock-day means a cell with many trades on one day needs more capital than the account has;
8-K dates carry no time of day.
