# Deal spread: buying a company that is being acquired, and holding to the close of the deal

Written 2026-11-17 15:48 ET, before the data for it is on disk (the owner has not yet run
`tools/owner/download_edgar_times.py --what other`). Nothing has been measured.

## Why

Two findings today point here. The earnings book uses a third of the account on average and
is nearly empty between reporting seasons; and every search for a fast pattern after news
came back empty. A stock under an agreed takeover is the opposite kind of trade: slow,
small, and paid for carrying the risk that the deal breaks. It trades a little under the
offer until the deal closes; the buyer earns that gap most of the time and loses much more
when a deal fails. It does not depend on reporting seasons, the companies are larger and
cheaper to trade, and it could work the idle money. Whether what is left after costs and
after the broken deals is worth having is the question.

## Events

From the SEC's filing lists (2005-01-03 to 2023-10-13):

- **Tender offer:** the first **SC 14D9** in a company's list in 250 days. Only the target of
  a tender offer files it.
- **Merger by vote:** the first **DEFM14A** in 250 days, when the stock is **pinned**: the
  standard deviation of its daily returns over the last 20 sessions is 0.75% or less. A
  target under an agreed deal trades like that; an acquirer asking its own holders to vote
  does not. The unpinned DEFM14As are measured once as the control.

The filing lists do not give the offer price or say cash or stock, so the gap itself is not
measured; the trade is judged by what it made.

R is the first session whose close comes after the SEC accepted the filing; buy at the open
of R+1. Sell at the last close the stock trades (the deal closing) or at the close H
sessions after R if it is still trading.

## Family `deal_spread`: 10 cells

Common stock, close $1 or more, $250,000 a day. Two sizes: $50M and over; $300M and over.

- Tender offer × 2 sizes × H of 20 and 60 = 4.
- Merger by vote, pinned × 2 sizes × H of 60 and 120 = 4.
- Merger by vote, not pinned × 2 sizes × H of 120 = 2 (control).

Costs: the auction allowance and commission on both sides (one side when the stock is taken
out for cash: charged in full anyway).

## Periods and what counts

- **Search: 2010 to 2017.** A cell goes forward only with 100 trades or more, a mean of 1% or
  more a trade after costs, a weekly t of 3 or more, and seven years of eight positive. The
  worst trade, the worst 1% and the mean sessions held are reported with it, and the return
  a year on the money while it is deployed.
- **Test: 2005 to 2009** (which holds the broken deals of 2008) **and 2018 to 2022,** each
  cell that goes forward run once. Pass: 0.5% or more after costs, weekly t of 2.5, four
  years of five positive, in both.
- **Check: 2023 to 13 October,** once. **Holdout: from 2023-11-09, sealed,** untouched by
  this family.
- A pass is then judged as a second sleeve beside the earnings book (dollars a year, worst
  year, drawdown of the two together), which is a separate plan to write then.

## Known before starting

Nothing measured here. From what is generally reported: the gap is usually 1% to 4% and has
narrowed over the years; deals fail perhaps one time in fifteen and the target then falls
20% to 40%; the losses cluster in market crises.

**Results, 2026-11-17 15:59 ET.** In REPORT.md. No cell meets the search bar, so no test was
run. Tender offers held to 60 sessions: 1.05% a trade after costs (weekly t 1.70), 7.6% a
year on the money while deployed, worst trade −35%. Pinned mergers: 0.3% to 0.9% a trade,
1.9% to 4.3% a year, worst trade −96%. 10 trials. Closed.
