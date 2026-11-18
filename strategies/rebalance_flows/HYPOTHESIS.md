# Rebalance flows: stocks against bonds in the last days of the month

Written 2026-11-17 22:47 ET, before anything is measured. Every other study tonight looked for an edge
in single stocks, and the short-horizon ones all faded after 2017. This one is about forced
flows in the whole market, which have grown rather than shrunk. Pension funds, target-date
funds and balanced funds hold fixed weights in stocks and bonds and restore them, many of
them at month end. When stocks have beaten bonds during the month, they must sell stocks and
buy bonds in its last days; when bonds have won, the reverse. The amounts are large and the
timing is known. A recent published study (Harvey and others) reports this pressure in index
returns. It is traded with two funds, at any size, with no borrowing.

## Data

Adjusted closes (dividends included) of SPY and TLT from the raw Sharadar fund table, read
only for dates before 2023-11-09. 2005 to October 2023.

## Rule

For each calendar month: **E** is its last session. **R** is SPY's return minus TLT's return
from the previous month's last close to the close **three sessions before E**.

- **Spread trade:** if R is above zero, own TLT and be short SPY (or, for an account that does
  not short, own TLT instead of SPY); if R is below zero, the reverse. Two windows:
  1. **The last days:** from the close three sessions before E to the close of E.
  2. **The first days of the next month:** from the close of E to the close two sessions
     later, in the opposite direction (the pressure giving way).
- Two thresholds: every month; only months with R beyond ±3%.

Costs: 0.03% a round trip on each fund (0.06% for the spread). The trade's return is TLT's
minus SPY's (or the reverse) over the window, after costs. Each cell also shows the long-only
version (owning the fund the rule favours, against owning both half and half).

## Cells

2 windows × 2 thresholds = **4**, family `rebalance_flows`.

## What counts (set now, for one trade a month)

Search 2010–2017: 0.25% a trade after costs, a t over trades of 2.5, six years of eight
positive. Tests on 2005–2009 and 2018–2022, each cell that goes forward run once: 0.12% a
trade, t of 2.0, four years of five, in both. 2023 is a check. The holdout stays sealed.

**Results, 2026-11-17 22:48 ET.** In REPORT.md. Search: the last-days trade points the way expected but is
weak (0.40% a trade, t 1.65; 0.61% beyond ±3%, t 1.66). **The first-days cell met the bar**:
over the first two sessions of a month, the side that won the month before beat the other by
0.72% a trade after costs (96 months, t 3.06, seven years of eight). Tested once: 2005–2009
0.41% (t 1.11, three years of five), 2018–2022 0.26% (t 0.90, four of five). **Not passed.**
4 cells and 2 test runs: 6 trials.
