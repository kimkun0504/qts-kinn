# Intraday shape: what a stock does in the first and last half hour, day after day

Written 2026-11-17 22:25 ET, before anything is measured. An indicator of our own, from a measurement no
daily chart carries. Every search here used daily prices (open, high, low, close); none
looked at **when in the session** a stock moves. Large orders are worked over many days, and
the algorithms that work them aim at the open or, more and more, at the close. A stock that
rises in the last half hour session after session, or in the first half hour, may have a
buyer who is not finished.

## Measurement

From minute bars, for every listed common stock of $50M or more and $250,000 a day, every
session 2005 to 13 October 2023 (in the universe of `night_bids`' daily table):

- **First half hour:** the official open to the close of the 09:59 minute.
- **Last half hour:** the close of the 15:29 minute to the official close.

## Rule

Each session D: the **score** is the sum of a stock's log returns in that half hour over the
last 10 sessions to D. The 10 stocks with the highest score in a size group are bought at
D+1's open and sold at the close 5 or 10 sessions later. Every stock-day in the top 10 is a
trade (books overlap). Costs: the auction allowance and commission, as the earnings rule. A
stock-day is used only if both half-hour prices exist.

## Cells

2 half hours × 2 holds × 3 sizes ($50M to $300M, $300M to $2B, $2B or more) = **12**,
family `intraday_shape`.

## What counts

The swing search's bar: search 2010–2017, 1% a trade after costs, weekly t of 3, six years
of eight, 150 trades. Tests on 2005–2009 and 2018–2022, each cell that goes forward run once:
0.5%, t of 2.5, four years of five, in both. Each cell is also shown over the average stock
of its size group on the same days. 2023 is a check for a cell that passes. The holdout stays
sealed.

**Search result, 2026-11-17 22:28 ET.** In REPORT.md. **None of the 12 cells meets the bar, and the
last-half-hour cells point the other way:** the 10 stocks most pushed up into the close over
10 sessions **trail the average stock** of their size by 0.48% to 1.36% over the next 5 to 10
sessions (weekly t −3.7 to −6.3), and lose after costs in most years. The first-half-hour
cells are near zero (small companies slightly negative). 12 trials.

## Addendum, 2026-11-17 22:28 ET: the other end, bought

Written after the search above showed the reversal, before anything below is measured; the
test periods of this family are still unseen. If a stock pushed up into the close day after
day gives it back, one pushed **down** into the close day after day (persistent selling at the
end of the session, which the closing-auction study tonight found comes back overnight) may
be the one to buy.

**Rule.** As above, but the 10 stocks with the **lowest** score in the size group (the most
negative sum of last-half-hour returns over 10 sessions; and, separately, of first-half-hour
returns), bought at D+1's open, sold at the close 5 or 10 sessions later.

Cells: 2 half hours × 2 holds × 3 sizes = **12**, the same bar. Charged to
`intraday_shape`. A short of the top cells is not tested here: in companies of $2B or more
it would make about 0.5% before borrow, under the bar.
