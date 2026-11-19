# After hours: an overnight gain in most years, missing in 2020 to 2022

**Verdict: not passed; the nearest thing to a new result on 17 November.** Eleven studies, 120
trials, nothing passed both tests. The holdout is untouched.

Plan: [HYPOTHESIS.md](HYPOTHESIS.md). An earnings 8-K accepted after the close (or before
the open); 30 minutes later the stock is read against the 16:00 close; bought in the next
minute that trades **at that minute's high**; at least $50,000 traded outside regular hours
by then. 50,579 entries, 2005 to October 2023. Code: `research/claude/after_hours.py`.

## What a stock does after the after-hours reaction (2010 to 2017, from the minute's high)

| Reaction 30 minutes after the report | Entries | To the next open | To the next close | 15 sessions |
|---|---|---|---|---|
| Down 5% or more | 2,386 | −1.13% | −1.22% | −1.21% |
| Within 5% | 7,238 | +0.04% | −0.06% | +0.41% |
| **Up 5% to 15%** | 1,814 | **+0.91%** | **+1.29%** | **+2.49%** |
| Up 15% or more | 201 | +0.34% | +0.42% | +5.28% |

The owner's idea was right for these years: after hours the price went only part of the way.
A stock up 5% to 15% on its report was, even bought at the worst price of the minute, about
1% higher at the next open and 2.5% higher three weeks on. A stock down kept falling.

## The cells that met the bar, and their tests (after costs)

| After the close, up 5% to 15% | 2010–2017 (search) | 2005–2009 | 2018–2022 |
|---|---|---|---|
| $300M–$2B, sold at the next open | +1.05% (791; t 4.25; 7 of 8) | +0.76% (624; t 2.71; 5 of 5) | **+0.11%** (654; t 0.39; 2 of 5) |
| $300M–$2B, sold at the next close | +1.62% (t 4.20; 8 of 8) | +1.31% (t 1.68) | +0.55% (t 0.64) |
| $300M–$2B, held 15 sessions | +2.72% (t 4.78) | +1.37% (t 1.91; 3 of 5) | +0.16% (t 0.49) |
| $2B and over, held 15 sessions | +1.49% (860; t 3.81) | +1.86% (366; t 4.37; 4 of 5) | +1.35% (1,075; t 1.95; 3 of 5) |
| $50M–$300M, held 15 sessions | +5.24% (163; t 3.25) | +4.58% (165; t 1.78) | +3.51% (174; t 0.47) |

Pass was 0.5%, weekly t of 2.5 and four years of five positive, in both test periods.

- **The overnight gain was there in most years and absent in 2020 to 2022.** In companies of
  $300M to $2B, buying after hours and selling at the next open made money in 14 of the 15
  years from 2005 to 2019 (0.2% to 2.3% a trade; 2014 lost 0.1%), lost 0.3% to 0.6% in each of
  2020, 2021 and 2022, and made 1.6% in the first ten months of 2023 (a figure seen while
  checking this sentence, so not a clean check). The three losing years are the years when
  after-hours trading by the public was at its height; whether the gain is back is what a
  forward test would show.
- **Large companies held for three weeks came closest:** positive in all three periods
  (1.5%, 1.9%, 1.4%) on 2,300 trades, and short of the bar only on steadiness since 2018
  (2020 and 2021 were slightly negative). This is the drift after results again, entered
  earlier and in the largest, cheapest stocks, where the other tests had found none.
- **Small companies show the largest averages (3.5% to 5.2%) and the least proof:** about
  165 trades a period, a median near zero, and half the entries in a minute where under
  $5,000 traded, so the price paid is doubtful even for a small order.
- **Before the open there is nothing:** no cell reached the bar.
- **A reaction of 15% or more after hours does not continue overnight** (0.3% to 0.5%); its
  15-session drift (5%) is rule A50's ground, on few trades.

## The other side: selling short after hours on a bad report (12 cells, 4 test runs)

Same events and reading. Sold short at the **low** of the minute, bought back at the next
open or the next close; the auction allowance, commission and a night's borrow at 10% a year.

| $300M–$2B, down 15% or more after hours | 2010–2017 (search) | 2005–2009 | 2018–2022 |
|---|---|---|---|
| Bought back at the next open | +2.82% (251; t 3.89; 6 of 8) | +2.98% (143; t 3.79; 5 of 5) | +1.60% (201; t 1.15; 5 of 5) |
| Bought back at the next close | +3.41% (t 3.03; 6 of 8) | +4.42% (t 3.12; 5 of 5) | +2.10% (t 1.87; 5 of 5) |
| Worst trade / worst 1% (to the open) | −25% / −22% | −12% / −12% | −26% / −24% |

After costs, to the short seller. No other short cell met the search bar (a fall of 5% to 15%
makes 0.1% to 0.6%; small and large companies down 15% make about 1% on few trades).

- **By the rule set beforehand this is not passed:** in 2018–2022 the weekly t is 1.2 and 1.9
  against the 2.5 required.
- **It is still the steadiest thing found since the earnings drift.** A company of $300M to
  $2B whose stock is down 15% or more half an hour after its report was lower again by the
  next open in 16 of the 18 years, and in every one of the ten test years, by 1.6% to 3.0% a
  trade after costs, about 30 to 40 trades a year. The fall in the mean since 2018 (1.6%
  against 3%) and the wide spread of single trades are why the t fails.
- **Why it might be real:** the same reason as the long side. After hours the first price is
  set by few traders; the funds that must sell a broken story do it at the open and through
  the next day.
- **What would make it untrue or unusable:**
  1. The fill: sold at the low of the minute is harsh, but a quarter of the entries are in a
     minute with under $5,000 traded, and there are no after-hours quotes on disk.
  2. Borrow and the rules for short sales after hours at a retail broker. These are mid-sized
     companies that are normally borrowable, but that has not been checked for one night
     after bad news.
  3. A short's tail: single trades lost 20% to 35% overnight.

## Indicators of our own, a resting order, and a hedge (evening of 17 November, 49 trials)

Three follow-ups on the long side after a report released after the close, in companies of
$300M or more with a rise of 5% or more unless said. Code:
`research/claude/after_hours_score.py`.

**Two indicators read from the first half hour** (15 cells, 12 test runs). Pressure is the
dollars traded after hours as a share of the stock's normal day; hold is how much of the
after-hours peak is left at the reading.

| After costs | 2010–2017 | Weekly t | 2005–2009 | 2018–2022 | t, 2018–2022 |
|---|---|---|---|---|---|
| Hold kept (at 86% or more of its peak), to the next close | 1.75% | 6.48 | 1.68% | 0.46% | −0.10 |
| Hold faded, to the next close | 0.60% | 1.74 | not run | not run | |
| Hold kept, 15 sessions | 2.95% | 6.15 | 2.56% | 0.52% | 0.79 |
| Pressure high (over 22% of a normal day), 15 sessions | 2.99% | 4.69 | 1.77% | −0.18% | 0.75 |
| Pressure high, to the next close | 1.17% | 3.38 | 1.22% | 0.22% | 1.84 |
| Pressure middle, 15 sessions | 2.07% | 3.51 | 2.21% | 0.84% | 0.53 |

Both indicators sorted the stocks in the years to 2017 (a rise still at its peak made three
times what a faded one made by the next close) and neither did after. Six cells met the
search bar; none passed 2018–2022.

**A resting order at the reading price** (18 cells, 2 test runs), filled only if a later
minute trades below it. About 64% fill. It is no better than paying the minute's high:
$300M to $2B, up 5% to 15%, to the next open made 0.79% on its 493 fills in the search years.
The orders that fill are the stocks that came back. The one cell over the bar was $2B and
over, up 5% to 15%, 15 sessions: 1.45% (t 3.20), then 1.21% in 2005–2009 (passed) and 1.45%
in 2018–2022 (t 1.98, three years of five: missed).

**That cell with SPY sold short against it** (2 cells): 1.08% a trade in the search years,
seven years of eight, weekly t 2.80. Under the search bar of 3, so not tested further. The
market was about 0.4 of its 1.5 points.

## What it is worth

Nothing here has passed. Three leads, in the order I rate them:

1. **Long after hours on a rise of 5% to 15%, $2B and over, held 15 sessions.** 1.2% to 1.5%
   a trade in all three periods by either fill, about 170 trades a year, no borrow needed,
   easy to trade in small size. It loses two years in five since 2018 and has never met the
   test on steadiness.
2. **Short after hours on a fall of 15% or more, $300M to $2B, bought back at the next open
   or close.** Positive in every test year; failed only on the t since 2018. It depends on
   shares being there to borrow at that moment, which the owner can only see at the broker.
3. **Long after hours, $300M to $2B, sold at the next open.** Worked in 14 of 15 years to
   2019, lost in 2020 to 2022.

**What they need before money:** after-hours quotes around reports (to see what $5,000 really
pays or receives), the broker's rules and borrow for short sales after hours, and a forward
record. All three can be followed on paper each evening at no cost.

## How robust the short is (2 trials, and a look at short interest)

| Short, after costs | 2005–2009 | 2010–2017 | 2018–2022 | 2023 |
|---|---|---|---|---|
| As tested: the low of the first minute after the reading | +2.98% (143) | +2.82% (251) | +1.60% (201) | +6.66% (44) |
| Only entries whose minute traded $5,000+ | +3.20% (108) | +2.66% (186) | +1.61% (151) | +6.48% (29) |
| Sold at the lowest price of five minutes | +2.17% | +2.23% | +0.70% (t 0.11) | +5.28% |

- **Thin minutes do not carry it**: dropping them changes nothing.
- **The price the order gets does.** With the worst of five minutes, 2018–2022 is left with 0.7%
  a trade. A paper or live order must be quick, at or near the first after-hours price after
  the reading.
- **The shorts are crowded before the report.** For 2018–2023 signals, short interest at the
  last report was a median 8.2% of shares (7.0 days to cover), three times the 2.7% of other
  companies of the size; a tenth were above 23%. Those are the ones a broker may not lend, or
  lend dearly. Code: `research/claude/after_hours_robust.py`.

**The same short before the open** (results filed 06:00–08:30, down 15%+ at 09:00, sold at the
next minute's low, bought back at that session's close; 3 cells): 2010–2017 +1.63% (26 trades,
$50M–$300M), +2.44% (71, t 1.55, $300M–$2B), +2.87% (53, t 2.52, seven years of seven, $2B+).
The same direction, on too few signals to meet the bar.

**When to buy it back** (2 trials; judged as the earnings rule's exits: better only if better in
all three periods):

| Short, after costs | 2005–2009 | 2010–2017 | 2018–2022 | 2023 |
|---|---|---|---|---|
| Bought back at the next open (as tested) | +2.98% | +2.82% | +1.60% (t 1.15) | +6.66% |
| … at 10:00 (spread crossed) | +3.25% | +3.14% | +2.29% (t 1.79) | +7.32% |
| … **at 15:30** (spread crossed) | **+4.55%** | **+3.47%** | **+2.37% (t 2.10)** | **+8.82%** |
| … at the close | +4.42% | +3.41% | +2.10% (t 1.87) | +8.80% |

Holding the short through the next session is better in every period: the selling after bad
results goes on all day. It then stops: bought at that session's close, the same stocks lose
0.5% over the next five sessions and are flat over ten (median −1.8%), so there is no rebound
to buy (2 trials).

**Its neighbours point the same way** (4 cells, held to 15:30, 2010–2017; none meets the bar):
$50M–$300M down 15%+ +1.51% (68 trades), $2B+ down 15%+ +1.37% (108), $300M–$2B down 10–15%
+0.77% (301), $2B+ down 10–15% +0.97% (205), **each positive in seven years of eight**. Bad results
are absorbed slowly across sizes; the mid-sized companies with a fall of 15% or more are where it
is large enough to trade. Bought back at 15:30 the short is closer to the bar it failed (t 2.10
in 2018–2022 against 2.5), and the paper ledger records it beside the open.

**As a book** (a description, not a test): $2,000 a trade, every signal taken, after costs, 639
signals 2005 to October 2023. By year: 2005 $1,143, 2006 $373, 2007 $1,178, 2008 $3,296, 2009
$2,547, 2010 $745, 2011 $507, 2012 $2,980, 2013 −$124, 2014 $2,956, 2015 $2,848, 2016 $4,601,
2017 −$347, 2018 $146, 2019 $752, 2020 $1,653, 2021 $649, 2022 $3,212, 2023 $5,864. **17 of 19
years positive**, about $1,900 a year on average. 537 evenings; at most six signals on one
evening, three or more on only nine. Most come in the reporting months (February, May, July and
August, October and November).

**Beside the earnings rule** (a description): every A50 signal and every short signal at $2,000 a
trade, by year: the two barely move together (correlation of yearly dollars −0.09). The short
adds most where A50 is weakest: 2008 ($3,296 against A50's $3,222), 2012, 2014, 2015 and 2022;
A50's one losing year (2011, −$671) becomes −$164 with both.

**Checked for data errors** (the danger for a short bought back at the open is a bad, too-low
open price): the eight largest winners all have next-day opens equal to the first regular
minute in the minute data, and are real collapses (Green Dot 2012-07-27, Sequenom 2009-04-30,
Huron Consulting 2009-08-03, Funko 2022-11-04, Design Therapeutics 2023-08-15 and others). The
ten largest winners make 23% of the total over 639 trades; without the two largest, 2023 is
still about +4.8% a trade.

## Following the short on paper (built 2026-11-17)

`tools/owner/paper_after_hours.py` keeps a paper ledger of the after-hours short, the strongest
lead (+6.7% a trade on 44 trades in 2023, read once; see `strategies/leads_2023`). Run it the
morning after an evening of results (after 09:35, so the next open exists):

```
export SEC_USER_AGENT="Your Name you@example.com"
uv run python tools/owner/paper_after_hours.py                   # the last evening
uv run python tools/owner/paper_after_hours.py --day 2026-11-18  # a given evening
uv run python tools/owner/paper_after_hours.py --since 2026-11-09   # catch up: every evening since
uv run python tools/owner/paper_after_hours.py --since 2026-11-09 --redo   # read them again
uv run python tools/owner/paper_after_hours.py --borrow "ABCD=yes, 0.4%"   # what IBKR showed
```

SEC_USER_AGENT must be your name and a real email address: the SEC refuses a request that does
not say who is calling (HTTP 403), and the tool then stops and says so. Until 2026-11-19 an
index that could not be read counted as an evening with no 8-Ks, and eight evenings
(2026-11-09 to 11-18) were recorded empty; the next run reads them again. The next day's index is
published late in its evening, so a morning run reads the evening in part (filings accepted
before 17:30) and a later run reads the rest; an evening with no index yet is not recorded,
and a filer that could not be read is read on the next run. An evening takes about 700 requests
to the SEC (one per 8-K filer); the tool sends at most four a second, reads each company once a
run, and if the SEC pauses the address anyway (it did on 2026-11-19, about 730 requests into
a catch-up) it waits eleven minutes and carries on.

It reads every 8-K in the SEC's daily index for the evening (and the next day, where filings
accepted after 17:30 are dated), keeps the results 8-Ks accepted between 16:00 and 18:30, and
for each fetches the stock's market value, normal volume and that evening's minute bars from
Massive. The rule is the research rule exactly (a test holds the reading to the research code
on 400 random days); the candidates come from the filings, never from the next morning's
price. **Checked on real data:** run over the 2022 and 2023 events with the ledger's own code, it
finds the same signals as the research (64 and 44) and the same returns within 0.16 of a point
(2.62% against 2.51%, 6.82% against 6.66%; `research/claude/after_hours_paper_check.py`).
Ledger: `paper/after_hours/report.md`. It sends no order. Each signal is settled at the
next open (the rule as tested) and, from a run after 15:32 the next day, also as held to 15:30
(the better exit).

**Start with `--since 2026-11-09`.** The holdout ends on 2026-11-06 and November is the busiest
month of the small and mid-sized companies' reporting season, so the evenings since then give a
first forward reading at once. A market holiday simply has no filings.

What the ledger is for: about one signal a week, most in the reporting seasons. For each, record
whether IBKR showed shares to borrow and at what fee (`--borrow`); whether the trade could have
been made at all is the first question. The fill (the low of the first minute after the
reading) is the second: a third of 2023's entries traded under $5,000 in that minute.

## Reproduce

```
cd research/claude
uv run python after_hours.py events
uv run python after_hours.py collect 2005 2023
uv run python after_hours.py search
uv run python after_hours.py test after mid up5 open
uv run python after_hours.py lows 2005 2023
uv run python after_hours.py search_short
uv run python after_hours.py test_short mid down15 open
uv run python after_hours_score.py peaks 2005 2023
uv run python after_hours_score.py search
uv run python after_hours_score.py limits 2005 2023
uv run python after_hours_score.py limit_search
uv run python after_hours_score.py hedged search
```

## Who sells after hours (1 trial, read 18 November 2026, 00:30 ET)

The short split at the 2010–2017 median of its after-hours footprint (shares per trade after
hours against the stock's normal; the median is 2.24), after costs, bought back at the open:

| Period | Short | Large pieces | Small pieces |
|---|---|---|---|
| 2005–2009 | +2.98% (143) | +3.84% (64) | +2.29% (79) |
| 2010–2017 | +2.71% (250) | +3.29% (125) | +2.13% (125) |
| 2018–2022 | +1.56% (198) | +0.67% (67) | +2.02% (131) |
| 2023 | +6.13% (43) | +5.17% (29) | +8.11% (14) |

Funds selling in large pieces marked the better shorts to 2017 and the worse ones since: not a
filter. The short is unchanged. (Code: `research/claude/after_hours_footprint.py`.)

## Who buys after hours (1 trial, read 18 November 2026, 00:32 ET)

$2B and over, up 5% to 15% after hours, bought at the minute's high, held 15 sessions, after
costs, split at the 2010–2017 median after-hours footprint (1.76):

| Period | Long | Large pieces | Small pieces |
|---|---|---|---|
| 2005–2009 | +1.85% (362) | +1.33% (164) | +2.29% (198) |
| 2010–2017 | +1.54% (854) | +1.51% (427) | +1.56% (427) |
| 2018–2022 | +1.07% (1,046) | +0.22% (426) | +1.66% (620) |
| 2023 | +0.28% (179) | +1.38% (94) | −0.94% (85) |

Not a filter: the larger-piece half did worse in every period but 2023. 2 trials for the two
footprint splits (family 122).

## Who buys after hours in small companies (2 trials, read 18 November 2026, 00:39 ET)

$50M–$300M, up 5% or more after hours on results, bought at the minute's high, held 15
sessions, after costs, split at the 2010–2017 median after-hours footprint (2.31):

| Period | Small-company long | Large pieces | Small pieces |
|---|---|---|---|
| 2005–2009 | +4.22% (208; t 1.66) | +5.35% (55; t 1.02; median −2.39%) | +3.81% (153) |
| 2010–2017 | +5.25% (210; t 3.61) | +6.14% (105; t 2.75; median +5.06%) | +4.36% (105) |
| 2018–2022 | +3.65% (251; t 0.58) | **+9.93%** (80; t 2.03; median +4.46%) | +0.71% (171; t −0.12) |
| 2023 | +6.43% (44) | +7.62% (30; median +4.41%) | +3.90% (14) |

**As a filter it passes the rule set beforehand**: the larger-piece half is better per trade in
all three periods and in 2023, and since 2018 it carries all of the small-company long (the
small-piece half made 0.7%). This is the owner's "enter earlier" idea on A50's ground: buying
on the evening of the results when the after-hours buying comes in large pieces. It is a lead,
not a rule: 10 to 16 trades a year, weekly t of 1.0 to 2.8, a negative median in 2005–2009 (the
mean there rests on one +231% trade), and half the entry minutes traded under $5,000, so the
price paid is the weakest part. The paper ledger for the short could record these evenings
too; not built tonight.

**Its fills** (1 trial): kept only where the entry minute traded $5,000 or more, the larger-piece
half makes +7.84% (28 trades; median +0.65%), +5.69% (50; median +4.94%), +5.42% (39; median
+0.66%) and +0.83% in 2023 (16; median −0.38%). Still positive on average, but outside
2010–2017 the typical trade is near zero once the doubtful minutes are dropped: the price paid
in a thin after-hours minute is carrying much of it. A lead to watch, not to trade.

**Bought at the next open instead** (1 trial; the same signal, known before the open, bought in
the opening auction, sold at the close 15 sessions later):

| Period | Small-company long | Large pieces | Small pieces |
|---|---|---|---|
| 2005–2009 | +3.41% (208) | +4.28% (55; t 0.72) | +3.10% |
| 2010–2017 | +3.90% (210) | +5.06% (105; t 2.38) | +2.74% |
| 2018–2022 | +4.42% (251) | **+8.53%** (80; t 1.89) | +2.50% |
| 2023 | +7.23% (44) | +7.02% (30) | +7.68% (14) |

Most of the gain survives without an after-hours fill: the larger-piece half is better in all
three periods bought in the auction (by 0.9 to 4.1 points; 2023 about even). That removes the
weakest part of the lead (the price in a thin after-hours minute) and leaves the other: about
ten trades a year and a weekly t under 2.5. The cleaner form of the lead to watch is this one:
**on the evening of results, a small company up 5%+ after hours with its after-hours trading in
large pieces; buy the next open, hold 15 sessions.** It sits on A50's ground a day earlier and
with a lower jump; how much the two overlap has not been measured.

**Overlap with A50** (1 trial): of the larger-piece signals bought at the next open, 22 of 55,
44 of 105, 28 of 80 and 12 of 30 (2023) went on to become A50 signals a day or two later.
Those made +14.7%, +7.4%, +14.1% and +17.5%; **the rest made −2.68% (2005–2009), +3.40%,
+5.52% and +0.06% (2023)**. The lead is mostly A50 caught a day earlier, before anyone can know
which jumps A50 will take; on its own it is weak. It stays a note on A50's timing, not a second
strategy: it suggests the A50 jumps that began after hours in large pieces gained a great deal
on their first day, which A50's entry (the open after the signal day) does not get.

**Mid-sized companies** (1 trial): $300M–$2B up 5% to 15% after hours, bought at the next open,
15 sessions: the larger-piece half −0.53% (2005–2009), +1.77%, +0.43%, −3.12% (2023), against
+0.34%, +1.39%, −0.29%, −3.04% for all. Worse in 2005–2009: not a filter; and the cell itself
is flat outside 2010–2017.

**The evening version of A50's jump** (1 trial): small companies already up 15%+ after hours,
bought at the next open, 15 sessions: all +2.97% (44), +3.53% (48), +4.96% (79), +8.03% (2023,
10); with large after-hours pieces −4.73% (8), +7.15% (23), +10.56% (20), +2.23% (6). Far too
few, and worse in 2005–2009 and 2023: not a filter. A50's own two-day test stays the better
gate.
