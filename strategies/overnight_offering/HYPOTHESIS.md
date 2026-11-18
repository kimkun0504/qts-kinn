# Overnight offerings: the morning after a company sells new shares

Written 2026-11-17 22:18 ET, before anything is measured. Tonight's studies found effects that worked to
2017 and stopped. This one is chosen because its events became far more common after 2018
(small companies selling shares overnight, registered directs, at-the-market deals) and
because the move it trades is caused by new supply rather than news about the business.

## Why

A company that sells shares overnight prices them under the last close. The stock opens near
the offering price, and the buyers of the deal (often funds that flip) sell into the first
session. If the drop is mostly that supply, the price should come back once it has been
absorbed; if it is information (the company needed money), it should keep falling. Which one
wins, and in which size, is what is measured. Nothing in this repository has used the
prospectus filings.

## Events

A prospectus supplement (form 424B5, from the owner's download of SEC filing times) accepted
**from 16:00 on session D to 09:15 on D+1**, for a company whose stock is listed common
stock with a market value of $50M or more and $250,000 a day on D, a close of $1 or more,
and **no results due** (no results 8-K from 12:00 on D to 09:30 on D+1). **Serial issuers are
dropped:** a company with more than six 424B5 filings in the 365 days before D (banks and
others selling notes). One event per company per night; a company counts again only 20
sessions after its last event.

The **gap** is D+1's open against D's close.

## Trades

- **Long:** buy at D+1's open; sell at D+1's close, at the close 5 sessions after D+1, or at
  the close 15 sessions after D+1.
- **Short:** sell short at D+1's open; buy back at D+1's close or 5 sessions later. A borrow
  fee of 10% a year (small companies after an offering are often far dearer to borrow; the
  report says so if a short cell goes forward).

Gaps: down 3% to 10%; down 10% or more. Sizes: $50M to $300M, $300M to $2B, $2B or more.
Costs: the auction allowance and commission both ways, as the earnings rule.

## Cells

Long 2 gaps × 3 sizes × 3 exits = 18; short 2 gaps × 3 sizes × 2 exits = 12. **30 cells**,
family `overnight_offering`.

## What counts

Search 2010–2017: 150 trades, 1% after costs, weekly t of 3, six years of eight. Tests on
2005–2009 and 2018–2022, each cell that goes forward run once: 0.5%, t of 2.5, four years of
five, in both. 2023 (to 13 October) is a check for a cell that passes. The holdout stays
sealed. Every query on the raw filings is limited to dates before 2023-11-09.

**Results, 2026-11-17 22:20 ET.** In REPORT.md. **None of the 30 cells meets the bar.** 14,210 overnight
424B5 filings by companies in the universe (2003–2023); four fifths moved nothing at the open
(routine shelf takedowns), 2,230 opened 3% to 10% down and 681 10% or more down (median
−14.7%). Bought at the open, they lost in almost every cell (small down 10%+: −1.1% by the
close, −1.8% in 15 sessions); sold short at the open they made nothing either (−0.4% to
+1.1%, weekly t under 1.5). The open is about the right price after an overnight deal. 30
trials. No tests run.
