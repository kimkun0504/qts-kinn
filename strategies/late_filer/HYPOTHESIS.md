# Late filer: buying when the overdue report finally arrives

Written 2026-11-17 22:38 ET, before anything is measured. A company that files a notice of late filing
(NT 10-Q or NT 10-K) tells the market something is wrong: an audit not finished, a
restatement, a covenant. Holders who cannot wait sell. When the report then arrives inside
the grace period, part of the doubt is gone, and in small companies, where belief is slow,
the price may take weeks to recover. Nothing in this repository has used the late-filing
notices (from the owner's download of SEC filing times).

## Events

A notice of late filing (NT 10-Q or NT 10-K) for a listed common stock, followed by that
company's 10-Q or 10-K **within 20 days**. Market value $50M or more, $250,000 a day and a
close of $1 or more on the session before the notice; no results 8-K in the 10 sessions
before the report's session (as `filing_drift`, so a report already told in a press release
is not counted twice). 2005 to 13 October 2023; raw filings read only before 2023-11-09.

## Trades

- **At once:** bought at the first open after the report was accepted.
- **After a session:** bought at the open after the first full session following the report
  (A50's convention), so the first reaction is seen before buying.

Held to the close 15 sessions after the entry. Costs: the auction allowance and commission,
as the earnings rule.

Groups: every event; events where the stock fell 10% or more from the close before the notice
to the close before the report. Sizes: $50M to $300M; $300M or more.

## Cells

2 entries × 2 groups × 2 sizes = **8**, family `late_filer`.

## What counts

Search 2010–2017: 150 trades (reported and taken on if fewer but the rest is met), 1% a trade
after costs, weekly t of 3, six years of eight. Tests on 2005–2009 and 2018–2022, each cell
that goes forward run once: 0.5%, t of 2.5, four years of five, in both. 2023 is a check.
The holdout stays sealed.

**Results, 2026-11-17 22:42 ET.** In REPORT.md. **None of the 8 cells meets the bar; the arrival of the
overdue report is followed by more falling, not relief.** 1,806 events (2003–2023); in
2010–2017, 353 (fewer than planned for). Small companies lost 3.0% a trade in 15 sessions
(median −3% to −4%, one or no year of eight positive); those already down 10% since the notice
lost 7% to 8%. Larger companies about −0.2%. 8 trials. No tests run.
