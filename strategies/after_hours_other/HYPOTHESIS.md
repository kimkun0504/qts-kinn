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
