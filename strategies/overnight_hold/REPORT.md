# Overnight hold: the night belongs to some stocks, until 2018

**Verdict: not passed.** 30 trials in three readings; the last reading's three cells passed
2005–2009 and failed 2018–2022. The holdout is untouched.

Plan: [HYPOTHESIS.md](HYPOTHESIS.md). An indicator of our own: where a stock's gains have come
over the last 20 or 60 sessions, between the close and the next open or during the session.
The 10 stocks of a size group whose gains have come most at night, bought in the closing
auction and sold in the opening auction (or the reverse by day). Every listed common stock of
$50M or more and $5 or more, with no results due, 2005 to October 2023. Code:
`research/claude/overnight_hold.py`.

## First reading: the auction allowance (12 cells)

| 2010–2017, a session | Before costs | After the allowance | Weekly t |
|---|---|---|---|
| Night book, 60-session score, $50M–$300M | +0.30% | −0.13% | −5.66 |
| Night book, 60-session score, $300M–$2B | +0.24% | −0.005% | −0.32 |
| Night book, 60-session score, $2B+ | +0.14% | −0.02% | −1.02 |
| Night books, 20-session score | +0.08% to +0.28% | −0.08% to −0.15% | −4.6 to −7.1 |
| Day books (either score) | −0.06% to +0.01% | −0.15% to −0.51% | −4.6 to −11.4 |

The day books lose before costs; the night books gain before costs and the allowance written
for a different trade (0.20% to 0.50% a round trip) takes it all.

## Second reading: sold at the first minute's low (6 cells)

Every cell lost (−0.25% to −0.49% a night). The lowest price of the first minute is on
average about 0.5% under the official open (its median is 0% to 0.1%: a few opening
collapses), and a market-on-open order is filled at the cross, not there. Recorded as
written: failed.

## Third reading: auction prices where both auctions can be seen (6 cells, 6 test runs)

Only nights where the official close lies inside the prints from 16:00 to 16:05 and the next
day's first minute opened within 0.2% of the official open; commission and auction fees only.

| A session, after commission and fees | 2010–2017 | 2005–2009 | 2018–2022 |
|---|---|---|---|
| 60-session score, $50M–$300M | +0.306% (t 4.28, 8 of 8) | +0.673% (t 4.72, 5 of 5) | +0.016% (t 0.07, 2 of 5) |
| 20-session score, $50M–$300M | +0.235% (t 3.05, 7 of 8) | +0.567% (t 3.10, 5 of 5) | −0.115% (t −1.15, 2 of 5) |
| 60-session score, $300M–$2B | +0.162% (t 3.34, 7 of 8) | +0.322% (t 3.26, 4 of 5) | +0.049% (t 0.97, 2 of 5) |
| 60-session score, $2B+ | +0.075% (t 2.82) | not run | not run |

By year in 2018–2022 (60-session score, $50M–$300M): 2018 −1.8%, 2019 +25.0%, 2020 +319.6%,
2021 −73.3%, 2022 −55.8%. One to six stocks a night qualify.

- **Until 2017 the night belonged to some stocks**, steadily: a stock whose gains had come at
  night kept gaining at night, by a quarter to two thirds of a percent, after fees.
- **Since 2018 it has not**, except in 2020, and 2021 and 2022 lost most of the book. The same
  break shows in every short-horizon effect tested on 17 November.
- The result rests on auction prices; it was never a finding until checked with ticks, and
  now it does not need to be.

## Reproduce

```
cd research/claude
uv run python night_bids.py filings
uv run python overnight_hold.py table
uv run python overnight_hold.py search
uv run python overnight_hold.py picks
uv run python overnight_hold.py minutes 2005 2023
uv run python overnight_hold.py reprice search
uv run python overnight_hold.py crossed search
uv run python overnight_hold.py crossed_test 60 small
```
