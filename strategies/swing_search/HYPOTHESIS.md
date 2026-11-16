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
