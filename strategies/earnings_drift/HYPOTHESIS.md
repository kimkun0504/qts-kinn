# Hypothesis: earnings drift in companies of $50M to $300M

Written 2026-11-16, after the rule was found and tested in
[`strategies/swing_search`](../swing_search/REPORT.md) (rule A50) and before any run of this
folder. This folder holds the rule as something `kinn swing` can run, so that the owner can
run it once on the holdout. It adds no new idea and no new parameter.

## The rule, frozen

- **Signal,** read at a close: the company is common stock worth $50M to $300M, closed at $1
  or more and normally trades $250,000 or more a day; it filed an earnings 8-K on the
  previous session or since; its two-day return is 15% or more; the larger of the two days'
  dollar volume is at least five times normal.
  A stock whose previous session was more than 7 days earlier gives no signal: its "two-day
  return" would span a halt. The research scripts did not have this line; it removes nine
  of their 1,488 trades of 2005 to 2022, stocks back from a halt or a relisting.
- **Trade:** buy at the next open, sell at the close 15 sessions after the signal day. If the
  stock stops trading first, the position ends at its last close with the forced-exit cost.
- **Book:** $20,000, 10 positions of $2,000, no leverage. A signal needs a free slot at the
  open; when several arrive together the one with the most volume against normal goes first.
- **Costs:** commission and fees from the cost model; slippage at 1× is an allowance for
  joining the auctions (25 bp a side under $1M a day, 10 bp to $10M, 5 bp to $100M, 2 bp
  above); 2× doubles it. The result with the quoted spread crossed is reported beside them.

## Why it might be real

A small company's good earnings reach few investors on the day. The search found the drift in
2010 to 2022, and it then passed on 2005 to 2009, on 2018 to 2022 as a test of the $50M floor,
and was not contradicted by 2023. It is the long-documented drift after earnings, in the
stocks too small for funds to trade.

## Why it might not be

It was picked out of about 12,000 cells. The profit is in the best 5% of trades. The allowance
for auction fills is assumed, not measured. Half the account can be lost in the 10-position
book.

## Runs planned

1. `research` and `early`: the search years and 2005 to 2009, to confirm that this code
   reproduces the research scripts' trades. These add no trial: same rule, same data.
2. `holdout`: 2023-11-09 to 2026-11-06, once, by the owner, with `--unseal`. Set now: the rule
   **passes** if the mean a trade at 2× is 1% or more and the run's total at 2× is positive;
   it **fails** if the mean a trade at 1× is zero or less. In between it is unproven.
   About 250 trades are expected, so the mean will be known to about ±1.5%.

## Addendum, 2026-11-16 14:40 ET: the fill measurement, written before any tick is read

The owner has downloaded the tick sample (150 trades of 2015 to 2023 at random: quotes and
trades from 09:25 to 09:40 on the entry day and 15:50 to 16:02 on the exit day) and has run
the holdout. The holdout result is recorded in REPORT.md. The ticks answer three questions,
each for stocks under and over $1M a day:

1. **Is the bar's price an auction price?** The share of entries with an opening-cross print
   (trade conditions 25 or 17) and of exits with a closing-cross print (8 or 19), the dollars
   in each cross, and how far the cross price is from the bar's open or close.
2. **Is the auction price a fair one?** The opening cross against the quote midpoint 30
   seconds after the open, and the closing cross against the midpoint 30 seconds before the
   close. A buyer in the cross pays this difference; near zero means the cross is not
   systematically on the wrong side.
3. **What does a market order pay instead?** The ask 30 seconds after the open against the
   bar's open, and the bar's close against the bid 30 seconds before the close. Their sum is
   the measured cost of trading without the auctions, to set beside the modelled spread
   (1% a side under $1M a day, 0.43% above).

**What it changes.** The auction allowance (0.25% a side under $1M a day, 0.10% above) stands
if at least nine trades in ten have a cross on both sides and the mean of question 2 is
within the allowance. Otherwise the figure to use is question 3's. Either way the reports
state the measured numbers. The ticks cannot show what the order's own size does to a cross;
with the median cross size they bound it.

## Addendum, 2026-11-16 23:30 ET: the quality test (rule A50Q), written before any run of it

The flat-years study (strategies/swing_search/REPORT.md) found that A50's signals in fallen,
cash-rich companies make nothing. The rule with that test added is fixed here, before the
runner has produced a number for it.

**A50Q.** Rule A50, and the signal is taken only if at least one of these holds at the
signal's close:

1. the stock's return over the 250 sessions to that close is above zero;
2. the company's debt is above its cash at the last quarterly report filed before the
   signal day (Sharadar's `debtusd` and `cashnequsd`, dimension ARQ; since 2019 that debt
   includes operating leases).

A fact that is missing does not qualify the signal. Everything else is A50: entry at the
next open, exit at the close 15 sessions after the signal day, the same book and costs.
In the runner it is `skip_fallen_cash_rich: true` on the rule; a run writes every signal,
kept or skipped, to `signals.parquet` with what it did before costs.

**Runs.**

1. `research_quality`, `early_quality`, `check_quality`: the years already read, to check
   that the runner reproduces the research script (which found 1,177 kept of 1,551 signals
   and a book of about $5,100 a year). No new trial: same rule, same data.
2. `holdout_quality`: 2023-11-09 to 2026-11-06, **only if the owner decides to**, once, with
   `--unseal`. The holdout is already spent for this family: rule A50 was run on it once and
   made 5.04% a trade, and its years are known (2026 was flat). This would be a second look.
   What keeps it worth something is that the 460 holdout signals have never been split by
   this test and the test is fixed above. Set now, how it is read:
   - **Supports the test** if the skipped signals' mean return before costs is under the
     kept signals' mean by one point or more, and the kept book's total at doubled costs is
     positive.
   - **Against the test** if the skipped signals did as well as or better than the kept.
   - In between, unproven. With about 110 skipped signals the difference is known to about
     ±3 points, so only a clear gap means anything.
   Whatever it shows, the forward record on the paper ledger is the cleaner evidence.
3. **Paper ledger:** two more books, the same sizes with the test applied, beside the two
   that take every signal. The facts come from the vendor's adjusted daily bars (the year's
   return) and the SEC's XBRL company facts (cash, debt and lease liabilities), which
   approximate Sharadar's fields; each signal records the figures used.

## Addendum, 2026-11-16 23:49 ET: a fifth paper book with the 20-day-average exit

Written before the ledger has taken a position by it. The study of A50Q's drawdown
(swing_search REPORT.md, family 21) found that rules about what to open next do not lower
it and the 20-day-average exit does ($10,366 to $7,601), because it acts on what is held.
That exit had already passed the terms set for it in the exit study. With the quality test
it gives the best book that rests on tests set beforehand ($5,783 a year, Sharpe 1.30, no
losing year on either cost basis, on years already read).

**Book `ten_quality_trend`:** A50Q's signals, 10 positions of $2,000. A position is sold at
the next open once a close is under the stock's 20-day exponential average (checked from
the session after the entry), and at the close of the 30th session after the signal at the
latest. Costs as for the other books. Holds can run to six weeks, past the three the owner
set for the search, which is why it is a separate book and not a change to the rule.

The ledger's exit was checked against the research's on 220 real signals fed through it:
the same exit day and return in all 220 with the research's own bars, and in 218 with the
45-session window the nightly tool fetches (the average starts from a later bar).

## Addendum, 2026-11-16 23:59 ET: one season nobody has looked at (autumn 2004)

Written before the run. Every study of this family used signals from 2005 on. The data
begin in September 2003, and the 8-K item for earnings (2.02) exists from 23 August 2004;
before that date earnings releases cannot be told apart in the events table. So the months
from 24 August to 31 December 2004 hold one earnings season (October and November 2004)
that no rule here has been fitted on or tested on, and the 250-session return exists for it.

**Run:** `autumn_2004_quality`, rule A50Q, the usual book, once. About 30 signals are
expected, so this cannot settle anything: a mean is known to perhaps ±6 points and the
skipped group will be a handful. It is recorded as one more unseen season and read only
this way: **consistent** if the kept signals' mean before costs is positive and the book's
total at doubled costs is positive; **a warning** if the kept signals lose. The kept against
the skipped is reported and not read as evidence either way unless 20 or more are skipped.
One trial.

**Result, 2026-11-16 23:59 ET.** 33 signals, 19 kept (12.8% each before costs), 14 skipped
(7.2%). 17 trades, 12.57% a trade, $4,263 ($4,077 doubled). Consistent, by the reading set
above; the skipped are under 20 (and six of them were skipped only because the prices do not yet
reach back a year), so the gap between kept and skipped is not read as evidence.

## Addendum, 2026-11-17 15:34 ET: how much of the account the book uses, and fewer, larger positions

Written before the books below are measured. Counting positions held day by day (2006 to
October 2023) shows the 10-position book is mostly empty: A50Q holds 3.3 positions on average,
a third of the account; it is full on 5% of days and holds nothing on 16%. Signals come in
the four reporting seasons (about 6 held in February–March, May, August and November; 1 to 2
in between). The owner has said $1,000 positions feel small.

**Measured:** the $20,000 book of A50Q with 5, 7 and 10 positions ($4,000, $2,857, $2,000
each), with the 15-session exit and with the 20-day-average exit, on the auction basis and
with the spread crossed: dollars a year, Sharpe, worst drawdown, worst year, losing years,
signals taken. The priority within a day stays the most volume against normal. 4 new trials
(5 and 7 positions, two exits), charged to `swing_search`.

**How it will be read.** Nothing is adopted from this table. Fewer positions put more of the
account to work and make the result depend on fewer trades; the table shows the price of
that. If a count looks better it becomes one more paper book, since the choice is being made
on years already read. Also reported, not a trial: what the idle cash would earn in Treasury
bills.

**Results, 2026-11-17 15:34 ET.** In REPORT.md. Fewer positions make more dollars and lose
more: 7 positions $6,298 a year (drawdown $14,487), 5 positions $7,043 (drawdown $20,486,
the whole account, two losing years), against 10 positions $5,097 ($10,366). With the
20-day exit: $6,692 ($10,408, one losing year), $7,901 ($11,968, two) and $5,783 ($7,601,
none). The Sharpe ratio falls with every step. No count is added to the paper ledger; the
choice is the owner's. 4 trials.
