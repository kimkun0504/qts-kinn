# Foreign drift: the earnings rule in companies that file no 8-K

Written 2026-11-17 15:37 ET, before the data for it is on disk (the owner has not yet run
`tools/owner/download_edgar_times.py --what other`). Nothing has been measured.

## Why

Rule A50 (`strategies/earnings_drift`) needs an earnings 8-K. Foreign companies listed in
the US (Israeli, Chinese, Greek, Canadian and others) do not file 8-Ks; they furnish results
on a **6-K**. They are in the stock universe and in the price data, and the rule has never
taken one of them: not in the search, not in the tests, not in the holdout run, not in the
paper ledger. If the drift after a jump on results is real, it should be there too. That
makes this a test the earnings rule can fail, on companies it has never seen, and a way to
more signals if it passes.

## The rule, fixed now

**F50.** A company that files 6-Ks and no 8-Ks (at least one 6-K and no 8-K in the 400 days
before). S is the session after the date of a 6-K (as A50 reads the 8-K's date). At the close
of S: the two-day return is 15% or more and the larger of the two days' dollar volume is 5
times normal. Common stock or ADR, market value $50M to under $300M, close $1 or more,
$250,000 a day. Buy at the next open, sell at the close 15 sessions after S. Costs: the
auction allowance and commission, as A50.

A 6-K is used for many things besides results. The jump and the volume are what select the
ones that matter; no attempt is made to read which 6-Ks are results.

**F50Q:** the same with A50Q's quality test where the facts exist (up over 250 sessions, or
debt above cash). Foreign filers often have no quarterly balance sheet in the data; the
count of signals with and without the fact is reported.

Also measured, one cell each: F50 in companies of $300M to under $2B. 3 trials.

## Periods and what counts

Nothing is chosen, so there is no search period. The rule is run on 2005–2009, 2010–2017 and
2018 to 13 October 2023.

- **Pass:** 100 trades or more in all; 2% or more a trade over all years; above zero in each
  of the three spans; weekly t of 2.5 or more over all years.
- A pass makes F50 a candidate for one run on its **own holdout** (2023-11-09 on, which no
  rule has read for these companies) and a book in the paper ledger. A fail closes it.

## Known before starting

A50's own figures (3.3% to 4.5% a trade by span). Family 18 found that jumps "with no filing"
or "on other filings" under $300M do not drift; those groups pooled every company and every
kind of filing as Sharadar's events table has them (8-Ks only), so a 6-K filer's results day
sat in "no filing" beside spikes with no news at all. This is the first look at them apart.
