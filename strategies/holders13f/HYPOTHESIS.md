# Holders: small companies that institutions are starting to own

Written 2026-11-17 22:31 ET, before anything is measured. The one rule that works here trades slow belief
in small companies. Another sign of it is in the quarterly 13F reports: when the number of
institutions holding a small company jumps, the stock is being discovered, and discovery is
usually not finished in one quarter (funds that bought small want more; others follow).
Nothing here has used the 13F data (Sharadar SF3A, the number of 13F filers holding each
stock each quarter).

## Data and timing

SF3A starts at 30 June 2013. Rows dated after 30 June 2023 are not read (the 30 September
2023 reports were due after the seal); they were left out when the table was copied into the
research folder. 13F reports are due 45 days after the quarter; Sharadar's counts can include
late filers, so the signal is used only from the **first session on or after the quarter's
end + 60 days** (S).

## Rule

For each quarter Q from 30 September 2013: a stock's holders (13F filers holding its shares)
at Q against Q's previous quarter. Two scores: the change in holders, and the change as a
share of the previous count (previous count at least 3). At S, in a size group (market value
at the session before S, $50M to $300M or $300M to $2B; $250,000 a day; a price of $1 or
more; listed common stock, matched by ticker): the **20 highest scores**, bought at S's open,
held 20 or 60 sessions (sold at the close). Costs: the auction allowance and commission, as
the earnings rule. Each trade is also measured against every stock of its size group bought
at the same open and held as long.

## Cells

2 scores × 2 sizes × 2 holds = **8**, family `holders13f`.

## What counts (set now; the periods differ from the usual ones because the data starts in 2013)

Search: the signals of 2013 to 2017 (17 quarters). Over the average stock of the size group,
**1% a trade for 20 sessions, 2% for 60**, a t of 3 over the quarters, four years of five
positive, and a positive average after costs. Test: 2018 to 2022 (20 quarters), each cell
that goes forward run once: **half those**, t of 2.5, four years of five. The first two
quarters of 2023 are a check. There is no second test period, so a pass here is a lead.
