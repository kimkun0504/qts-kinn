# Report timing: a company later than its own calendar, or earlier

Written 2026-11-17 23:14 ET, before anything is measured. A published result (Johnson and So, 2018):
companies that report later than their own usual date tend to bring bad news, and their stock
falls before and as it comes out; early reporters tend to bring good news. A company's usual
date is in the owner's SEC download: every results 8-K with the time it was accepted. That a
company is late can be known on the expected day itself, before the report.

## Events

From the reaction sessions of every results 8-K (the table of family 24, 2004–2023), for a
listed common stock: the **expected session E** of a report is the first session on or after
the reaction session of the same company's report 364 days earlier (one found 344 to 384 days
before). A report is not due if the company reported in the 30 days before E.

- **Late (short):** no report by the close of **E+2** (or **E+5**) sessions. Sold short at that
  close; bought back at the close of the session after the report's reaction session, or after
  30 sessions if it never comes. Borrow 1% a year (companies of $300M or more).
- **Early (long):** the reaction session comes **7 or more calendar days before E**. Bought at
  the open after the reaction session, held 15 sessions.

Market value at the signal: $300M to $2B and $2B or more for the shorts; $50M to $300M and
$300M to $2B for the longs. $250,000 a day. Costs: the auction allowance and commission.

## Cells

Late: 2 waits × 2 sizes = 4; early: 2 sizes = 2. **6 cells**, family `report_timing`.

## What counts

Search 2010–2017: 1% a trade after costs, a weekly t of 3, six years of eight, 150 trades.
Tests on 2005–2009 and 2018–2022, each cell that goes forward run once: 0.5%, t of 2.5, four
years of five, in both. 2023 is a check. The holdout stays sealed.

**Results, 2026-11-17 23:15 ET.** **None of the 6 cells meets the bar.** Late reporters, sold short at E+2
or E+5: −0.11% to −0.44% a trade (they did not fall; 9,962 trades in $300M–$2B at E+2). Early
reporters bought after the report: −0.79% ($50M–$300M) and +0.21% ($300M–$2B, t 2.50). 6
trials. No tests run.
