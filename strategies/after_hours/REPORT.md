# After hours: an overnight gain in most years, missing in 2020 to 2022

**Verdict: not passed; the nearest thing to a new result on 17 November.** Seven studies, 109
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

## Following the short on paper (built 2026-11-17)

`tools/owner/paper_after_hours.py` keeps a paper ledger of the after-hours short, the strongest
lead (+6.7% a trade on 44 trades in 2023, read once; see `strategies/leads_2023`). Run it the
morning after an evening of results (after 09:35, so the next open exists):

```
export SEC_USER_AGENT="Your Name your@email"
uv run python tools/owner/paper_after_hours.py                   # the last evening
uv run python tools/owner/paper_after_hours.py --day 2026-11-18  # a given evening
uv run python tools/owner/paper_after_hours.py --borrow "ABCD=yes, 0.4%"   # what IBKR showed
```

It reads every 8-K in the SEC's daily index for the evening (and the next day, where filings
accepted after 17:30 are dated), keeps the results 8-Ks accepted between 16:00 and 18:30, and
for each fetches the stock's market value, normal volume and that evening's minute bars from
Massive. The rule is the research rule exactly (a test holds the reading to the research code
on 400 random days); the candidates come from the filings, never from the next morning's
price. Ledger: `paper/after_hours/report.md`. It sends no order.

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
