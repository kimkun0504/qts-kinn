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

**Result of the other end, 2026-11-17 22:29 ET.** In REPORT.md. None of the 12 cells meets the bar. The
stocks most pushed **down** into the close do a little better than the average stock (small,
10 sessions: +0.72% over it, t 3.04; +0.36% after costs), much less than the stocks pushed up
do worse. The first-half-hour ends are both slightly negative. 12 trials; `intraday_shape`
has 24.

## Addendum, 2026-11-17 22:29 ET: both ends at once, where shares can be borrowed

Written after both ends were seen on 2010–2017, before any test period is looked at. The
effect is lopsided: the push up into the close predicts; the push down barely does. A book
that owns the 10 most pushed down and is short the 10 most pushed up, in companies large
enough to borrow freely, takes the market out and keeps both.

**Rule.** Each session D, in a size group: long the 10 stocks with the lowest last-half-hour
score, short the 10 with the highest, both at D+1's open, both closed at the close 5 or 10
sessions later. The trade's return is the long leg's average after costs plus the short leg's
average after costs, halved (a return on the gross money). Short costs: the auction allowance
and commission, and borrow at **1% a year** (general collateral for companies of this size at
a retail broker is well under that; a short of any of these that cannot be borrowed is the
risk said in the report).

Cells: 2 sizes ($300M to $2B; $2B or more) × 2 holds = **4**, charged to `intraday_shape`.

**What counts (set now, for a market-neutral trade).** Search 2010–2017 (already seen through
its legs, shown for the record): 0.4% a trade for 10 sessions, 0.2% for 5, weekly t of 3,
six years of eight. Tests on 2005–2009 and 2018–2022, run once each: **0.2% a trade for 10
sessions, 0.1% for 5, weekly t of 2.5, four years of five, in both.**

**Result of the pair, 2026-11-17 22:30 ET.** **None of the 4 cells meets the bar** (0.20% a trade for 10
sessions in $2B or more, weekly t 1.79; 0.22% and t 1.50 in $300M to $2B). The stocks most
pushed up into the close are thin and cheap for their size: costs both ways average 0.21% in
$2B or more, and the short leg keeps 0.03% of their 0.29% fall. 4 trials; `intraday_shape`
has 28. No tests run.

## Addendum, 2026-11-17 22:33 ET: an exit for the earnings rule (the owner's "exit better")

Written before it is measured. The finding above (a stock pushed up into the close gives it
back) may help the one rule that works: an A50 holding that spikes in the last half hour may
be better sold than held to the 15th session. Exits for A50 were compared on 16 November
(holds, stops, targets, trailing stops, averages) and none beat the plain rule in all three
periods; this adds four, judged the same way.

**Trades:** every A50 signal from 2005 to 13 October 2023 (bought at the next open; plain exit
at the close 15 sessions after the signal). **Variants:** sell at the next open after the
first session, among the 14 held before the last, whose last-half-hour return (15:29 price to
the official close) is **4% or more**; **2% or more**; or whose last-half-hour returns over the
last three held sessions add up to **6% or more**; **3% or more**. Costs as A50 (the auction
allowance both ways).

**How it is read:** each variant against the plain rule on 2010–2017, 2005–2009 and 2018–2022
apart (2023 shown). A variant is better only if it beats the plain rule's mean a trade in all
three. **4 cells**, charged to `intraday_shape`.

**Results of the A50 exits, 2026-11-17 22:33 ET.** In REPORT.md. 1,558 A50 trades with a full path. **One
variant beats the plain rule in all three periods:** sell at the next open after a held
session that rose 4% or more in its last half hour (3.59% against 3.26% in 2010–2017, 4.61%
against 4.47% in 2005–2009, 4.27% against 4.13% in 2018–2022; 2023 5.43% against 5.95%). It
fires in about one trade in eleven (39, 47 and 50 trades), changing those by +5.1, +1.3 and
+1.3 points, paired t 2.06, 0.48 and 0.30. Better by the rule set, on too few firings to be
sure; the other three variants are not better in all three. 4 trials; `intraday_shape` has
32.

## Addendum, 2026-11-17 22:44 ET: the push into the close, in the most traded large companies

Written before it is measured. The parent cells of 2010–2017 are seen (large companies pushed
up into the close for 10 sessions trailed the average stock by 0.48% in 5 sessions and 0.73%
in 10, weekly t −5.6 and −5.0); the short failed only on costs, because the stocks it picked
were thin. This asks whether the effect lives in stocks that cost almost nothing to trade or
borrow, where a short is practical for the owner. The test periods of this family are unseen.

**Universe:** listed common stock of $2B or more, **$50M a day or more, a price of $10 or
more**. **Rule:** each session, the 10 with the highest last-half-hour score over 10 sessions,
**sold short** at D+1's open and bought back at the close 5 or 10 sessions later, with SPY
**bought** for the same money over the same sessions (open to close). Costs: the auction
allowance and commission both ways on the stocks, 0.03% on SPY, borrow at 1% a year. A second
version also buys the 10 with the lowest score instead of SPY (long-short, both legs priced as
above).

Cells: 2 hedges (SPY; the 10 lowest) × 2 holds = **4**, charged to `intraday_shape`. **What
counts:** search 2010–2017 (shown; the parent is seen): 0.3% a trade for 5 sessions, 0.5% for
10, weekly t of 3, six years of eight. Tests on 2005–2009 and 2018–2022, run once each: half
those, weekly t of 2.5, four years of five, in both.

**Result in the most traded large companies, 2026-11-17 22:45 ET.** **None of the 4 cells meets the bar.**
Short with SPY bought against it: 0.07% a trade for 5 sessions (t 1.48), 0.21% for 10 (t
2.74); long-short: −0.01% and 0.09%. In stocks of $50M a day and $10 or more the push into the
close predicts almost nothing; the effect is in the thinner stocks, where the short costs too
much. 4 trials; `intraday_shape` has 36. No tests run.

## Addendum, 2026-11-17 22:53 ET: the warning as a filter on the two rules that work

Written before it is measured. The one finding of this family that holds (a stock pushed up
into the close for two weeks trails other stocks) could keep the two passed rules out of such
stocks. **Filter:** skip a signal when the stock's last-half-hour score over the 10 sessions to
the signal day is in the top fifth (or top tenth) of all stocks of $50M to $300M that day.

Applied to **rule A50** (every signal 2005 to 13 October 2023, as in the exits above) and to
**rule I** (insider buying: $50M to $300M, $100,000 or more bought on one filing date, one
signal a company in 21 days, held 15 sessions; its research signals). Judged as the exits:
a filter is better only if the kept signals beat all signals, in the mean a trade after costs,
in all three periods (2010–2017, 2005/2006–2009, 2018–2022; 2023 shown). The skipped group is
shown. **4 cells** (2 rules × 2 cut-offs), charged to `intraday_shape`.

**Results of the filters, 2026-11-17 22:54 ET.** In REPORT.md. **Neither filter is better in all three
periods for either rule.** A50, skipping the top fifth: kept 3.66% against 3.26% (2010–2017),
4.97% against 4.49% (2005–2009), **3.71% against 4.13% (2018–2022)**, and in 2023 the skipped
did best. Rule I, skipping the top fifth: **2.72% against 3.22% (2010–2017)**, 4.12% against
3.87%, 2.02% against 1.70%. On a day with news, buying into the close is part of the news and
does not reverse. 4 trials; `intraday_shape` has 40.
