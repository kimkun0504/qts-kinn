# Runner close: a stock that has run on the day, into the close and overnight

Written 2026-11-17 17:39 ET, before anything is measured. The owner's observation today: "I
see steep drops at closing (for example see SLS). Stocks that overran on good news yet had
no bottom support."

## Why

A stock up 30% or more on the day is either still at its high in the last hour or already
giving it back. The owner's eye says the ones that have lost their footing collapse into the
close. If so there are three trades: sell short the ones fading, buy the ones holding, or
leave both alone and learn when to get out of a position that has run. None of the tests
so far looked at the last hour or at the overnight after a run.

## Events

At 15:00 on day D: the day's high so far is 30% or more above the previous close, and the
dollar volume so far is 5 times the stock's normal day. Common stock, market value $50M or
more (before the run), $250,000 a day, last price $1 or more. 2005-01-03 to 2023-10-13.

Two sizes of run: 30% to under 60% at the high; 60% or more. Two states at 15:00:
**holding** (the last trade is within 10% of the day's high) and **fading** (25% or more
under it). Runs in between are counted and not traded.

## Trades, from 15:00

- **Holding, bought:** to the close; to the next open; to the next close.
- **Fading, sold short:** to the close; to the next open.
- **Fading, bought at the close** (does it bounce?): to the next open.
- **Any state, sold short at the close:** to the next open (the overnight after a run), for
  holding and for fading separately.

That is (3 + 2 + 1 + 1) = 7 trades for each state pairing as listed, by two sizes of run:
**16 cells** (holding: 3 bought + 1 short at the close; fading: 2 short + 1 bought + 1 short
at the close; each × 2 sizes). Family `runner_close`.

**Prices and costs.** At 15:00 a buyer pays the high and a short seller receives the low of
the first minute from 15:00 (the worst price of the minute), plus commission. The close and
the open are auctions: the allowance and commission. **Borrow is not charged and not
checked.** These are the stocks least likely to be borrowable, so a short cell that passes
is a finding to check against a broker's list, not a trade.

## Periods and what counts

- **Search: 2010 to 2017.** A cell goes forward only with 150 trades or more, a mean of 1% or
  more a trade after costs, a weekly t of 3 or more, and six years of eight positive.
- **Test: 2005 to 2009 and 2018 to 2022,** each cell that goes forward run once. Pass: 0.5%
  or more, weekly t of 2.5, four years of five positive, in both.
- **Check: 2023 to 13 October,** once. **Holdout: from 2023-11-09, sealed.**

## Known before starting

Stocks up 50% before the open fade by the close (`recent_search`, about 5% to a short
seller before borrow); a 30% jump with no filing in a small company fell 12% in three weeks
on 115 trades (`short_search`). The last hour and the overnight after a run have not been
measured.

**Results, 2026-11-17 17:41 ET.** In REPORT.md. No cell meets the bar, so no test was run. 16
trials. Of the runners at 15:00 in 2010 to 2017, 1,690 were holding and only 52 were fading
by the plan's definition (25% under the day's high), too few to say anything; 3,400 across
all years sat between the two and were not traded.
