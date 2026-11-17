# Hypothesis: a search for a profitable swing rule (holds of 1 to 3 weeks)

Written 2026-11-16 12:55 ET, before any measurement. The owner's instruction of the same day:
holding for more than a day is allowed, as swing trades of 1 to 3 weeks; a smaller edge than 3%
a trade is acceptable but it must be profitable; do not stop at the first few ideas. The
intraday searches are in `strategies/recent_search` and `strategies/intraday_momentum`.

## Trades

A signal is read at the close of a day. The buy is at the next day's open. The sale is at the
close 5, 10 or 15 sessions after the signal day. Long only. One $2,000 position a trade.

Returns are built from each day's close against the prior close on the same share basis, so
splits are handled; dividends are left out, which understates a long trade slightly. If a
stock stops trading during the hold, the trade ends at its last close; such trades are counted
and the result is shown again with a further 50% loss on each.

## Costs

Per side: commission ($0.0035 a share, $0.35 minimum) plus half the spread by 20-day dollar
volume (under $1M, 1.00%; $1M to $10M, 0.43%; $10M to $100M, 0.18%; over $100M, 0.05%: the
means measured in the quote sample of 2026-11-15). At 2× the spread is doubled.

## Periods (decision 0020)

- **Search:** signals from 2010-01-04 to 2022-11-30. Each year 2018 to 2022 is shown apart,
  and 2010 to 2017 as one block.
- **Check:** signals from 2023-01-03 to 2023-10-13 (so every hold ends before the seal),
  looked at once, for shortlisted rules only.
- **Holdout:** from 2023-11-09, sealed, the owner's one run for this family.

## Idea families (each a grid of conditions; more may be added, dated, before measuring)

1. **Short-term reversal:** a fall over 5 days, by the 60-day trend, by company size.
2. **Earnings drift:** the first session after an earnings 8-K, by that day's return and
   volume, by size.
3. **Breakouts:** a new 250-day high, by volume and by the 20-day run.
4. **Pullbacks in winners:** up strongly over 120 days, down over 5.
5. **Volume shocks:** five times normal dollar volume with no filing, by the day's return.
6. **Near the 250-day low:** by the 20-day fall and the day's close in its range.
7. **Short interest** (2018 on): share of shares short and days to cover, with the 5-day and
   20-day moves.
8. **Fundamentals at earnings:** year-on-year change in quarterly earnings and revenue from
   the filed statements, with the reaction.
9. **Stock-selection cuts** on whatever the first eight turn up: price, size, liquidity,
   volatility, sector, age, market trend.

## Selection, set now

A cell is shortlisted from the search years only if:

1. at least 300 trades in 2018–2022 and 300 in 2010–2017;
2. mean net return at 2× of at least 1.0% a trade (3.0% is the owner's first target; cells at
   or above it are marked);
3. a t-statistic of at least 4 on weekly means of 2018–2022 (holds overlap, so weeks, not
   days, are the unit);
4. positive net at 2× in every year 2018 to 2022, and in 2010–2017.

A shortlisted cell may be refined by further features. The best are then run as a book
($20,000, at most 10 positions of $2,000, no leverage) with the same data, since a mean per
trade says nothing about whether the account could have held the trades. The check on 2023 is
for the book that results. Nothing is called found on the search years alone.

## Risks

Many cells; delisting in losers; signals crowd into bad weeks, when the account cannot take
them all; 2020 flatters anything that buys falls.

## Addendum, 2026-11-16 13:10 ET: wider features, more families, a second test

Written after families 1 to 6 and 8 were measured (2,289 cells, none passing; the large
returns sit in falls during market sell-offs, 2020 and 2022, and are not steady across weeks)
and before anything below is built or measured.

**A wider table.** `research/claude/swing_wide.py` rebuilds the daily table with: distance
from the 20-, 50- and 200-day averages; a 2-day and a 14-day strength index; 2-, 3- and 10-day
returns; the largest and smallest daily return of 20 days; overnight and daytime return summed
over 20 days; 5-day volume against normal; the average daily range; the return of the same 20
sessions a year earlier; sessions since the last earnings release and to the next one as
predicted from a year earlier; the industry; the latest filed fundamentals as of each day
(profit or loss, earnings, free cash flow, book value and net cash against price, revenue
growth, gross profit to assets, debt to assets, share issuance, asset growth, accruals); and
short interest (2018 on).

**More families.**

10. **Market state with the fall:** the market's own 5- and 20-day move and volatility,
    crossed with the stock's fall (buying falls only in a market sell-off).
11. **Technical state:** the averages, strength index, range-scaled falls, overnight against
    daytime return, the largest daily return.
12. **Calendar:** turn of the month, month, December losers into January, weekday, the stock's
    own return in the same season a year earlier, the days before a predicted earnings date.
13. **Fundamental state** with the price signals: profitability, value, net cash, dilution,
    asset growth, accruals.
14. **8-K items other than earnings:** the drift after each item.
15. **Industry:** industry momentum and a stock's move against its industry.
16. **A combined model:** one cross-sectional model of the 10-day return on all the features,
    fitted walk-forward (on the years before Y, applied to year Y, Y = 2014 to 2022), buying
    the top-ranked stocks each day. It is judged only on years it was not fitted on, which is
    its own guard against the number of cells above.

**A second test, reported beside the first.** A long trade carries the market's own noise, so
the weekly t-statistic of a long-only rule is low even when it beats other stocks every week.
Each cell now also shows the t-statistic of its weekly mean return over the all-stock mean of
the same days and hold. A cell with rules 1, 2 and 4 and an excess t of at least 4 (raw t
below 4) is shortlisted as "beats the market" and labelled so; this is a looser rule than the
first and is said wherever it is used. Such a rule still loses money when the market falls
further than its edge, so its book is shown with its losing years.

**Fills.** A buy at the open and a sale at the close can be sent as on-open and on-close
orders, which fill at the auction price without crossing a spread. Selection stays on the
costs above (spread crossed, doubled); the gross column shows what auction fills would leave
before commission. Whether the auction price is the bar's open is to be checked on minute
bars before any claim rests on it.

## Addendum, 2026-11-16 13:21 ET: the combined model (family 16), fixed before it is fitted

Written after families 7 and 10 to 15 were measured on the wide table (about 7,900 further
cells; none passes either test: single conditions beat other stocks by 0.5% to 1% over 15
sessions at most, less than the cost of trading the small stocks where they are found; falls
bought in a market sell-off rebound 10% or more but in a handful of weeks).

- **Stocks:** close of $3 or more and 20-day dollar volume of $5M or more, for fitting.
  Trading is judged on two sets: dollar volume of $10M or more, and of $100M or more.
- **Target:** the 10-session trade return (next open to the close 10 sessions after the
  signal day) less the mean of all stocks for the same days, cut off at ±30%.
- **Features:** every numeric column of the wide table and the market and industry tables
  (about 80), the sector as a category. No feature uses anything after the signal day's close.
- **Model:** gradient-boosted trees (LightGBM, a research-only tool run with
  `uv run --with lightgbm`): 300 trees, learning rate 0.03, 31 leaves, at least 2,000 rows a
  leaf, 70% of features a tree, half the rows a tree, L2 of 10. Fixed; not tuned.
- **Walk-forward:** the model for year Y is fitted on signals from 2010-01-04 to 10 December
  of Y−1 (every third session, since neighbouring days repeat each other), for Y = 2014 to
  2022. Each year's trades come from a model that never saw that year.
- **Rule:** each day the stocks are ranked by the model's score; cells are the top 1, top 3,
  top 10 and top 1% of the day, for holds of 5, 10 and 15 sessions. The same two tests apply,
  with 2014 to 2017 standing for the earlier block.
- **Variants allowed, each counted:** a 5-session and a 15-session target; a model without
  the market columns. No others without a further dated note.

## Addendum, 2026-11-16 13:44 ET: small stocks, auction fills, and a check on the open

Written after the combined model was scored on stocks of $10M a day and more: its top pick
of the day made 1.5% a trade net at 2× in 2018 to 2022 (15 sessions) but nothing in 2014 to
2017 and −3.0% in 2022; top against bottom tenth differ by 0.7%. It passes neither test.
Large, cheap stocks are priced too well for these features.

The effects that are large (falls, earnings reactions, quality) sit in small stocks, where
the declared cost (the quoted spread crossed, doubled: 0.9% to 2% a side) removes them. A
swing trade does not have to cross the spread: it can join the opening and closing auctions.

- **A small-stock model.** The same model and walk-forward, fitted on stocks with dollar
  volume from $250k to $10M a day and a close of $1 or more (every fourth session, for
  memory), without the market columns (in the first model they carried a third of the weight
  through sector-by-period splits, which is fitting to dates). One variant with them.
- **A second cost basis, labelled "auction".** Commission plus an allowance for the order's
  own effect on the auction: 0.25% a side under $1M a day, 0.10% from $1M to $10M, 0.05% from
  $10M to $100M, 0.02% above. These allowances are my assumption, not a measurement.
- **What it may be used for.** A rule that meets the tests only on the auction basis is
  called "auction-dependent" and is not called found. It becomes a candidate only after
  (a) the same trades are re-priced from minute bars, buying at the volume-weighted price of
  09:30 to 10:00 and selling at that of 15:30 to 16:00, which a small patient order can
  approach and which does not depend on a single opening print, and (b) the owner downloads
  a tick sample of opening and closing prints for its trades so the auction price, the first
  quote and the size traded can be compared. The 2023 check waits for (a).

## Addendum, 2026-11-16 13:52 ET: earnings drift in small stocks, refined (family 17)

Written after the small-stock model was scored (its top tenth beats other small stocks by
0.5% over 10 sessions, steadily, excess t 7.7 over all years, but that is 0.4% a trade on the
auction basis and its top picks lost in 2021) and after every family was re-read on the
auction basis: one cell in about 10,000 is auction-dependent (pullbacks in small winners,
2.0% a trade). The largest steady effect is the one family 2 was written for: a small company
that jumps 15% or more on earnings with five times its normal volume keeps rising, 3.2% over
15 sessions on the auction basis, in 2010 to 2017 and in four years of five since.

Family 17 refines that one effect, and splits the periods so the refinement is tested:

- **Chosen on 2010 to 2017 only.** A grid of thresholds, 1,944 cells: the day the signal is
  read (the earnings day itself when the 8-K is dated that day, with that day's return and
  volume; or the session after, with the two-day return and the larger of the two days'
  volume); a jump of at least 5%, 10%, 15% or 25%; volume of any size, at least 2× or at least
  5× normal; a close anywhere, in the top half or in the top fifth of the day's range; company
  size under $300M, $300M to $2B, or both; a price of at least $1, $3 or $5; a hold of 5, 10
  or 15 sessions. `research/claude/swing_earnings.py choose` reads nothing after 2017.
  The cell taken forward is the one with the highest weekly t-statistic on the auction basis
  among cells with 300 or more trades and a mean of 2% or more in 2010 to 2017.
- **Tested on 2018 to 2022,** which the choice above did not use (the base effect was seen
  there, the refinement was not): mean of 1% or more on the auction basis, weekly t of 2.5 or
  more, and at least four years of five positive. One rule, so the bar is that of a single
  test, not of a search.
- **Then** the minute-bar re-pricing, a book, and the 2023 check, as in the note above.

## Addendum, 2026-11-16 13:56 ET: family 17 failed its test; two rules go to 2005–2009

Family 17's chosen cell (session after the release, two-day jump of 15%+, volume 5×+, close
in the top half, under $2B, hold 15; 2.00% a trade and weekly t 4.44 in 2010 to 2017) made
0.76% a trade in 2018 to 2022 with a weekly t of 0.34. It fails. The under-$300M part of it
held up (about 3% in both periods) but saying so after the test is hindsight.

The years 2005 to 2009 are in the research data, have not been read by this search, and
include 2008. Two rules, fixed here, are tested on them once. Signals from 2005-01-03 to
2009-12-08; the same table (`swing_wide.py --early`), costs and trade.

- **Rule A, earnings drift in the smallest stocks** (family 2's cell as written on the first
  day): the session after an earnings 8-K; a two-day return of 15% or more; the larger of the
  two days' volume at least 5× normal; market value under $300M; buy at the next open, sell
  at the close 15 sessions after the signal. Passes if the mean is 1% or more on the auction
  basis, the weekly t is 2.5 or more and at least four of the five years are positive.
- **Rule B, buying a sell-off:** on a day when larger stocks ($2B and more) are down 7% or
  more on average over 5 sessions, buy stocks of $2B and more that are down 20% or more over
  those 5 sessions; sell at the close 15 sessions later. Passes if the mean is 3% or more on
  the auction basis and no year with 50 or more trades loses more than 5% a trade. The weekly
  t is reported, not required: the rule trades in a handful of weeks by design, and the
  question for it is whether 2008 breaks it.

Neither becomes a strategy on this alone; passing sends a rule on to the minute-bar
re-pricing, a book and the 2023 check.

## Addendum, 2026-11-16 14:05 ET: rule A after 2005–2009, and what the 2023 check can say

Rule A passed on 2005 to 2009 (452 trades, 4.04% a trade on the auction basis, weekly t 4.42,
five years of five positive; rule B failed, −0.10% a trade with 2008 at −1.09%). Re-priced
from minute bars rule A is 3.90% (2005 to 2009) and 2.77% (2010 to 2022). As a book of 10
positions of $2,000 over 2005 to 2022 it makes $2,683 a year with the spread crossed and
$4,314 on the auction basis, with a worst drawdown near $11,000 and six losing years of 18.

The 2023 check (signals 2023-01-03 to 2023-10-13) is now read once, for rule A unchanged.
About 70 trades are expected, and one trade swings by about 25%, so the mean will be known
only to about ±3%. Set before reading:

- **Not contradicted:** the mean a trade on the auction basis is above zero.
- **Contradicted:** it is below −3%, which a true edge of about +3% would rarely produce.
- **Says nothing:** between the two.

A book of 20 positions of $1,000 is also shown for 2005 to 2022 (same signals; it takes the
trades the 10-position book skips). No other change to the rule is made before the check.

## Addendum, 2026-11-16 14:11 ET: the 2023 check, and family 18 (jumps on news, under $300M)

**The 2023 check of rule A:** 68 trades, 4.81% a trade on the auction basis (3.74% with the
spread crossed; 4.40% at 30-minute prices). Not contradicted. Results are in REPORT.md.

Rule A uses about a third of a $20,000 account on average. Family 18 looks for a second rule
of the same kind: a small company that jumps on heavy volume when there is news.

- **Grid, 180 cells.** Kind of news: earnings 8-K read the same day (that day's return and
  volume); earnings 8-K read the session after (rule A's reading; two-day return, larger of
  two days' volume); another 8-K, read the session after; another filing but no 8-K; no
  filing at all. Jump of at least 10%, 15% or 25%. Volume at least 2×, 5× or 10× normal.
  Market value under $300M, or $50M to $300M. Hold 10 or 15 sessions.
  The $50M floor is in the grid because rule A lost on companies under $50M in every period,
  which I know from periods that are test periods here; the floor is therefore hindsight and
  any cell that needs it is marked so.
- **Chosen on 2010 to 2017 only:** every cell with 300 or more trades, a mean of 2% or more on
  the auction basis and a weekly t of 3 or more, up to the five highest t.
- **Tested on 2005 to 2009 and 2018 to 2022 together,** which the choice does not read (for
  cells that are rule A or contain it these years are already known, and that is said): a
  mean of 1% or more on the auction basis in each period, and a weekly t of 3 or more over
  the two together (3, not 2.5, because up to five cells are tested).
- A cell that passes is a second candidate under the same conditions as rule A: fills
  unmeasured, holdout sealed. The 2023 check has been read for rule A; for a new cell it is
  a second look at those months and is reported as such.

## Addendum, 2026-11-16 14:29 ET: family 18's result, and rule C to 2005–2009

**Family 18:** the five cells chosen on 2010 to 2017 are all the earnings rule with the $50M
floor; each passed on 2005 to 2009 and 2018 to 2022 (pooled weekly t 3.5 to 4.2, every test
year positive). No other kind of news qualified. The rule taken forward is A50 (15%, 5×,
$50M to $300M, 15 sessions), now also `strategies/earnings_drift` for `kinn swing`.

**Rule C,** to use the money rule A50 leaves idle: the one other cell that qualified on the
auction basis in the search years (family 4). A company of $300M to $2B that is up 50% to
100% over 120 sessions and down 5% to 10% over the last 5; buy at the next open, sell at the
close 15 sessions after the signal. It is tested once on 2005 to 2009, which have not been
read for it, with rule A's test: a mean of 1% or more on the auction basis, a weekly t of 2.5
or more, and four years of five positive. In the search years it made 0.9% (2010–2017) and
2.0% (2018–2022), so the prior is weak; this test decides whether it is worth more work.

**Rule C, result (same day):** 11,103 trades in 2005 to 2009, 1.78% a trade on the auction
basis, weekly t 3.22, four years of five positive (2008: −3.94%). It passes the test as
written. It is not taken forward: 0.80% of the 1.78% is over the market, and filling the
earnings book's idle slots with it lowers the book's Sharpe ratio and raises its drawdown.

## Addendum, 2026-11-16 16:25 ET: sliding windows and market cycles (owner's question)

Asked after the holdout run; a description of the rule on years already read (2005 to
October 2023), not a new search and not a change to the frozen rule.

1. **Sliding-window choice of the thresholds.** For each year Y from 2010 to 2023, the cell of
   family 18's grid (180 cells) with the highest weekly t-statistic on the five years before Y
   (signals to 8 December of Y−1; at least 150 trades and a mean of 2% on the auction basis)
   is traded in year Y. The same with all years before Y instead of five. Both are set beside
   the fixed rule A50 on the same years. The question: does re-fitting to recent years beat a
   rule that never changes?
2. **Market cycles.** A50's trades grouped by named stretches of the market (the 2005–2007
   rise, the 2007–2009 fall, the 2009–2010 recovery, and so on to 2023), with the mean, the
   share of winners and the number of trades in each.

## Addendum, 2026-11-16 16:32 ET: entries and exits (owner's question), before any is measured

The rule's signal is specific; its entry (the next open) and its exit (the close 15 sessions
later) are the simplest possible and were never compared with alternatives beyond holds of 5,
10 and 15 sessions. This study compares them, on A50's signals of 2005 to October 2023.

**Exits** (entry at the next open): holds of 5, 10, 15, 20 and 30 sessions; a stop 8%, 12% or
20% under the entry price, and one at the signal day's low; a target 15%, 25% or 40% above; a
stop with a target (12% and 25%); a trailing stop 15%, 20% or 25% under the highest close
since entry, to 30 sessions; an exit when the close falls under its 9- or 20-day exponential
average, to 30 sessions. A stop or target is checked against each day's range (the stop first
if both are inside it); a gap through the level fills at the open. Rules read at a close exit
at the next open.

**Entries** (exit at the close 15 sessions after the signal): the next open; only if that
open gaps no more than 5% up; only if it does not gap down; a limit 3% or 5% under the signal
close, good for three sessions; the next close.

**Costs:** the auction allowance for fills at an open or close; the modelled half-spread
instead for a stop filled inside the day; the allowance for a limit fill.

**How it is read:** each variant on 2010 to 2017, then on 2005 to 2009 and on 2018 to October
2023 apart. A variant is better only if it beats the plain rule in all three, in the mean a
trade and in a 10-position book's Sharpe ratio and drawdown. About 30 variants, so one that
wins in one period only is noise. The holdout is spent: nothing here can be confirmed on it,
and the frozen rule stays the reference. A variant that wins everywhere would go to the paper
ledger beside it.

## Addendum, 2026-11-16 22:53 ET: the overnight programme (owner's instruction)

The owner: keep researching swing rules overnight; aim at 3% a trade or close to it; solve
the flat years; treat 2020 as an outlier year. Still long only. Everything below is on years
already read (2005 to October 2023); the holdout is spent for this family and untouched for
insider buying, so whatever survives goes to the paper ledger, not to a claim of proof.
**2020 is shown apart, and nothing is chosen because of it:** every comparison is also made
with 2020 left out.

Written before any of it is measured.

1. **Which earnings jumps fail (a quality filter).** A50's signals split by facts known at the
   signal: shares issued over the past year (more than 10% or not), profitable last quarter
   or not, free cash flow positive or not, net cash or net debt, price ($3, $5), already at a
   250-day high or not, up or down over the past year, and short interest (2018 on). A filter
   counts only if the kept trades beat all trades in each of 2010–2017, 2005–2009 and
   2018–2023, with and without 2020.
2. **A hedge that is a purchase.** An inverse small-stock fund (RWM) is bought beside each
   position, so no short sale and no margin: half or all of the position's dollars, always or
   only when the small-stock index is under its 200-day average. The fund is modelled as the
   opposite of the index's daily return less 2% a year, checked against the fund's own prices.
   The account's $20,000 pays for both legs.
3. **Standing aside.** No hedge; new signals are skipped when the index is under its 200-day
   average, or has fallen 5% in five sessions.
4. **Exits with the above:** the 20-day-average exit and a 40% target, from the exit study.
5. **Stronger insider signals.** Cells of the insider grid that were eligible on 2010–2017 but
   not among the five tested: $500,000 or more bought, and two or three insiders, in
   companies of $50M to $300M, hold 15. Tested like the others on 2006–2009 and 2018–2022.
6. **The book that results,** year by year, with the measures used so far (a year, Sharpe
   ratio, worst drawdown, worst year, losing years), on the auction basis and with the spread
   crossed, with and without 2020.

A book "solves the flat years" here if its worst year of 2006 to 2023 is a gain of at least
5% of the account on the auction basis and no year loses with the spread crossed.

## Addendum, 2026-11-16 23:08 ET: checks on the quality filter, before anything is built on it

Steps 1 to 4 above are measured (results in REPORT.md). One filter stood out: A50 signals in
companies that hold **net cash and whose stock is down over the past year** make nothing;
skipping them ("up or net debt") leaves 4% to 5.6% a trade in every span and a book with no
losing year. It was found by looking at eight splits of years already read, so it is a
finding to distrust until it survives the checks below. None of them chooses anything new.
Written before any of them is run.

1. **Chance.** 5,000 random filters that drop the same number of trades: how often does
   chance give a mean without 2020, and a count of winning years, as good as the filter's?
2. **Would the first span alone have found it?** All pairs of the eight facts (28 pairs, four
   groups each, 112 groups) ranked on 2010–2017 only, groups of 60 trades or more. Where does
   "down and net cash" rank, and how do the five worst groups of 2010–2017 do in 2005–2009
   and 2018–2023? If the filter is real, the worst groups of one span stay bad in the others.
3. **Cut-offs.** The year's return at −30%, −20%, −10%, 0, +10%, +20% and net cash at −10%,
   0, +10%, +25% of market value. A real effect changes smoothly; a knife edge is a fit.
4. **What the failing group is:** sector, share with a loss, price, size, and how the stock
   did over the following year (description only, no rule).
5. **The same filter on insider buying** (rule I, and the cell of $100,000 or more by two or
   more insiders): 2 trials. Insider buying in a fallen stock is the classic case, so the
   filter may well not carry over; if it does not, that is recorded and the insider sleeve
   stays unfiltered.
6. **Jumps of 10% to 15%** with the filter (seen once already for 2018–2023 in the
   cross-check: 2.85%): all three spans. Kept as extra signals only if the trade clears 3%
   in each span, with and without 2020.
7. **The book** (step 6 of the previous addendum): the filtered rule alone and with the
   insider sleeve in the idle slots, year by year, both cost bases, with and without 2020.

Trials added: 16 (splits) + 13 (book configurations) + 9 (2×2 and unions) + 24 (filtered
books) + 4 (insider cells) + 112 (pairs) + 24 (cut-offs) + 2 + 1 + about 6 (books) = about 211.

**Results, 2026-11-16 23:25 ET.** In REPORT.md, "The flat years". The filter survived all
seven checks' terms: chance (0 of 5,000 random filters as good; 1 of 5,000 when dropping the
same number in each year), the first span (sixth worst of 75 groups in 2010–2017 and the only
one of the eight worst that stayed bad), the cut-offs (all 24 leave every year positive), and
a second universe (the same group loses among 10% to 15% jumps). It does not carry over to
insider buying. The 10% to 15% jumps stay under 3% and are not added. The filtered book has
no losing year on either cost basis; adding the insider rule brings losing years back. The
note in check 2 said eight facts: short interest exists only from 2018 and the two price
splits are one fact, so seven facts and 75 groups of 60 trades or more were ranked. Trials
added by the two addenda: about 210, all in family `swing_search`.

## Addendum, 2026-11-16 23:40 ET: does the quality test rescue other jumps? (families 19 and 20)

Written before anything is measured. The quality test (up over the year, or net debt) was
found on earnings jumps. If the reason is general (a jump in a fallen, cash-rich company is
a bounce that holders sell into), it should also lift jumps on other news, which family 18
found too weak to trade (no cell at 2%). If it does, they are extra signals for the idle
slots; if it does not, the test is specific to earnings and that is worth knowing too.

Companies of $50M to $300M, hold 15, the auction basis, the test exactly as fixed (no new
cut-offs), spans 2010–2017, 2005–2009 and 2018 to October 2023 with and without 2020.

**Family 19, other news** (a jump of 15% or more on 5 times normal volume): four kinds of
day, each with the test applied: an earnings 8-K filed the same day, another 8-K item since
the previous session, another filing, and no filing at all. 4 cells.

**Family 20, weaker earnings jumps:** a jump of 15% or more on 2 to 5 times volume, with the
test, and with the stricter "up over the year and net debt"; and a jump of 10% to 15% on 5
times volume with the stricter test (with the plain test it was 2.0% to 2.9%, already
seen). 3 cells.

**What counts.** A cell is added to the rule only if it makes 3% or more a trade in each of
the three spans, without 2020 as well, on 100 trades or more in each, and the book with it
added has no losing year on either cost basis. Otherwise it is recorded as failed. 7 trials.

**Results, 2026-11-16 23:43 ET.** In REPORT.md. Family 19: jumps on other 8-K items, other
filings and no filing lose with or without the test (failed). The earnings 8-K dated the day
of the jump clears the trade bar with the test (5.19%, 8.20%, 4.01%; 3.81% without 2020; 211,
168 and 195 trades) and fails the book term: added to A50Q with one position a company it
raises the book to $6,044 a year with no losing year on the auction basis, and two small
losing years with the spread crossed. Not added. Family 20: failed (no cell with 100 trades a
span clears 3%). 7 trials.

## Addendum, 2026-11-16 23:50 ET: the drawdown of A50Q (family 21), written before any of it is measured

"No losing calendar year" is not the same as never being under water. Described first, no
trial: A50Q's book has two drawdowns of about $10,000 on a $20,000 account (June to November
2007, not recovered until August 2009; December 2019 to April 2020, recovered by August
2020). That is over the half of the account decision 0017 allows. The 20-day-average exit,
already a candidate, cuts the worst to $7,601.

Three plain risk controls on A50Q's book (10 positions, the plain 15-session exit), each a
single setting fixed here without looking:

1. **Smaller positions in wilder stocks.** A position is $2,000 times the lesser of 1 and
   4% divided by the stock's daily volatility over the 60 sessions before the signal.
2. **A pause after a loss.** When the book's marked profit is $3,000 (15% of the account) or
   more under its high, no new position is opened for 20 sessions.
3. **At most two new positions a day** (the most volume against normal first), since the
   signals come in clusters in earnings weeks.

**What counts.** Against A50Q on the auction basis ($5,097 a year, drawdown $10,366): a
control is kept as a candidate only if the worst drawdown falls to $7,800 or less, dollars a
year stay at $3,800 or more, no year loses on either cost basis, and the Sharpe ratio is not
lower in either half (2006–2014, 2015–2023). Each is also shown with the 20-day exit, as
description. Standing aside by the market's trend already failed, and the pause may fail for
the same reason (the rule's best trades follow sell-offs); it is tested because it is the
control most people would reach for. 3 trials.
