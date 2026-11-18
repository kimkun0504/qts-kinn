# Russell move: a company that drops from the Russell 1000 to the top of the Russell 2000

Written 2026-11-17 23:53 ET, before anything is measured. Each June the Russell indexes are rebuilt from
market values on the last trading day of May (the rank day). A company that shrinks out of the
Russell 1000 becomes one of the largest members of the Russell 2000, where index funds hold far
more of each company than Russell 1000 funds do: it must be bought, in size, at the close of
reconstitution day. Published work (Chang, Hong and Liskovich, 2015) finds these companies
beat those just above the line. The membership lists are not on disk, so it is rebuilt from
market values; the plan states the proxy and keeps it fixed.

## Events

For each year 2005 to 2023, rank on the rank day (the last session of May) every stock in the
price table that is domestic common stock on a US exchange, $1 or more, by its market value at
that close (marketcap on the next session's row). A company **moves down** if it ranked 1,000
or better on the previous year's rank day and ranks worse than 1,000 now; it **moves clearly**
if it now ranks 1,151 to 1,600 (well past any band Russell applies).

Reconstitution day: the last Friday of June, or the Friday before it when that falls on the
29th or 30th (Russell's rule).

## Trades (4 cells, family `russell_move`)

Kind (moved down, moved clearly) × window:

1. **Into reconstitution:** bought at the open of the first session after the rank day, sold
   at the close of reconstitution day.
2. **After reconstitution:** bought at the open of the session after reconstitution day,
   held 20 sessions.

Costs: the auction allowance and commission. Each trade is measured against the average
common stock ranked 1,001 to 3,000 on the same rank day, bought and sold at the same times.

## What counts

One event date a year, so the weekly t is a t over years. Search 2010–2017: 150 trades, 1% a
trade over that average, t of 3, six years of eight, positive after costs. Tests on 2005–2009
and 2018–2022 at 0.5%, t of 2.5, four years of five. 2023 is a check. The holdout stays sealed.

## Follow-up: selling them short into reconstitution (written 2026-11-17 23:54 ET, after the 4 cells)

The companies that moved down lost to the average small company from the rank day to
reconstitution in all eight search years (above). The trade, **sold short at the open of the
first session after the rank day and bought back at the close of reconstitution day**,
measured as the short's return over the average of ranks 1,001 to 3,000 (a short hedged with
the small-company average; IWM would be the tradable hedge), and also after costs and borrow
at 10% a year for the days held, unhedged. **2 cells** (moved down, moved clearly). The search
years are the mirror of what was read, so only the tests count: 2005–2009 and 2018–2022, 0.5%
over the average, t of 2.5 over the five years, four years of five. 2023 is a check if both pass.
