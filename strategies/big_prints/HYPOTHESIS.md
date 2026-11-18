# Big prints: a quiet up day traded in unusually large pieces

Written 2026-11-18 00:01 ET, before anything is measured. An indicator of our own. A fund that is building
a position trades in larger pieces than the crowd, and takes days or weeks to finish. On a
day when a stock's average trade (shares traded ÷ number of trades) is far larger than its
own normal, with more volume than usual, a modest rise and no filing, the likeliest story is
a large buyer at work; if the buying continues, the price should drift up after the day.

## Indicator

For each stock and session D: average trade size = volume ÷ transactions from the daily bars
(`transactions` in the vendor's day bars). **Footprint** = that size ÷ its geometric mean over
the 60 sessions before D.

## Events

Common stock, $300M or more in market value, $1M a day or more, $5 or more, 2005 to 13
October 2023, on a session D with:

- footprint of 2 or more;
- dollar volume of 1.5 times the 20-day average or more;
- close 0% to 4% above the previous close (up, but not a news jump);
- no 8-K by the company whose reaction session (first close after acceptance) is D or D−1;
- a stock-specific day: under 5% of these stocks have a footprint of 2 or more on D (index
  rebalances, where large closing trades hit many stocks at once, drop out).

## Trade

Bought at the open of D+1, held 10 or 20 sessions. Costs: the auction allowance and
commission. Measured against the average common stock of the same size bought at the same
open and held as long.

## Cells

size ($300M–$2B, $2B and over) × hold (10, 20) = **4**, family `big_prints`.

## What counts

Search 2010–2017: 150 trades, 1% a trade over the average, weekly t of 3, six years of eight,
positive after costs. Tests on 2005–2009 and 2018–2022 at 0.5%, t of 2.5, four years of five.
2023 is a check. The holdout stays sealed.

## Follow-up: a stronger footprint, and smaller companies (written 2026-11-18 00:02 ET, after the 4 cells)

The mid-sized cells beat the average in all eight years by about half a point. If the reading
is a large buyer, a larger footprint, and companies where a fund's order is a larger part of
the volume, should show more. **4 cells, held 20 sessions only:** $300M–$2B with a footprint
of 3 or more, and of 4 or more; $50M–$300M ($250,000 a day, $2 or more) with a footprint of 2
or more, and of 3 or more. Every other condition as above (the share of footprint days is
counted within each size). Same bars. These were chosen after seeing the first four cells, so
the search years carry less weight than the tests.

## Checks for the passed cell (written 2026-11-18 00:03 ET, after both tests passed)

1. **2023** (to 13 October): the same cell, read once.
2. **Is it the trade size, or only a quiet up day on heavy volume?** The same events with a
   footprint under 1.2 (an ordinary trade size), $50M–$300M, 20 sessions, in all three periods.
   If these do as well, the indicator adds nothing to the known high-volume premium.
3. **Year by year after costs**, and the share of signals in 2018–2022 whose stock trades
   under $1M a day (the price paid is least certain there).

Each is one trial: 3.

## Check 4: stocks that stop trading inside the hold (written 2026-11-18 00:04 ET)

The tables so far keep only signals whose stock still trades 20 sessions later, which drops
companies taken over or delisted in the hold. The passed cell is read again with the last
close inside the 20 sessions in place of the 20th (as the after_hours study does), in all
three periods and 2023. One trial.

## Check 6: the passed cell's neighbours (written 2026-11-18 00:07 ET)

Whether the cell is a knife-edge: $50M–$300M, read in all three periods with stopped stocks
kept, (a) held 20 sessions with footprint floors of 2.5, 4 and 5, and (b) footprint 3 or more
held 10 and 40 sessions. 5 cells; a neighbourhood that holds up is expected to be positive in
all three periods. 5 trials.

## Follow-up 2: the seller's footprint (written 2026-11-18 00:14 ET)

If large pieces on a quiet up day are a buyer at work, large pieces on a quiet **down** day
should be a seller at work, and the stock should trail afterwards. Same conditions, but the
close **0% to 4% below** the previous close. Read as a short: the short's return over the
average stock of its size, 20 sessions, sold at the next open; after costs and borrow at 10%
a year. **2 cells:** $50M–$300M and $300M–$2B, footprint 3 or more for the small and 2 or
more for the mid-sized (each size's first reading above). Search bar: 1% over the average,
t of 3, six years of eight, positive after costs and borrow; tests at half, t 2.5, four of
five. 2 trials.

## Follow-up 3: the footprint as a filter on the earnings rule (written 2026-11-18 00:15 ET)

Rule A50 (strategies/earnings_drift) buys small companies after a results jump of 15%+ on 5x
volume. If large pieces mark institutional trading, A50 jumps traded in large pieces should
drift more than jumps carried by small (retail) trades. The footprint is read on A50's signal
day, as above (that day's shares per trade against the previous 60 sessions). **1 cell:** A50
with a footprint of 1 or more (the trade at least its normal size), held as A50's plain exit
(next open to the close 15 sessions later, after costs), against all A50 signals. Judged as
A50's exits and filters are: **better only if better per trade in all three periods** (2005–
2009, 2010–2017, 2018–2022), with 2023 as a check; the complement (footprint under 1) is
printed beside it. 1 trial (charged here, not to earnings_drift; it changes nothing in A50).

## Follow-up 4: large pieces on a news day (written 2026-11-18 00:16 ET)

The rule above leaves out any day near an 8-K. If large pieces mark institutions at work, they
may matter most when there is news to act on. Same conditions ($50M–$300M, footprint 3 or
more, 1.5x volume, up 0% to 4%, held 20 sessions), but **with** an 8-K whose reaction session is
D: **2 cells**, (a) a results 8-K (item 2.02) and (b) any other 8-K (no 2.02 from four days
before D to D). Same search bar and tests. 2 trials.

## Follow-up 5: large pieces on a mid-sized company's results jump (written 2026-11-18 00:17 ET)

In companies of $300M to $2B the drift after a results jump is small (busy_day: +0.8% over
20 sessions after a 5% jump, 2010–2017) and faded after 2017 (earnings_drift, family 22). If
large pieces mark institutions that keep buying for weeks, the jumps traded in large pieces
should drift more. Events: busy_day's (results 8-K, $300M–$2B, $1M a day, up 5%+ on the
reaction session D, bought at the next open), whatever the day's crowding, with the footprint
read on D. **2 cells:** footprint 1.5 or more, held 20 and 60 sessions, against the average
stock of that size; the rest (under 1.5) printed beside. Bars: 1% (20) and 2% (60) over the
average, t 3, six of eight, positive after costs; tests at half. 2 trials.

## Follow-up 6: a footprint that repeats (written 2026-11-18 00:18 ET)

A fund building a position over weeks should leave more than one footprint. The passed cell
($50M–$300M, quiet up day, footprint 3+, 20 sessions), split by whether the stock also had a
footprint of 2 or more on at least one of the 10 sessions before D. **1 cell** (repeated), read
in all three periods with stopped stocks kept, against the passed cell: it is worth using only
if it is better per trade in all three periods and still meets the test bars (0.5%, t 2.5,
four of five) in both test periods. The single-footprint rest is printed beside. 1 trial.

## Check 7: the price a buyer gets, and the largest winners (written 2026-11-18 00:20 ET)

(a) The passed cell entered not at the official open but at the volume-weighted price of the
first 30 minutes of D+1 (09:30–10:00, from minute bars), sold as before, in 2010–2017,
2018–2022 and 2023; and the average gap between that price and the official open. (b) The ten
largest winners of the cell in 2005–2023, checked against the price table for data errors.
2 trials.

## Follow-up 7: the crowd's footprint (written 2026-11-18 00:22 ET)

The other end of the indicator: a quiet up day (0% to 4%, 1.5x volume, no 8-K) traded in pieces
**half the normal size or smaller** (footprint 0.5 or less) — many small orders, the mark of
retail attention. Published work finds attention-driven buying is followed by weaker returns.
Read as a short over the average stock of its size, 20 sessions, after costs and borrow at 10%
a year. **2 cells:** $50M–$300M and $300M–$2B. Same search bar and tests. 2 trials.

## Follow-up 8: large pieces beside rule I (written 2026-11-18 00:23 ET)

Rule I (strategies/insider_buying: an insider purchase of $100,000+ in a $50M–$300M company,
bought the next open, held 15 sessions) made 3.2% to 3.9% a trade before 2018 and 1.5% since.
If insiders buying and institutions trading in large pieces are two signs of the same thing,
rule I signals whose signal day is traded in large pieces should do better. **1 cell:** rule I
with a footprint of 1.5 or more on the signal day, against all rule I signals, after costs.
Judged as a filter: better per trade in all three periods (2005–2009, 2010–2017, 2018–2022),
2023 a check; the rest printed beside. 1 trial (charged here; rule I is unchanged).

## Follow-up 9: a quiet fall, by who sold (written 2026-11-18 00:25 ET)

A stock that falls 5% or more on a day with no 8-K (reaction session from four days before to
D) and 1.5x its normal dollar volume: if the selling came in small pieces (footprint under
0.8, the crowd) it may be an overreaction that comes back; in large pieces (2 or more) it may be
a fund that has not finished. Bought at the next open, held 10 sessions, against the average
stock of its size. **4 cells:** size ($50M–$300M, $300M–$2B) × footprint (under 0.8, 2 or
more). Search bar: 150 trades, 1% over the average, t 3, six of eight, positive after costs;
tests at half. 4 trials.

## Check 8: is it buying ahead of results? (written 2026-11-18 00:26 ET)

A diagnostic of the passed cell, not a rule (it uses what happened later): its signals split by
whether a results 8-K reacted inside the 20-session hold. If the gain sits in the signals
followed by results, the large pieces are informed buying ahead of them, and an earnings
calendar would sharpen the rule. 1 trial.

## Follow-up 10: large pieces with a report expected inside the hold (written 2026-11-18 00:26 ET)

Check 8 used what happened later. A rule must use what is known on D: the company's last
results 8-K. Companies report about every 91 days, so if the last results reacted 63 to 91
calendar days before D, the next is expected within the next four weeks, inside the hold.
**1 cell:** the passed cell with that condition, in all three periods and 2023. It is worth
using only if better per trade than the passed cell in all three periods and it meets the test
bars (0.5%, t 2.5, four of five) in both test periods. 1 trial.

## Follow-up 11: a month of large pieces, as a monthly ranking (written 2026-11-18 00:27 ET)

The events above are single days. A fund that works an order for weeks raises a stock's
average trade size for weeks. **Monthly footprint:** the geometric mean of a stock's shares per
trade over its last 20 sessions, against the same over the 60 sessions before those. On the
first session of each month, rank the stocks of each size (common stock, $250,000 a day, $2 or
more; $50M–$300M and $300M–$2B) and buy the top tenth (the ranking
uses the previous close, so the buy is at the first session's open), held 20 sessions, against
the average stock of the size over the same days. **2 cells** (small, mid). Bar: 1% over the
average, t over the months of 3, six of eight years, positive after costs; tests at half, t
2.5, four of five. 2 trials.

## Follow-up 12: the smaller results jumps, traded in large pieces (written 2026-11-18 00:28 ET)

A50 takes only jumps of 15% or more on 5x volume; the smaller jumps (5% to 15%, 3x volume or
more) in the same $50M–$300M companies drift less (the earlier families found them under the
bar). If large pieces mark institutions buying into the news, the smaller jumps traded in large
pieces may drift like A50's. Events from the same tables as A50 (results day, 2-day return 5%
to 15%, 2-day volume 3x or more), footprint read on the signal day. **1 cell:** footprint 1.5 or
more, held as A50's plain exit (next open to the close 15 sessions later), after costs; the rest
printed beside. Search bar: 150 trades, 1% a trade after costs, weekly t 3, six of eight;
tests at 0.5%, t 2.5, four of five. 1 trial.

## Check 9: large pieces in the weeks after results (written 2026-11-18 00:34 ET)

A diagnostic of the passed cell using only what is known on D: its signals split by whether
the company's last results 8-K reacted 5 to 30 calendar days before D (funds buying after the
news, the ground of the earnings drift) or longer ago. 1 trial.

## Follow-up 13: large pieces in sector funds (written 2026-11-18 00:36 ET)

A fund moving money into a sector often does it through a sector or industry index fund, in
blocks. A sector fund traded in large pieces on a quiet day may mark an allocation that goes on
for weeks. **Funds (fixed list):** XLB XLE XLF XLI XLK XLP XLU XLV XLY SMH XBI IBB KRE KBE XRT
XHB ITB IYR VNQ GDX XME OIH XOP IYT ITA KIE XSD IGV. **Event:** footprint 2 or more (shares per
trade against the fund's previous 60 sessions), dollar volume 1.5x its 20-session median, the
fund's return 0% to +2% above SPY's that day, and fewer than a quarter of the listed funds with
a footprint of 2 or more that day (market-wide days out). Bought at the next open, held 20
sessions, against SPY over the same days (open to close); costs 0.02% a side and commission.
**1 cell.** Search bar: 150 trades, 1% over SPY, weekly t 3, six of eight; tests at half, t
2.5, four of five. 1 trial.
