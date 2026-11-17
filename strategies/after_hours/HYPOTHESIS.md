# After hours: buying an earnings reaction outside the regular session

Written 2026-11-17 17:32 ET, before anything is measured. The owner's instruction: think
outside what everyone does; find ways to enter earlier; "one thing I also think has a big
edge is after hours trading. Especially if trading sizes are below 5k."

## Why

Every test so far bought during the regular session, and each found the same thing: by the
time the market is open, the news is priced. Results are mostly released after the close or
before the open, when few trade, spreads are wide and large orders cannot be filled. That is
where a small order can do what a fund cannot. If the price in those hours is only part of
the way to where the stock opens, a buyer of $5,000 or less gets in before the jump that
rule A50 buys after. This has not been looked at: no test here has used a price from
outside 09:30 to 16:00 as an entry.

## Events

An earnings 8-K (item 2.02), by the SEC's acceptance time, 2005-01-03 to 2023-10-13:

- **After the close:** accepted from 16:00 to 18:30 on a session day D.
- **Before the open:** accepted from 06:00 to 08:30 on a session day D.

Common stock, market value $50M or more, $250,000 a day. Sizes: $50M to $300M, $300M to
$2B, $2B and over.

## The reading and the trade

- **After the close.** Read 30 minutes after the acceptance (not before 16:30, not after
  19:30): the last trade then against the 16:00 close. At least $50,000 must have traded
  since 16:00, so that $5,000 is a tenth of it or less.
- **Before the open.** Read at 09:00: the last trade against the previous close. At least
  $50,000 traded since 04:00.
- **Buy** in the first minute that trades after the reading (within 20 minutes), **at that
  minute's high**: the spread outside regular hours is wide and not on disk, so the worst
  price of the minute stands in for it. Plus commission.
- **Two reactions:** up 5% to under 15%; up 15% or more. (The paths after a fall or no move
  are shown in the report, not traded.)
- **Exits.** After the close: the next session's open; the next session's close; the close
  15 sessions after that session. Before the open: that session's close; the close 15
  sessions after it. Exit costs: the auction allowance and commission.

Cells: after the close 3 sizes × 2 reactions × 3 exits = 18; before the open 3 × 2 × 2 = 12.
**30 trials**, family `after_hours`.

## Periods and what counts

- **Search: 2010 to 2017.** A cell goes forward only with 150 trades or more, a mean of 1% or
  more a trade after costs, a weekly t of 3 or more, and six years of eight positive.
- **Test: 2005 to 2009 and 2018 to 2022,** each cell that goes forward run once. Pass: 0.5%
  or more, weekly t of 2.5, four years of five positive, in both.
- **Check: 2023 to 13 October,** once. **Holdout: from 2023-11-09, sealed,** not read by this
  family.

## What could make a result untrue

- The fill. A minute's high is a harsh price when the minute is busy and a kind one when one
  small trade printed; the report gives the share of entries whose minute had under $5,000.
  Anything that passes needs quotes from those hours before it means anything.
- The press release comes before the 8-K, so the reading can be later than the news by more
  than 30 minutes. That makes the entry later, never earlier, than a trader could manage.

## Known before starting

At 09:35 after a report before the session, a stock up 5% or more makes 0.6% to 0.9% over a
week after costs (`news_hours`); buying A50's jump during the next session does not beat
waiting (`swing_search`, family 23). Nothing from extended hours has been measured.

**Results, 2026-11-17 17:37 ET.** In REPORT.md. Search: five cells met the bar, all after the
close with a reaction of 5% to 15% (small held 15 sessions; mid to the next open, the next
close and 15 sessions; large held 15 sessions). Tests, each run once on 2005–2009 and
2018–2022: none passes both. Mid to the next open passed 2005–2009 (0.76%, t 2.71, five
years of five) and failed 2018–2022 (0.11%; negative in 2020, 2021 and 2022). Large for 15
sessions passed 2005–2009 (1.86%, t 4.37) and missed 2018–2022 on the t (1.35%, t 1.95,
three years of five). 30 cells and 10 test runs: 40 trials.

**Note, 2026-11-17 17:38 ET.** While checking the report's year-by-year sentence I printed
every year for one cell (mid, up 5% to 15%, sold at the next open), which showed its 2023
figure: +1.59% on 101 trades. The 2023 check was reserved for a cell that passed, and this
one had not. It is recorded here as seen; for this cell 2023 is no longer an unseen check.

## Addendum, 2026-11-17 17:42 ET: the other side, selling short after hours on a bad report

Written before it is measured. The path table of the first part showed (search years, every
size together, measured from the minute's high) that a stock down 5% or more 30 minutes
after its report was another 1.1% lower at the next open and 1.2% lower at the next close.
That is known. Not known: what a short seller would have made, by size and by how far the
stock had fallen, and on the other years. The owner allowed short research today. Unlike the
other short ideas, the larger companies here are easy to borrow and the hold is one night.

Same events, reading and liquidity floor as the first part (reports after the close only).
**Sell short at the low of the first minute that trades after the reading.** Buy back at the
next session's open, or at its close. Costs: the auction allowance and commission, and a
borrow fee of 10% a year for the night.

Cells: 3 sizes × 2 reactions (down 5% to under 15%; down 15% or more) × 2 exits = **12**,
charged to `after_hours`.

**What counts:** as the first part. Search 2010–2017: 150 trades, 1% after costs, weekly t
of 3, six years of eight. Tests on 2005–2009 and 2018–2022, each cell that goes forward run
once: 0.5%, t of 2.5, four years of five, in both. For any cell that goes forward the report
gives the worst trade and the worst 1%, since a short's loss has no limit. Whether the
shares can be borrowed after hours at a retail broker is not known and is the first thing to
check if anything passes.
