# Hypothesis: a search for a profitable swing rule (holds of 1 to 3 weeks)

Written 2026-11-16 13:05 ET, before any measurement. The owner's instruction of the same day:
holding for more than a day is allowed, as swing trades of 1 to 3 weeks; a smaller edge than 3%
a trade is acceptable but it must be profitable; do not stop at the first few ideas. The
intraday searches are in `strategies/recent_search` and `strategies/intraday_momentum`.

## Trades

A signal is read at the close of a day. The buy is at the next day's open. The sale is at the
close 5, 10 or 15 sessions after the signal day. Long only. One $2,000 position a trade.

Returns are built from each day's close against the prior close on the same share basis, so
splits are handled; dividends are left out, which understates a long trade slightly. If a
stock stops trading during the hold, the trade ends at its last close; such trades are counted
and the result is shown again with a further 50% loss on each.

## Costs

Per side: commission ($0.0035 a share, $0.35 minimum) plus half the spread by 20-day dollar
volume (under $1M, 1.00%; $1M to $10M, 0.43%; $10M to $100M, 0.18%; over $100M, 0.05%: the
means measured in the quote sample of 2026-11-15). At 2× the spread is doubled.

## Periods (decision 0020)

- **Search:** signals from 2010-01-04 to 2022-11-30. Each year 2018 to 2022 is shown apart,
  and 2010 to 2017 as one block.
- **Check:** signals from 2023-01-03 to 2023-10-13 (so every hold ends before the seal),
  looked at once, for shortlisted rules only.
- **Holdout:** from 2023-11-09, sealed, the owner's one run for this family.

## Idea families (each a grid of conditions; more may be added, dated, before measuring)

1. **Short-term reversal:** a fall over 5 days, by the 60-day trend, by company size.
2. **Earnings drift:** the first session after an earnings 8-K, by that day's return and
   volume, by size.
3. **Breakouts:** a new 250-day high, by volume and by the 20-day run.
4. **Pullbacks in winners:** up strongly over 120 days, down over 5.
5. **Volume shocks:** five times normal dollar volume with no filing, by the day's return.
6. **Near the 250-day low:** by the 20-day fall and the day's close in its range.
7. **Short interest** (2018 on): share of shares short and days to cover, with the 5-day and
   20-day moves.
8. **Fundamentals at earnings:** year-on-year change in quarterly earnings and revenue from
   the filed statements, with the reaction.
9. **Stock-selection cuts** on whatever the first eight turn up: price, size, liquidity,
   volatility, sector, age, market trend.

## Selection, set now

A cell is shortlisted from the search years only if:

1. at least 300 trades in 2018–2022 and 300 in 2010–2017;
2. mean net return at 2× of at least 1.0% a trade (3.0% is the owner's first target; cells at
   or above it are marked);
3. a t-statistic of at least 4 on weekly means of 2018–2022 (holds overlap, so weeks, not
   days, are the unit);
4. positive net at 2× in every year 2018 to 2022, and in 2010–2017.

A shortlisted cell may be refined by further features. The best are then run as a book
($20,000, at most 10 positions of $2,000, no leverage) with the same data, since a mean per
trade says nothing about whether the account could have held the trades. The check on 2023 is
for the book that results. Nothing is called found on the search years alone.

## Risks

Many cells; delisting in losers; signals crowd into bad weeks, when the account cannot take
them all; 2020 flatters anything that buys falls.
