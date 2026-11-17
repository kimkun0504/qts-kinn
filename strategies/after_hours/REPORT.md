# After hours: the edge was there until about 2019

**Verdict: not passed; the nearest thing to a new result today.** 30 cells on 2010 to 2017,
five met the bar, none passed both tests. 40 trials. The holdout is untouched.

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

- **The overnight gain was real for fifteen years and then stopped.** In companies of $300M
  to $2B, buying after hours and selling at the next open made money in every year from 2005
  to 2019 (0.45% to 1.48% a trade) and lost in 2020, 2021 and 2022. Far more people trade
  after hours since 2020; the simplest reading is that the gap they left has been closed.
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

## What it is worth

Nothing here is a strategy yet. Two things are worth carrying forward:

1. **The large-company cell is a lead for the paper ledger**, not for money: it is positive
   everywhere, cheap to trade, takes any size, and comes in different stocks from the
   earnings book. It failed its test on the t-statistic, so it stays a lead.
2. **The fills are the weak point of everything on this page.** There are no after-hours
   quotes on disk. Before any of this is trusted, a sample of after-hours quotes around
   reports is needed to see what a $5,000 order would have paid.

## Reproduce

```
cd research/claude
uv run python after_hours.py events
uv run python after_hours.py collect 2005 2023
uv run python after_hours.py search
uv run python after_hours.py test after mid up5 open
```
