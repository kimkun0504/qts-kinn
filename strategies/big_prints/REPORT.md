# Big prints: report

**Verdict: the best long lead of 17–18 November; passed both test periods, not a clean pass;
follow it on paper.** A company of $50M to $300M that, on a quiet day with no 8-K, closes 0% to
4% up on 1.5x its normal dollar volume while trading in pieces three times its own normal size,
bought at the next open and held 20 sessions: +1.85% (2005–2009, t 4.21) and +1.77% (2018–2022,
t 3.09) over the average small stock, +2.08% in 2023; the same days with an ordinary trade size
make nothing. Against it: chosen as a follow-up; 0.94% in 2010–2017 with delisted stocks kept;
tail-heavy. The paper ledger is `tools/owner/paper_big_prints.py`. 48 trials.

Code: `research/claude/big_prints.py`.

## The 4 cells, 2010–2017 (read 18 November 2026, 00:01 ET)

| Size | Hold | Trades | Over the average stock | Weekly t | Years positive | After costs |
|---|---|---|---|---|---|---|
| $300M–$2B | 10 sessions | 8,179 | +0.35% | 3.79 | 8 of 8 | +0.49% |
| $300M–$2B | 20 sessions | 8,179 | +0.54% | 3.78 | 8 of 8 | +1.12% |
| $2B and over | 10 sessions | 6,272 | +0.07% | 0.95 | 5 of 8 | +0.26% |
| $2B and over | 20 sessions | 6,272 | −0.09% | −0.62 | 3 of 8 | +0.60% |

No cell meets the bar (1% over the average). The indicator does sort mid-sized stocks: after a
quiet up day traded in large pieces they beat the average in every one of the eight years,
by about half a point in four weeks, with a t near 4, on 1,000 signals a year. In the largest
companies there is nothing, as expected where a large buyer is a small part of the volume.
A stronger reading of the same indicator, and smaller companies, are planned below before
they are measured.

Trials: 4.

## Follow-up, 2010–2017 (read 18 November 2026, 00:03 ET)

| Cell (20 sessions) | Trades | Over the average stock | Weekly t | Years positive | After costs |
|---|---|---|---|---|---|
| $300M–$2B, footprint 3+ | 2,461 | +0.30% | 0.67 | 6 of 8 | +0.85% |
| $300M–$2B, footprint 4+ | 1,067 | +0.43% | 0.85 | 6 of 8 | +0.98% |
| **$50M–$300M, footprint 2+** | **5,505** | **+1.03%** | **5.40** | **8 of 8** | **+1.11%** |
| **$50M–$300M, footprint 3+** | **2,070** | **+1.00%** | **3.24** | **7 of 8** | **+1.21%** |

A larger footprint does not help in mid-sized companies. In small companies both cells meet
the search bar, and go to their tests.

## Tests of the two small-company cells (read 18 November 2026, 00:03 ET)

| $50M–$300M, 20 sessions | 2005–2009 | 2018–2022 |
|---|---|---|
| Footprint 2+ | +1.89% (6,489; t 7.41; 5 of 5; after costs +1.62%) **passed** | +0.90% (4,288; t 1.78; 4 of 5; after costs +0.01%) failed |
| **Footprint 3+** | **+1.85% (2,554; t 4.21; 5 of 5; after costs +1.46%) passed** | **+1.77% (1,858; t 3.09; 4 of 5; after costs +0.83%) passed** |

Over the average small stock, by year:

- Footprint 3+: 2005 +1.9%, 2006 +1.8%, 2007 +1.7%, 2008 +2.3%, 2009 +1.4%; 2018 +2.2%,
  2019 +2.2%, 2020 −1.4%, 2021 +1.7%, 2022 +3.7%.
- Footprint 2+: 2018 +1.0%, 2019 +1.0%, 2020 −1.6%, 2021 +1.3%, 2022 +2.3%.

**Small companies with a footprint of 3 or more pass both tests**, the first cell to do so
tonight. It was chosen after the first four cells were read, so its search figures count for
less; the two test periods were unread when it was chosen.

## Checks on the passed cell (read 18 November 2026, 00:04 to 00:06 ET)

**1. 2023 (to 13 October):** +2.08% over the average small stock (384 trades, t 2.38); after
costs −0.56%, as small stocks fell that year.

**2. The trade size is what matters.** The same events with an ordinary trade size (footprint
under 1.2), $50M–$300M, 20 sessions: +0.15% over the average (45,531; t 0.68) in 2010–2017,
+0.10% in 2005–2009, −0.14% in 2018–2022. A quiet up day on heavy volume is worth nothing
here; the large pieces are the signal.

**3. Year by year, liquidity, and a book.** Over the average small stock the cell was positive
in 17 of 19 years (2016 −0.4%, 2020 −1.4%). 87% of signals are in stocks trading under $1M a
day (median about $400,000, price about $9, market value about $200M); those over $1M a day do
as well (+1.21% in 2010–2017, +2.15% in 2005–2009, +1.98% in 2018–2022). At $2,000 a trade,
about 300 signals a year leave 28 positions open on an average day (95th percentile 57, most
81); unhedged the book made money in 12 of 18 years, and against the small-stock average in
15 of 18. Single trades lost up to 40% to 96%; the worst 1% lost 19% to 53%.

**4. Stocks that stop trading inside the hold** (3.7% of signals; on average +0.3%, mostly
completed takeovers), kept at their last close:

| Period | Trades | Over the average | Weekly t | Years positive | After costs |
|---|---|---|---|---|---|
| 2010–2017 | 2,155 | +0.94% | 3.24 | 7 of 8 | +1.15% |
| 2005–2009 | 2,633 | +1.78% | 4.12 | 5 of 5 | +1.39% |
| 2018–2022 | 1,906 | +1.83% | 3.10 | 4 of 5 | +0.80% |
| 2023 | 405 | +2.10% | 2.43 | | −0.65% |

**5. How much rests on a few trades** (a diagnostic, after the above). The median trade beats
the average by +0.02% (2010–2017), +0.47%, +1.28% and +1.88% (2023), and the best 1% of trades
make 27% to 69% of the excess. With each trade's excess capped at ±30%: +0.64% (t 2.65),
+1.37% (t 3.79), +0.97% (t 2.05), +1.92% (t 2.66).

## Verdict: the best long lead of the night, not a clean pass

- **For it:** chosen before either test period was read, it passed both (+1.8% a trade over
  the average small stock, t 3 to 4); 2023 was +2.1%; 17 of 19 years positive; the control
  shows the effect is the trade size and not volume or the up day; it needs no borrow; it is
  an indicator of our own, from data the vendor sends every evening.
- **Against it:** it was a follow-up chosen after the first four cells; kept with the stocks
  that stopped trading, its search figure is 0.94%, just under the 1% bar; much of the mean
  comes from a few large winners, and capped at ±30% its 2018–2022 t is 2.05; it trades small,
  thin stocks with fat losing tails, and needs $50,000 or more at $2,000 a position.
- **Next:** follow it on paper from tonight's data, and decide on size only after a few
  months of signals. It was not run on the holdout.

Trials: 4 cells + 4 follow-up cells + 4 test runs + 5 checks = **17** (family `big_prints`).

## Check 6: neighbours (read 18 November 2026, 00:09 ET)

$50M–$300M, over the average small stock, stopped stocks kept:

| Cell | 2010–2017 | 2005–2009 | 2018–2022 |
|---|---|---|---|
| Footprint 2.5+, 20 sessions | +0.99% (3,307; t 4.68; 8 of 8) | +1.75% (t 4.82) | +1.69% (t 3.33) |
| Footprint 4+, 20 sessions | +1.65% (1,112; t 4.36) | +1.24% (t 2.03) | +1.38% (t 2.58) |
| Footprint 5+, 20 sessions | +2.04% (687; t 3.35) | +0.89% (t 0.50) | +2.14% (t 3.50) |
| Footprint 3+, 10 sessions | +0.53% (2,155; t 1.91) | +1.33% (t 4.65) | +0.99% (t 2.84) |
| Footprint 3+, 40 sessions | +2.13% (t 2.41) | +1.92% (t 3.45) | +2.44% (t 2.06) |

All fifteen readings are positive, from +0.5% to +2.4%; the cell is not a knife-edge. The gain
keeps building past 20 sessions (about +2% by 40). Trials: 5 (family total 22).

## Following it on paper (built 18 November 2026)

The ledger is ready; it sends no order and needs no borrow:

```
export SEC_USER_AGENT="Your Name your@email"
uv run python tools/owner/paper_big_prints.py --since 2026-10-20   # first run: four weeks back
uv run python tools/owner/paper_big_prints.py                      # then each evening after 16:30
```

Each evening it fetches the vendor's grouped daily bars (unadjusted, with the trade counts),
keeps them in `paper/big_prints/bars/` so later evenings fetch one day, reads every stock's
footprint, and for the stocks that pass looks up the type and market value (Massive) and
the 8-Ks (SEC). Signals are bought at the next open and sold at the close 20 sessions after
the signal, from the stock's adjusted bars, with IWM over the same days beside each; a second
column holds the same trade sold after 40 sessions (better per trade in every period of the
neighbours check, with twice the money tied up). The page
is `paper/big_prints/report.md`. Code: `src/kinn/big_prints_paper.py`,
`tools/owner/paper_big_prints.py`, tests in `tests/test_big_prints_paper.py` (the footprint
and normal volume equal the research's window functions; the tool is run end to end on
made-up answers).

**On real data:** run on 25 random sessions of 2022 with the processed daily bars, the
panel's market value and the research's 8-K filter in place of the vendor's and the SEC's
answers (`research/claude/big_prints_paper_check.py`), the ledger's code found 43 of the
research's 46 signals; the 3 it missed are stocks whose ticker changed within their 60
sessions (the research follows the company, the ledger the ticker). It found 4 more on 21
December 2022, a day the research skipped as an index day (the share of large-trade stocks
is counted over a slightly different pool; see the module's note).

**What to watch:** about 25 signals a month at the research's rate, so a month of paper gives
a first count and two or three months a first reading of the average. The research figure
to compare is +1.8% a trade over small stocks; the median trade is near zero, so a few
months can easily look flat.

## Follow-up 2: the seller's footprint (read 18 November 2026, 00:15 ET)

Quiet **down** days (0% to −4%) in large pieces, read as a short over the average, 2010–2017:

| Cell | Shorts | Short over the average | t | Years positive | After costs and borrow |
|---|---|---|---|---|---|
| $50M–$300M, footprint 3+ | 1,691 | −0.79% | −2.12 | 1 of 8 | −3.05% |
| $300M–$2B, footprint 2+ | 6,571 | −0.14% | −0.92 | 2 of 8 | −2.22% |

**The short fails, and the stocks did better than average after a down day in large pieces
too** (small companies +0.8% over 20 sessions, seven years of eight). So the large pieces do not
mark only a buyer: in small companies they mark institutional trading of either kind, after
which the stock does better than the average, and best when the day closed up. That weakens
the "a fund is still buying" story and leaves "large traders are involved" (a seller's block
in a thin stock is absorbed, then the price recovers). The long cell's numbers are unchanged
(the up-day signals are the same in both tables). Not followed further; 2 trials (family 24).

## Follow-up 3: the footprint as a filter on A50 (read 18 November 2026, 00:17 ET)

A50 signals, plain exit (next open to the close 15 sessions later), after costs:

| Period | All A50 | Footprint 1+ | Footprint under 1 |
|---|---|---|---|
| 2010–2017 | +3.26% (603; t 3.96) | +3.38% (500) | +2.67% (103) |
| 2005–2009 | +4.53% (434) | +4.66% (345) | +4.05% (89) |
| 2018–2022 | +4.13% (460) | +4.17% (390) | +3.89% (70) |
| 2023 | +5.95% (63) | +5.95% (56) | +5.89% (7) |

Better per trade in all three periods, as the rule for A50's filters asks, but by only 0.04 to
0.13 points, and the trades it removes still make 2.7% to 4.1% each: as a filter it would cut
A50's total profit. **Not recommended**; A50 is unchanged. Most A50 jumps are already traded
in larger pieces than normal (median footprint 1.2 to 1.4). 1 trial (family 25).

## Follow-up 4: large pieces on a news day (read 18 November 2026, 00:19 ET)

$50M–$300M, footprint 3+, up 0% to 4%, with an 8-K reacting that day, 2010–2017: a results 8-K
−0.26% over the average (36 trades), any other 8-K +0.44% (91). Too few and nothing there: on
news days the trades are many and small, so the footprint rarely reaches 3. The quiet-day rule
stands as it is. 2 trials (family 27).

## Follow-up 5: large pieces on a mid-sized results jump (read 18 November 2026, 00:18 ET)

$300M–$2B, up 5%+ on results, 2010–2017, over the average stock of that size:

| Footprint on the reaction day | 20 sessions | 60 sessions |
|---|---|---|
| 1.5 or more | +1.03% (326; t 0.78; 6 of 8) | +2.29% (307; t 0.21; 6 of 8) |
| Under 1.5 | +0.66% (7,481; t 1.44; 8 of 8) | +1.07% (7,463; t 1.01; 8 of 8) |

Larger means with large pieces, but on 40 trades a year, spread over quiet weeks, with a weekly
t under 1: nothing to test. 2 trials (family 29).

## Follow-up 6: a footprint that repeats (read 18 November 2026, 00:19 ET)

The passed cell split by an earlier footprint (2+) in the 10 sessions before, over the average:

| Period | Passed cell | Repeated | Single |
|---|---|---|---|
| 2010–2017 | +0.94% (2,155; t 3.24) | +0.98% (1,069; t 2.85) | +0.90% (1,086; t 2.06) |
| 2005–2009 | +1.78% (2,633; t 4.12) | +1.99% (1,623; t 2.69) | +1.45% (1,010; t 3.64) |
| 2018–2022 | +1.83% (1,906; t 3.10) | +1.58% (1,349; t 1.56) | +2.44% (557; t 3.26) |
| 2023 | +2.10% (405) | +2.62% (345) | −0.91% (60) |

Not better in 2018–2022, and its t there is 1.56: a repeated footprint is not a better rule.
The passed cell stays as it is. 1 trial (family 30).

## As a book (a description, not a test)

$2,000 a position, at most N open; each session the day's signals are taken largest footprint
first while there is room; held 20 sessions; after costs, unhedged. Code:
`research/claude/big_prints_book.py`.

| Cap (money tied up) | Trades 2005–Oct 2023 | Dollars in all | A year | Years positive |
|---|---|---|---|---|
| 10 ($20,000) | 2,241 | $56,997 | about $3,000 | 15 of 19 |
| 20 ($40,000) | 4,175 | $85,986 | about $4,500 | 14 of 19 |
| 30 ($60,000) | 5,481 | $112,236 | about $5,900 | 13 of 19 |
| none | 7,099 | $148,303 | about $7,800 | 12 of 19 |

With ten positions: 2005 +$5,455, 2006 +$8,111, 2007 +$863, 2008 −$2,708, 2009 +$11,530,
2010 +$7,897, 2011 +$1,602, 2012 +$905, 2013 +$9,832, 2014 +$2,884, 2015 +$166, 2016 +$2,899,
2017 +$1,421, 2018 −$1,789, 2019 +$4,977, 2020 +$2,899, 2021 +$2,566, 2022 −$721, 2023 −$1,793.
The losing years are years small stocks fell (2008, 2018, 2022, 2023); against the small-stock
average 14 of 19 years are positive at every cap. About 15% a year on the money tied up with
ten positions, before any hedge: smaller than A50, and it does not need the same events.

## Check 7: the price a buyer gets, and the largest winners (read 18 November 2026, 00:22 ET)

**Bought at the first 30 minutes' volume-weighted price** of D+1 instead of the official open
(`research/claude/big_prints_fill.py`), over the average small stock:

| Period | Signals priced | From the open | From the 30-minute VWAP | Median VWAP against the open |
|---|---|---|---|---|
| 2010–2017 | 2,075 | +0.93% | +0.88% (t 2.92) | 0.00% |
| 2018–2022 | 1,532 | +1.96% | +1.85% (t 3.06) | 0.00% |
| 2023 | 268 | +2.08% | +1.87% (t 1.56) | 0.00% |

A buyer spread over the first half hour does about as well as the auction: the edge is not in
the opening print.

**The ten largest winners** (+131% to +406% in 20 sessions) are, with one exception, real: a
2022 small-stock squeeze (IMTE), drug-trial and approval news (FULC, FPRX, MIRM, SRNE, VRUS,
BCAB), a SPAC that squeezed after its merger vote (TVAC), EMES. The exception is SUPR in April
2008, where the price table jumps from $4.58 to $14.90 across a month with no rows (an
unrecorded share change or a reused identifier): a data error. Signals whose hold spans a gap
of more than seven days in the price table are 124 of 7,099; without them the cell reads
+0.95% (t 3.28), +1.78% (t 4.10), +1.87% (t 3.10) and +2.02% in 2023 — unchanged.

2 trials (family 32).

## Follow-up 7: the crowd's footprint (read 18 November 2026, 00:23 ET)

Quiet up days in pieces half the normal size or smaller, read as a short, 2010–2017: small
companies +0.05% over the average for the short (192; t −0.41), mid-sized +1.67% (76; t 0.52).
Rare and nothing there. 2 trials (family 34).

## Follow-up 8: large pieces beside rule I (read 18 November 2026, 00:25 ET)

Rule I signals, held 15 sessions, after costs:

| Period | Rule I | Footprint 1.5+ | Under 1.5 |
|---|---|---|---|
| 2005–2009 | +3.86% (1,862) | +3.50% (246) | +3.92% |
| 2010–2017 | +3.18% (2,909) | +3.22% (287) | +3.18% |
| 2018–2022 | +1.54% (2,086) | +1.43% (310) | +1.55% |
| 2023 | +1.73% (275) | +5.07% (51) | +0.96% |

No better: insider purchases and large pieces do not add up. Rule I is unchanged. 1 trial
(family 35).

## Beside the earnings rule (a description)

A50's signals at $2,000 a trade (plain 15-session exit) and big prints with ten positions, by
year, after costs: the two move together more than A50 and the after-hours short do
(correlation of yearly dollars 0.51; both are small-company longs). Together every year from
2005 to 2023 is positive; the weakest are 2008 (+$514: A50 +$3,222, big prints −$2,708) and
2011 (+$931: A50 −$671, big prints +$1,602). Big prints adds most in 2010, 2013 and 2019 and
costs in 2018, 2022 and 2023.

## Follow-up 9: a quiet fall, by who sold (read 18 November 2026, 00:27 ET)

Down 5% or more with no 8-K, bought at the next open, 10 sessions, over the average, 2010–2017:

| Size | Small pieces (under 0.8) | Large pieces (2+) |
|---|---|---|
| $50M–$300M | −0.79% (950; t −1.15; 1 of 8) | +0.99% (511; t 0.68; 6 of 8) |
| $300M–$2B | +0.49% (357; t 0.44) | −0.24% (255) |

No cell meets the bar. In small companies the pattern of the night repeats faintly: after a fall
in small pieces the stock keeps trailing; after a fall in large pieces it does better than the
average. Too noisy to trade. 4 trials (family 39).

## Check 8: is it buying ahead of results? (read 18 November 2026, 00:28 ET)

The passed cell split by whether a results 8-K reacted inside the 20-session hold (known only
afterwards), over the average small stock:

| Period | Results inside the hold | No results |
|---|---|---|
| 2010–2017 | +1.60% (597; t 2.15) | +0.68% (1,558; t 1.13) |
| 2005–2009 | +1.76% (697) | +1.79% (1,936; t 3.85) |
| 2018–2022 | +4.50% (337; t 2.74) | +1.26% (1,569; t 1.70) |
| 2023 | +4.82% (45) | +1.76% (360) |

In three of the four periods the signals followed by results did two to four times better: part
of the large-piece buying is informed buying ahead of results. Those without results are still
positive. A calendar of coming report dates (the Benzinga question still open) would let the
rule favour signals with a report due inside the hold; that is a new rule and would need its
own test. 1 trial (family 40).

## Follow-up 10: a report expected inside the hold (read 18 November 2026, 00:28 ET)

The passed cell kept only when the last results 8-K reacted 63 to 91 days before the signal (the
next report due within about four weeks), over the average small stock:

| Period | Passed cell | Report due | Not due |
|---|---|---|---|
| 2010–2017 | +0.94% (2,155) | +1.60% (500; t 2.06; 8 of 8) | +0.74% |
| 2005–2009 | +1.78% (2,633) | +1.05% (545; t 0.82) | +1.98% |
| 2018–2022 | +1.83% (1,906) | +2.70% (248; t 1.68; 5 of 5) | +1.70% |
| 2023 | +2.10% (405) | +1.46% (32) | +2.15% |

Worse in 2005–2009 and 2023, and its t is under 2.5 in both tests: guessing the report date
from the last one does not make a better rule. The passed cell stands. 1 trial (family 41).

## Follow-up 11: a month of large pieces, ranked monthly (read 18 November 2026, 00:27 ET)

The top tenth by the last 20 sessions' trade size against the 60 before, bought on the first
session of each month, 20 sessions, 2010–2017: small companies −0.08% over the average (5,351;
t −0.20), mid-sized +0.10% (13,921; t 0.72). Nothing: the signal is the single quiet day with
very large pieces, not a month of somewhat larger ones (the top tenth's footprint is only 1.2
to 1.3). 2 trials (family 43).

## Follow-up 12: smaller results jumps in large pieces (read 18 November 2026, 00:29 ET)

$50M–$300M, results jump of 5% to 15% on 3x volume, plain 15-session exit, after costs,
2010–2017: footprint 1.5+ +3.53% (138 trades; t 2.18; 6 of 8); the rest +1.39% (1,157; t 2.94).
Large pieces mark the better jumps here too (2.5 times the rest), but on 17 trades a year and a
t of 2.2 the cell misses the search bar (150 trades, t 3); the test years were not read.
1 trial (family 44).

## Check 9: large pieces in the weeks after results (read 18 November 2026, 00:35 ET)

Signals whose last results reacted 5 to 30 days before: +1.12% (2010–2017), +2.03%
(2005–2009), +1.22% (2018–2022), +2.19% (2023); the rest +0.87%, +1.69%, +1.94%, +2.08%. No
steady difference: the signal is not the earnings drift seen another way. 1 trial (family 45).

## Follow-up 13: large pieces in sector funds (read 18 November 2026, 00:37 ET)

28 sector and industry funds, footprint 2+, quiet relative up day, 20 sessions, 2010–2017:
+0.25% over SPY (362 trades; t 0.80; 5 of 8). Nothing: in the most liquid funds, large pieces
are ordinary. 1 trial (family 46).

## Follow-up 14: large pieces before an A50 jump (read 18 November 2026, 00:40 ET)

A50 signals with a footprint of 2+ on one of the five sessions before: +2.21% (54) in
2010–2017 against +3.26% for all A50, +6.69% (50) against +4.53% in 2005–2009, +4.45% (57)
against +4.13% in 2018–2022, +2.63% (12) against +5.95% in 2023. Worse in 2010–2017 and 2023:
not a filter. A50 is unchanged. 1 trial (family 47).

## Follow-up 15: a report due by last year's calendar (read 18 November 2026, 00:46 ET)

| Period | Passed cell | Due by last year (a report 336–364 days before) | Not due |
|---|---|---|---|
| 2010–2017 | +0.94% (2,155) | +1.92% (558; t 2.20; 8 of 8) | +0.60% |
| 2005–2009 | +1.78% (2,633) | +1.29% (560; t −0.10; 4 of 5) | +1.92% |
| 2018–2022 | +1.83% (1,906) | **+4.66%** (310; t 2.79; 5 of 5) | +1.28% |
| 2023 | +2.10% (405) | +3.22% (49) | +1.94% |

Better since 2010 (twice the passed cell, and 4.7% a trade in 2018–2022), worse in 2005–2009
with a t near zero: by the rule set beforehand, **not used**. Note: results 8-Ks carry item 2.02
only from August 2004, so the 2005 anniversaries are partly missing, which may weaken the first
period. Together with check 8 it points the same way: big prints ahead of a report are the best
of them. With a real calendar of report dates (the Benzinga question) this is the first thing to
test forward. 1 trial (family 48).
