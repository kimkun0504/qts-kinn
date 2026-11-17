# Stake filings: buying after a holder reports crossing 5%

Written 2026-11-17 15:37 ET, before the data for it is on disk (the owner has not yet run
`tools/owner/download_edgar_times.py --what other`). Nothing has been measured.

## Why

What has worked here is hard information about a small company that the market takes days
to finish pricing (the drift after results). The other filing of that kind is the
**Schedule 13D**: a holder who has crossed 5% of a company and may seek to influence it must
say so within days. Published studies of activist filings report a rise around the filing
and, in some, a drift after it. It has not been tested here, and the filings were not on
disk until the SEC's bulk file was fetched.

## Events

An **initial SC 13D** (not an amendment) in the filing list of the company that is its
subject, 2005-01-03 to 2023-10-13. R is the first session whose close comes after the SEC
accepted the filing. The signal is read at the close of R; buy at the open of R+1.

Two limits of the data, stated now: the bulk file does not say who filed, so a first filing
by a new holder and a re-filing cannot be told apart beyond the form type; and a company's
list also holds 13Ds that the company itself filed about others. To keep those out, companies
in the financial sector are left out, and so is any company with more than six initial 13Ds
in a calendar year.

**Control:** initial **SC 13G** filings (a passive holder crossing 5%), treated the same way.
If 13G does what 13D does, the effect is not about activism.

## Family `stake_filings`: 24 cells

Common stock, close $1 or more, $250,000 a day. Sizes: $50M to $300M, $300M to $2B, $2B
and over.

- 13D × 3 sizes × 3 reactions on R (any; up 2% or more; up 5% or more on twice normal
  volume) × 2 holds (15 and 40 sessions) = 18.
- 13G × 3 sizes × 2 holds, any reaction = 6.

Costs: the auction allowance and commission on both sides.

## Periods and what counts

- **Search: 2010 to 2017.** A cell goes forward only with 150 trades or more; a mean after
  costs of 2% or more (15 sessions) or 4% or more (40 sessions); a weekly t of 3 or more; six
  years of eight positive; and a mean of 1% or more above the small-stock index fund (IWM)
  over the same days.
- **Test: 2005 to 2009 and 2018 to 2022,** each cell that goes forward run once. Pass: half
  the search bar's mean, weekly t of 2.5, four years of five positive, in both.
- **Check: 2023 to 13 October,** once. **Holdout: from 2023-11-09, sealed,** untouched by
  this family.

## Known before starting

Nothing measured here. From the literature: the rise is mostly on and before the filing day,
which a buyer at the next open does not get; what is left afterwards is the question.

**Results, 2026-11-17 15:59 ET.** In REPORT.md. No cell meets the search bar, so no test was
run. After a 13D a stock makes 1.1% to 1.8% after costs over 15 to 40 sessions, 0.5% to 0.9%
more than the index fund, with weekly t under 3 except in the middle size (which misses the
mean). The 13G control does the same. 24 trials. Closed.
