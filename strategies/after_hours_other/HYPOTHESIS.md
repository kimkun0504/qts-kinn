# After hours, other news: a large after-hours move that is not a results release

Written 2026-11-17 23:37 ET, before anything is measured. The after-hours short (strategies/after_hours)
rests on one idea: after the close the first prices are set by few traders, and the funds that
must act do it at the next open. Nothing in that idea is about results. This study asks whether
the same holds for every other large after-hours move in small and mid-sized companies: a
guidance cut, a share offering announced after the close, a drug decision, a lost contract, a
deal. It is a sister family, kept apart from after_hours' trials.

## Events

Every session D from 2005 to 13 October 2023 and every stock in the price table that is
common stock, $50M to $2B in market value, $250,000 a day or more and $2 or more at the last
close. Minute bars after the close (16:01 to 19:30), against the last regular-session minute's
price.

**Reading:** the first after-hours minute k at which (a) $50,000 or more has traded after
hours, (b) $5,000 or more traded in that minute, and (c) its price is 10% or more below the
last regular price (a fall) or 10% or more above it (a rise). **Entry:** the next minute with
trades, if it comes within 20 minutes, sold short at its low after a fall or bought at its
high after a rise (the harsh side of the minute, as in after_hours).

**Kind**, by the SEC's acceptance times of the company's 8-Ks from 15:30 on D to 09:30 on
D+1: *results* (any 8-K with item 2.02; these are the after_hours lead's ground and are kept
out of the cells), *other 8-K*, or *none* (news by press release only, or no news on file).

## Exits and costs

Bought back or sold at the open of D+1, or at the close of D+1. Costs: the auction allowance
by the stock's dollar volume, commission both ways, and for shorts a night's borrow at 10% a
year (one night to the open, the same to the close).

## Cells

kind (other 8-K, none) × side (short after a fall, long after a rise) × size ($50M–$300M,
$300M–$2B) × exit (next open, next close) = **16 cells**, family `after_hours_other`. One
more reading, results / fall / $300M–$2B / next open, is printed beside them only to compare
this reading with the lead's; it is counted as a trial. **17 trials.**

## What counts

Search 2010–2017: 150 trades, 1% a trade after costs, weekly t of 3, six years of eight.
Tests on 2005–2009 and 2018–2022 for any cell that meets it: 0.5%, t of 2.5, four years of
five. 2023 is a check for a cell that passes both. The holdout stays sealed.

## Follow-up: selling short a no-news rise (written 2026-11-17 23:47 ET, after the 16 cells were read)

Rises of 10% after hours with no 8-K gave back overnight in 2010–2017 when bought (above). The
opposite trade was not measured: **sold short at the low of the entry minute** (the harsh side
for a seller), bought back at the next open or close, with the same costs and a night's
borrow. Because the search years have been seen in the mirror, they are read only to see that
the short clears the bar after its own fill; the evidence is the test years.

Stricter events: no 8-K and no 6-K by the company accepted from the day before D to four days
after it (results filed late and foreign companies' results drop out).

**4 cells:** size ($50M–$300M, $300M–$2B) × exit (next open, next close). Same bars: search
150 trades, 1% after costs, t of 3, six years of eight; tests 0.5%, t 2.5, four of five.

## Follow-up 2: buying a no-news fall (written 2026-11-17 23:52 ET, after follow-up 1 was read)

The 16 cells showed that selling short after a no-news fall lost money overnight (it bounced).
The opposite trade: the same stricter events (no 8-K or 6-K from the day before to four days
after), a fall of 10% or more after hours, **bought at the high of the entry minute**, sold at
the next open or close; the auction allowance and commission. **4 cells:** size × exit. Same
bars as above; the search years have been seen in the mirror, so the test years are the evidence.
