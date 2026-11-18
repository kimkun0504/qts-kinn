# Lockup end: the weeks around the day insiders may first sell after an IPO

Written 2026-11-17 22:21 ET, before anything is measured. Tonight's offerings study found that new
supply sold in one night is priced at once. A lockup is the opposite case: the day the
supply may arrive is known six months ahead, and how much will be sold is not. If holders of
the stock step aside before the date and buy back once the selling is seen, there is a dip to
sell short before and a recovery to buy after. The recovery is the side that needs no borrow.

## Events

An **IPO**: a listed common stock (not a blank-check company, SIC 6770; not a spin-off,
whose company filed a form 10-12B; not an ADR) whose first session in the price data is from
2005 on, whose company filed an S-1 in the 365 days before that session. Most IPO lockups end
180 days after pricing. **L** is the first session on or after the first session + 180 days.
Market value $50M or more and $250,000 a day, six sessions before L.

## Trades

- **Short before:** sell short at the close six sessions before L, buy back at the close of
  the session after L (L+1). Borrow 10% a year (new issues are often dearer; said if it goes
  forward).
- **Long after:** buy at the close of L+2 (after the first three sessions in which insiders
  may sell); sell at the close of L+12, or of L+22.

Sizes at L−6: $50M to $300M, $300M to $2B, $2B or more. Costs: the auction allowance and
commission both ways, as the earnings rule.

## Cells

Short 1 × 3 sizes + long 2 holds × 3 sizes = **9 cells**, family `lockup_end`.

## What counts

Search 2010–2017: 150 trades, 1% after costs, weekly t of 3, six years of eight. Tests on
2005–2009 and 2018–2022, each cell that goes forward run once: 0.5%, t of 2.5, four years of
five, in both (2005–2009 has few IPOs; a cell with under 50 trades there is reported as too
few rather than failed). 2023 is a check for a cell that passes. The holdout stays sealed.
Raw filings and the ticker table are read only for dates before 2023-11-09; the ticker table
supplies the SIC code and category, which are taken as they stand now.
