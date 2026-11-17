# Short search: stocks to sell short for one to three weeks

Written 2026-11-17 14:55 ET, before anything in this family is measured. The owner allowed
research on short selling today ("yes you can research short selling").

## Why

Every search so far was for a buyer, and the largest effects it met were falls: stocks up
50% before the open fade by the close (`recent_search`), an earnings jump given back by the
close keeps falling for three weeks (`swing_search`, family 23), earnings jumps in companies
under $50M lose (`swing_search`). A short seller is paid for those. None has been tested as
a short, with a short's costs, on years it was not found in.

## What a short costs that a purchase does not

- **Borrow.** There is no stock-loan data on disk. A fee of **10% a year** on the position is
  charged for the days held (0.60% for 15 sessions). Each result is also given as the fee
  at which it breaks even. Shares that cannot be borrowed at all are the real risk and are
  not modelled; the universe below is chosen to make that less likely, and anything that
  passes must be checked against a broker's shortable list before it means anything.
- **The loss has no limit.** For every cell the report gives the worst trade and the worst
  1% of trades, not only the mean.
- **The market rises.** A short pays the market's drift. Each result is shown raw and
  against the average stock over the same days.
- **The short-sale rule** (no short at the bid after a 10% fall) binds on the day of a fall
  and the next. Entries here are at the next session's open, which the rule allows above
  the bid; fills on a restricted day are a risk to measure if anything passes.

## Universe

Common stock, market value $50M or more, close $3 or more, normal dollar volume $1M or more
(all as of the signal day). Companies under $50M and stocks under $3 are left out: they are
where borrow is least likely. Three sizes: $50M to $300M, $300M to $2B, $2B and over.

## Family `swing_short`: 24 cells

The signal is read at the close of S. Sell short at the open of S+1, buy back at the close
5 or 15 sessions after S. Four events, three sizes, two holds.

1. **A fall on earnings.** An earnings 8-K since the previous session, a two-day return of
   −15% or worse, the larger of the two days' volume 5 times normal (A50 turned over).
2. **An earnings jump given back.** An earnings 8-K since the previous session, the high of S
   15% or more above the close of S−2 on 5 times volume, and the close of S less than 15%
   above it.
3. **A jump with no news.** A one-day return of 30% or more on 5 times volume, no 8-K and no
   other filing on S or the day before, no earnings.
4. **A run-up.** Up 100% or more over 20 sessions, at a 250-session high.

**Costs:** the auction allowance and commission on both sides (as the buyer's studies), plus
the borrow fee.

## Periods and what counts

- **Search: 2010 to 2017.** A cell goes forward only with 150 trades or more, a mean of 2%
  or more a trade after all costs, a weekly t of 3 or more, at least 6 of the 8 years
  positive, and a mean above zero against the average stock.
- **Test: 2005 to 2009 and 2018 to 2022,** for cells that go forward, each run once. Pass:
  1% or more after costs, weekly t of 2.5 or more, 4 of 5 years positive, in both.
- **Check: 2023 to 13 October,** once, for a cell that passes.
- **Holdout: from 2023-11-09, sealed.** This family has not looked at it. One run, by the
  owner, of one frozen rule.

24 trials in the search; each test run is one more.

## Known before starting

The buyer's studies showed me these groups from the other side, on all years: the fall
after a given-back earnings jump (5% to 8% over 15 sessions from the moment of the touch,
$50M to $300M, bought during the session), and that jumps with no filing "do not drift".
Neither was measured from the next open, with a short's costs, or in this universe. Cells
1 and 4 I have not seen. This is why the search years prove nothing by themselves and the
tests are the evidence.
