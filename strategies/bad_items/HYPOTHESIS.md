# Bad items: selling short after an 8-K that carries quiet bad news

Written 2026-11-17 23:59 ET, before anything is measured. Some 8-K items are bad news that rarely moves
the price on the day, because reading them takes work: an unregistered sale of shares (item
3.02, often a discounted placement or a convertible being turned into stock), financial
statements that can no longer be relied on (4.02), a debt default or acceleration (2.04), a
notice from the exchange that the company no longer meets a listing rule (3.01), a change of
auditor (4.01), and a material impairment (2.06). Published work finds negative drift after
several of these. The news-hours study grouped all 8-Ks by price reaction; this one takes the
items themselves, whatever the first reaction, and holds for weeks. The trade is a short; the
owner has not decided whether shorts will be traded.

## Events

SEC filing times, 8-Ks accepted before 2023-11-09 with one of the six items, by a filer
Sharadar maps to a stock, the first 8-K with that item by that filer in 90 days. Entry at the
first open after acceptance (that morning's if accepted before 09:30). The stock must be
common stock, $50M to $2B in market value at the last close, $250,000 a day or more, $2 or
more. 2005 to 13 October 2023.

## Trade

Sold short at that open, bought back at the close 20 or 60 sessions later. Costs: the auction
allowance both ways, commission, and borrow at 10% a year for the sessions held. Measured as
the short's return over the average common stock of the same size bought at the same open
(a short hedged with that average).

## Cells

item (3.02, 4.02, 2.04, 3.01, 4.01, 2.06) × size ($50M–$300M, $300M–$2B) × hold (20, 60) =
**24**, family `bad_items`.

## What counts

Search 2010–2017: 150 trades, 1% over the average for 20 sessions or 2% for 60, weekly t of
3, six years of eight, positive after costs and borrow. Tests on 2005–2009 and 2018–2022 at
half those, t of 2.5, four years of five. 2023 is a check. The holdout stays sealed.

## Follow-up: a shelf registration (written 2026-11-18 00:30 ET)

A company that files a shelf registration (form S-3, not an amendment) is preparing to sell
shares; the sale comes later, at a discount. If the market prices the dilution only as it
happens, the stock should trail from the filing. Same trade and costs as above (sold short at
the first open after acceptance, held 20 or 60 sessions, borrow at 10% a year, against the
average stock of its size); the first S-3 by a filer in 365 days. **4 cells:** size × hold. Same
bars. 4 trials.
