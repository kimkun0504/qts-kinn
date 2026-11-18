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

**Results of the short side, 2026-11-17 17:44 ET.** In REPORT.md. Search: two cells met the
bar, both in companies of $300M to $2B down 15% or more after hours: bought back at the next
open (2.82%, 251 trades, weekly t 3.89, six years of eight) and at the next close (3.41%, t
3.03). Tests, each run once: 2005–2009 passed (2.98%, t 3.79, five years of five; 4.42%, t
3.12, five of five); 2018–2022 was positive in all five years and missed the weekly t (1.60%,
t 1.15; 2.10%, t 1.87). **Not passed** by the rule set beforehand. 12 cells and 4 test runs;
`after_hours` has 56 trials in all. The 2023 check has not been looked at for these cells.

## Addendum, 2026-11-17 20:41 ET: two indicators of our own for the long side

Written before it is measured. The owner asked whether indicators of our own could be built.
The first part used one crude reading (how far the price had moved 30 minutes after the
report). Two more readings of the same half hour, neither of which a daily chart can show:

- **Pressure:** the dollars traded after hours up to the reading, as a share of the stock's
  normal day (20-day dollar volume). A rise that many people traded into is agreed; a rise on
  little trading is a few orders.
- **Hold:** the reading as a share of the highest price reached between the close and the
  reading (1.00 is still at its peak; 0.50 has given back half). The same thought as the
  earnings rule's second session, inside the first half hour.

Only the two feature distributions were looked at before writing this (no returns): among
search-year reports after the close in companies of $300M or more with a rise of 5% or more
(1,802), the pressure thirds are cut at 6% and 22% of a normal day. Companies under $300M
have 213 such reports in eight years and are left out.

**Rule.** As the first part: results 8-K accepted after the close, reading 30 minutes later,
$50,000 traded after hours, **buy at the high of the next minute that trades**. Company
$300M or more, rise of 5% or more. Sold at the next open, the next close, or the close 15
sessions later.

Cells: pressure in three groups (under 6%, 6% to 22%, over 22%) × 3 exits = 9; hold in two
groups cut at the search-year median (taken without returns, after the collection) × 3 exits
= 6. **15 cells**, charged to `after_hours`.

**What counts:** as the first part. Search 2010–2017: 150 trades, 1% after costs, weekly t
of 3, six years of eight. Tests on 2005–2009 and 2018–2022, each cell that goes forward run
once: 0.5%, t of 2.5, four years of five, in both. An indicator is only worth keeping if its
groups differ: the report gives every group, not only the best.

**Results of the two indicators, 2026-11-17 20:44 ET.** In REPORT.md. Search: six cells met the bar
(pressure middle for 15 sessions; pressure high to the next close and for 15 sessions; hold
kept to the next close and for 15 sessions; hold faded for 15 sessions). The clearest was
hold kept to the next close: 1.75% after costs on 901 trades, weekly t 6.48, eight years of
eight, against 0.60% for the faded half. Tests, each run once: **none passes**. Every one of
the six made 0.2% to 1.1% a trade in 2018–2022 with a weekly t under 2, and lost in 2020
and 2021 or 2021 alone. Hold kept to the next close: 1.68% in 2005–2009 (t 2.57, four years
of five) and 0.46% in 2018–2022 (t −0.10). 15 cells and 12 test runs: 27 trials;
`after_hours` has 83 in all. The indicators sort the old years and not the recent ones:
the gain after a rise on results has been small since 2020 however it is cut.

## Addendum, 2026-11-17 20:59 ET: a resting order at the reading price instead of the minute's high

Written before it is measured. `night_bids` showed tonight what trading after hours costs:
a minute's best and worst prices can be 1% to 3% apart (measured afterwards: in a quarter
to a tenth of minutes; half trade at one price), and every test in this family paid the
worst one. The first part's long side made 0.9% to the next open **after** paying it. The
owner asked for better entries; the plain one is not to cross that gap.

**Rule.** As the first part (results 8-K accepted after the close, the reading 30 minutes
later, $50,000 traded after hours, a rise of 5% to under 15% or of 15% or more). At the
reading, a buy order rests **at the reading price** (the last trade before it) for 15
minutes. It is filled, at that price, only if a later minute in those 15 trades **below**
it. Not filled, no trade. Sold at the next open, the next close, or the close 15 sessions
later. Costs as the first part.

Cells: 3 sizes × 2 reactions × 3 exits = **18**, charged to `after_hours`.

**What is already known, and what that does to the reading.** These are the first part's
cells with a different fill, and the first part's results on all three periods are known
(five met the search bar; none passed 2018–2022 at the minute's high). A better fill raises
every period mechanically, so the search years say little here. What counts is whether a
cell clears the test bar in **both** 2005–2009 and 2018–2022 (0.5% after costs, weekly t of
2.5, four years of five) on the trades that fill, and how many fill. Each cell that meets the
search bar is run once on the tests. A pass is a candidate for paper trading, not a finding:
the order fills when the price comes back to it, which is the case a buyer should worry
about, and the fill itself is assumed from trades by the minute.

**Results of the resting order, 2026-11-17 21:02 ET.** In REPORT.md. About 64% of the orders fill (55%
to 92% by cell). **The better price is cancelled by which orders fill:** companies of $300M
to $2B up 5% to 15%, sold at the next open, made 0.79% on the 493 fills of the search years,
no more than buying at the minute's high made on every signal. The stock that comes back to
the order is the weaker one. One cell met the search bar: $2B or more, up 5% to 15%, held 15
sessions (1.45%, weekly t 3.20, seven years of eight). Tested once: 2005–2009 passed (1.21%,
t 2.68, four years of five); 2018–2022 made 1.45% and **missed** (t 1.98, three years of
five; 2020 −0.17%, 2021 −1.79%). 18 cells and 2 test runs; `after_hours` has 103 trials.

## Addendum, 2026-11-17 21:02 ET: is the large-company cell the stock or the market?

Written before it is measured. The one long cell that keeps making the same amount (1.2% to
1.5% for 15 sessions in all three periods, by either fill) is in companies of $2B or more
with a rise of 5% to 15%. Fifteen sessions of the market are worth about half a percent on
their own, and its bad years (2008, 2020) are market years. Two cells: that trade with **SPY
sold short for the same dollars over the same sessions** (SPY's close on the report day to
its close 16 sessions on; 0.03% added for its costs), by the minute's high and by the
resting order. Same bar and tests. **2 cells**, charged to `after_hours`.

**Results of the SPY-hedged cell, 2026-11-17 21:04 ET.** In REPORT.md. Search years: 1.08% a trade after
costs by the minute's high (860 trades, weekly t 2.80, seven years of eight) and 1.01% by the
resting order (698 trades, t 2.07, seven of eight). **Neither meets the search bar** (the t
of 3), so no tests were run. The market was about 0.4 of the cell's 1.5 points; the rest is
the stocks. 2 cells; `after_hours` has 105 trials.

## Addendum, 2026-11-17 23:10 ET: how robust is the short to the fill, and how crowded is it

Written before it is measured. The short ($300M–$2B, down 15% or more, sold at the low of the
next minute, bought back at the next open) is the lead being followed on paper. All its periods
are seen; these are not new rules but the same rule priced more harshly, to see whether the
result depends on the fill:

1. **Only entries whose minute traded $5,000 or more** (the others dropped).
2. **Sold at the lowest price of the five minutes after the reading** (from the first minute
   that trades), instead of the first minute's low.

Each is read on 2005–2009, 2010–2017, 2018–2022 and 2023 together with the plain rule. 2
trials. And, as a description that counts no trial: for the signals of 2018–2023 (the years
with short-interest data on disk), the short interest as a share of shares and as days to cover
at the last report before the signal, against all stocks of the same size.

**Results of the harsher fills, 2026-11-17 23:11 ET.** In REPORT.md. Only entries with $5,000 or more in
the minute: 3.20%, 2.66%, 1.61%, 6.48% (2005–09, 2010–17, 2018–22, 2023), about the same as the
plain rule. Sold at the worst of five minutes: 2.17%, 2.23%, **0.70%** (t 0.11), 5.28%. The thin
minutes do not carry the result; the price the order gets does, most in 2018–2022. Short
interest before the signal (2018–2023, 244 signals): median 8.2% of shares and 7.0 days to cover
against 2.7% and 4.6 for all stocks of the size; a tenth above 23%. 2 trials; `after_hours`
has 109.

## Addendum, 2026-11-17 23:12 ET: the short before the open

Written before it is measured. The short after the close works, by the reading of this family,
because the first prices after bad results are set by few traders and the funds sell later. The
same may hold for results filed **before the open** (06:00 to 08:30): the first part measured
only the long side there ("before the open: nothing").

**Rule.** As the first part's "before" events (results 8-K accepted 06:00 to 08:30; the reading
at 09:00 against the previous close; $50,000 traded in the premarket by then). Down **15% or
more**: **sold short at the low of the next minute that trades** (by 09:20), **bought back at
that session's close**. Costs: the auction allowance and commission, and a day's borrow.

Cells: 3 sizes ($50M to $300M, $300M to $2B, $2B or more) = **3**, the first part's bar
(150 trades, or fewer reported and taken on if the rest is met; 1%, t of 3, six years of eight;
tests at 0.5%, t 2.5, four of five). 2023 is a check. Charged to `after_hours`.

**Results of the short before the open, 2026-11-17 23:13 ET.** **None of the 3 cells meets the bar.**
2010–2017: $50M–$300M +1.63% (26 trades, t 0.70); $300M–$2B +2.44% (71, t 1.55); $2B or
more +2.87% (53, t 2.52, seven years of seven). Bad results before the open also keep falling
through the session, on too few signals for a rule. 3 trials; `after_hours` has 112.

## Addendum, 2026-11-17 23:18 ET: when to buy the short back

Written before it is measured. The short buys back at the next open; bought back at the next
close it made more in every period (3.41% against 2.82% in 2010–2017), so the selling goes on
into the session. Two more exits from the minute bars of the next session: **the price at 10:00**
(the close of the last minute before it) and **at 15:30**. Judged as the exits of the earnings
rule: an exit is better only if it beats the open in all three periods (2023 shown). The 10:00
and 15:30 prices are bought back with the spread crossed (half the modelled spread added) since
they are not auctions. **2 cells**, charged to `after_hours`.

**Results of the later buy-backs, 2026-11-17 23:18 ET.** In REPORT.md. **Both are better than the open in
all three periods**, by the rule set: at 10:00 3.25%, 3.14%, 2.29% (2023 7.32%); at 15:30 4.55%,
3.47%, 2.37% (t 2.10), 2023 8.82%; against 2.98%, 2.82%, 1.60% and 6.66% at the open. The
selling after bad results after hours goes on through the next session. 2 trials;
`after_hours` has 114. The paper ledger records the 15:30 buy-back beside the open.

## Addendum, 2026-11-17 23:20 ET: after the selling, a rebound to buy?

Written before it is measured. The short's events ($300M–$2B, down 15%+ after hours on
results) keep falling through the next session. If the selling is spent by its close, the stock
may come back. **Bought at the close of the session after the report** (D+1), sold at the close
5 or 10 sessions later. Costs: the auction allowance and commission. The bar of the first part
(1% a trade, t of 3, six years of eight on 2010–2017, 150 trades or fewer if the rest is met;
tests at 0.5%, t 2.5, four of five). **2 cells**, charged to `after_hours`.

**Results of the rebound, 2026-11-17 23:21 ET.** **Neither cell meets the bar.** Bought at the close of
the session after the report: −0.50% in 5 sessions (median −0.60%, two years of eight), +0.19%
in 10 (median −1.80%). The fall does not overshoot; it is slow and then it stops. 2 trials;
`after_hours` has 116.

## Addendum, 2026-11-17 23:25 ET: the neighbours of the short, held to 15:30

Written before it is measured. If the short works because bad results are absorbed slowly
through the next session, the cells next to it should show it too when held to 15:30, which
none of them has been. Four cells, each a new rule with the 15:30 buy-back (spread crossed), the
rest as the short: **$50M–$300M down 15%+**; **$2B or more down 15%+**; **$300M–$2B down 10%
to 15%**; **$2B or more down 10% to 15%**. The first part's bar (2010–2017: 1% a trade, t of 3,
six years of eight, 150 trades or fewer if the rest is met), and each cell that meets it goes
once to 2005–2009 and 2018–2022 (0.5%, t of 2.5, four years of five). 2023 is a check for a cell
that passes. **4 cells**, charged to `after_hours`.

**Results of the neighbours, 2026-11-17 23:25 ET.** **None of the 4 cells meets the bar, and all four point
the same way:** 2010–2017, held to 15:30: $50M–$300M down 15%+ +1.51% (68 trades, t 1.08);
$2B+ down 15%+ +1.37% (108, t 1.06); $300M–$2B down 10–15% +0.77% (301, t 0.63); $2B+ down
10–15% +0.97% (205, t 1.84); **each positive in seven years of eight.** The slow absorption of bad
results is broad; it is largest, and only tradable, in the mid-sized companies with a fall of
15% or more. 4 trials; `after_hours` has 120.

## Addendum, 2026-11-18 00:29 ET: who sells after hours (1 trial)

Big prints (strategies/big_prints) found that in small companies the size of the pieces says
who is trading. For the after-hours short: if a stock's after-hours selling comes in large
pieces (funds), the selling may go on at the open; if in small pieces (the public), less so.
**After-hours footprint:** shares per trade over the after-hours minutes up to the reading,
against the geometric mean of the stock's shares per trade over its 60 previous sessions (daily
bars). The short cell ($300M–$2B, down 15%+, sold at the low of the next minute, bought back
at the next open), split at the median footprint of its 2010–2017 events. **1 cell:** the
larger-piece half, judged as a filter on the short: better per trade in all three periods, 2023
as a check; the other half printed beside.

## Addendum, 2026-11-18 00:32 ET: who buys after hours (1 trial)

The same footprint split for the closest long lead: a results release after the close in a
company of $2B or more, up 5% to 15% half an hour later, bought at the high of the next minute
and held 15 sessions. Split at the 2010–2017 median of the after-hours footprint. **1 cell:** the
larger-piece half, judged as a filter: better per trade in all three periods, 2023 as a check.

## Addendum, 2026-11-18 00:37 ET: who buys after hours in small companies (1 trial)

The small-company long ($50M–$300M, up 5% or more after hours on results, bought at the high
of the next minute, held 15 sessions) had the largest averages and the least steadiness. Split
at the 2010–2017 median after-hours footprint. **1 cell:** the larger-piece half, judged as a
filter: better per trade in all three periods, 2023 as a check.

## Addendum, 2026-11-18 00:41 ET: the same signal, bought at the next open (1 trial)

The small-company long with large after-hours pieces leans on thin after-hours fills. The
signal is known before the next open, so it can be bought in the opening auction instead.
Same events and the same median split; **bought at the next open**, sold at the close 15
sessions after it; the auction allowance and commission. **1 cell:** the larger-piece half,
judged as the after-hours version was (better per trade than the whole cell, bought the same
way, in all three periods; 2023 a check), and reported beside the after-hours fill.

## Addendum, 2026-11-18 00:42 ET: overlap with A50 (1 trial)

How many of the small-company long's large-piece signals (bought at the next open) are also
A50 signals (the same company, an A50 signal day one to three sessions after the evening), and
what the rest make on their own, in each period.
