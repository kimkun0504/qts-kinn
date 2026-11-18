# Night bids: after hours the resting order is picked off, and following the move loses too

**Verdict: closed.** 45 cells on 2010 to 2017 in two parts, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 45 trials. The holdout is untouched.

The owner's idea: after 16:00 almost nobody quotes, so a small account might be paid for
being there. Every listed common stock of $50M or more on every session from 2005 to October
2023 with no results due, read from trades by the minute between 16:05 and 19:59. Code:
`research/claude/night_bids.py`, `research/claude/night_moves.py`.

## A buy order resting below the close (18 cells)

Filled when whole minutes trade under it (5 trades and $5,000), at the order's price;
cancelled if the company files anything first; sold at the next open.

| 2010–2017, after costs | Fills | A trade | Median | Weekly t | Worst | Filed before the next open |
|---|---|---|---|---|---|---|
| 3% under, $50M–$300M | 1,762 | −3.16% | −0.39% | −10.04 | −82% | 27% |
| 3% under, $300M–$2B | 2,756 | −1.96% | −0.62% | −11.51 | −87% | 28% |
| 3% under, $2B+ | 1,994 | −0.92% | −0.25% | −6.61 | −86% | 23% |
| 5% under, $50M–$300M | 862 | −5.55% | −2.21% | −10.30 | −81% | 39% |
| 5% under, $300M–$2B | 1,236 | −2.85% | −1.05% | −8.42 | −87% | 35% |
| 5% under, $2B+ | 725 | −1.36% | −0.38% | −4.95 | −85% | 26% |
| 8% under, $50M–$300M | 468 | −7.36% | −3.57% | −8.54 | −81% | 41% |
| 8% under, $300M–$2B | 583 | −3.79% | −1.52% | −7.23 | −87% | 36% |
| 8% under, $2B+ | 277 | −1.89% | −0.93% | −3.88 | −85% | 27% |

Sold at the next close instead, every cell is as bad or worse.

- **The seller after hours has read the news.** The worst fills are FXCM on 15 January 2015
  (−87%), NVAX on 15 September 2016 (−85%), and a row of drug-trial failures: announced by
  press release after the close, with nothing at the SEC until the next day. The order is
  filled on the way down.
- **Checking the SEC feed does not protect it.** Orders were cancelled if a filing came
  first. A quarter to two fifths of the fills still had a filing before the next open; the
  news reached the tape before it reached the SEC.
- The typical fill loses a little and one in twenty loses 20% or more. This is the strongest
  result of the day, and it points the wrong way for a buyer.

## Trading with the move instead (27 cells)

The same reading used as a detector of news: once whole minutes have traded 3%, 5% or 8%
beyond the close, buy a rise at the next minute's high, or sell a fall short at the next
minute's low; close at the next open.

| 2010–2017, after costs | Trades | A trade | Weekly t | Years positive | Paid or received at |
|---|---|---|---|---|---|
| Rise of 5%, $300M–$2B, bought | 1,304 | −0.97% | −5.17 | 0 of 8 | +7.0% |
| Rise of 5%, $2B+, bought | 789 | −1.06% | −4.09 | 0 of 8 | +6.5% |
| Rise of 5%, $50M–$300M, bought | 1,064 | −0.23% | −1.24 | 2 of 8 | +7.4% |
| Fall of 5%, $300M–$2B, sold short | 1,008 | −0.49% | 0.58 | 2 of 8 | −7.1% |
| Fall of 5%, $2B+, sold short | 636 | −1.17% | −4.24 | 0 of 8 | −6.4% |
| Fall of 5%, $50M–$300M, sold short | 649 | −0.17% | −0.51 | 3 of 8 | −7.7% |

The 3% and 8% levels and the sale at the next close read the same; 25 of 27 cells lose.

- **The move gives a little back by the next open, in both directions.** A stock first seen
  5% up is paid for at 7.0% up and opens 6.2% up; one first seen 5% down is sold at 7.1% down
  and opens 6.4% down (medians, $300M to $2B). About a tenth of the move is an overshoot.
- **So following the move loses** that tenth plus costs, and the first part showed that
  buying against it loses far more on the nights the news is real.
- Half of the entry minutes trade at a single price; a quarter have a range over 1.1% and a
  tenth over 2.5% (2015). The loss is the overshoot, more than the width of the minute.

## What it means

After hours the price is about right within minutes of unscheduled news, with a small
overshoot. Following the move pays the overshoot; fading it with a resting order earns the
overshoot on ordinary nights and gives back many times it on the night the news is real.
There is no after-hours trade here for an account of any size without knowing the news
before the order fills. The practical use is for a holder: **a fall of 3% or more after
hours on real trading, with no results due, is news more often than noise, and it is not a
price to buy.**

Not tested: quotes (none on disk, so fills are inferred from trades); the premarket.

## Reproduce

```
cd research/claude
uv run python night_bids.py daily
uv run python night_bids.py filings
uv run python night_bids.py collect 2005 2023
uv run python night_bids.py search
uv run python night_moves.py collect 2005 2023
uv run python night_moves.py search
```
