# Filing drift: the earnings rule where the numbers first appear in the 10-Q

Written 2026-11-17 22:22 ET, before anything is measured. The one rule that has passed everything here
(A50) buys a small company the session after a results 8-K when the stock has risen 15% or
more over two sessions on five times its normal volume. Many small companies issue no results
press release: their quarter first becomes public in the 10-Q or 10-K itself. Those reports
are the most neglected of all and A50 never sees them, because it needs the 8-K. Family 18
(16 November) tried jumps on days with "other filings" by count, mixing every kind of filing;
this uses the quarterly report alone.

## Events

A 10-Q or 10-K (original, not amended), from the owner's download of SEC filing times, for a
listed common stock. Its **event session** is the first session after the day it was
accepted (the convention A50 uses for the 8-K date). The company had **no results 8-K** in
the ten sessions up to and including that session (A50's own event flag). 2005 to 13 October
2023.

## Rule and cells

On the event session, as A50 reads it: two-session return of 15% or more, two-session dollar
volume five times normal, market value $50M to $300M. Bought at the next open, sold at the
close 15 sessions after the signal, costs as A50. Three cells:

1. **Q50:** exactly A50's thresholds.
2. A rise of 10% or more instead of 15%, otherwise as Q50.
3. Q50's thresholds in companies of $300M to $2B.

**3 cells**, family `filing_drift`.

## What counts

As A50's search: 2010–2017, 1% a trade after costs, weekly t of 3, six years of eight, and
150 trades; if a cell has under 150 trades but meets the rest, it is reported and taken to
the tests anyway, with the count said. Tests on 2005–2009 and 2018–2022, each cell that goes
forward run once: 0.5%, t of 2.5, four years of five, in both. 2023 is a check. The holdout
stays sealed (its period holds no raw filing data here; the download stops at 2023-11-08).
