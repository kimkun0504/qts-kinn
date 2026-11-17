# News hours: what a stock does in the hours and days after a company filing becomes public

Written 2026-11-17 15:11 ET, before anything in this family is measured. The owner's
question: "surely there has to be some sort of pattern, especially right after news."

## Why this can be asked now

Until today the only timed news on disk covered 2021 and 2022 from one wire, and its stamps
could not be trusted to the minute. The owner downloaded the SEC's acceptance time for every
8-K (1,680,137 filings, 2003 to 2023-11-08; `tools/owner/download_edgar_times.py`). An 8-K is
how a company reports results, agreements, management changes and other material events,
and the acceptance time is the second it became public on EDGAR. The times are in UTC
(checked on the hour-of-day pattern only: they peak at 20:00 to 21:00, which is 16:00 to
17:00 in New York).

A limit to keep in mind: a press release often comes before the 8-K, by minutes or days, so
the acceptance time is "public by now", not always "public first now". Both ways of reading
the reaction are therefore used (below).

## Events

One event a stock a session. 8-K only (amendments left out), 2005-01-03 to 2023-10-13.
The company is matched to the stock through the SEC number in Sharadar's ticker table.

- **During the session:** accepted from 09:30 to 15:25 New York time on a session day.
- **Before the session:** accepted after 15:25 on the previous session and before 09:25, so
  the first chance to act is the open.

**Kinds, by the 8-K's items:** results (2.02); agreements (1.01, no 2.02); announcements
(7.01 or 8.01, neither of the first two); other.

**Universe:** common stock, market value $50M or more and normal dollar volume $250,000 or
more as of the previous close, last price $1 or more when the trade is made. Sizes: $50M to
$300M, $300M to $2B, $2B and over.

## The reaction, and the trade

- **During the session.** Two readings of the reaction, both known five minutes after the
  filing: (A) the last trade then against the last trade before the filing; (B) the last
  trade then against the previous close. Buy at the open of the next minute bar.
- **Before the session.** One reading at 09:35: the last trade against the previous close.
  Buy at the open of the next minute bar.
- **Five groups by the reaction:** down 5% or more; down 2% to 5%; within 2%; up 2% to 5%;
  up 5% or more. All are bought, so the tables show whether a rise continues, whether a
  fall bounces, and what a stock with news and no move does.
- **Two exits:** the close of the same session; the close five sessions later.

Cells: (2 + 1 readings) × 5 reactions × 4 kinds × 3 sizes × 2 exits = **360**.

**Costs.** Entry: the modelled half spread (1.00%, 0.43%, 0.18%, 0.05% by normal volume) plus
commission. Exit: the closing auction allowance plus commission.

## Periods and what counts

- **Search: 2010 to 2017.** A cell goes forward only with 150 trades or more, a mean of 1% or
  more a trade after costs (the owner's target), a weekly t of 3 or more, and at least 6 of
  the 8 years positive. With 360 cells about one in two searches would throw up a cell at
  that t by chance, so a cell that goes forward is a candidate and nothing more.
- **Test: 2005 to 2009 and 2018 to 2022,** each cell that goes forward run once. Pass: 0.5%
  or more after costs, weekly t of 2.5 or more, 4 of 5 years positive, in both.
- **Check: 2023 to 13 October,** once, for a cell that passes.
- **Holdout: from 2023-11-09, sealed.** This family has not looked at it.

Whatever the cells do, the report gives the plain table the owner asked about: the average
path after news by reaction, kind and size.

## Known before starting

From other families: buying a 15% earnings jump during the session after the report does not
beat waiting for the open after (`swing_search`, family 23); jumps on 8-Ks other than
results do not drift over 15 sessions on daily bars (family 18); a release in 2021–2022
bought one or five minutes after its stamp earned nothing by the close (`recent_search`).
Not seen: any reaction measured from the SEC's acceptance time, any fall after news bought,
anything in companies over $300M within the day.

**Results, 2026-11-17 15:18 ET.** In REPORT.md. No cell meets the search bar, so no test was
run. 360 trials. Detail added when the entries were built and not in the plan above: a
during-session reading against the last trade before the filing needs a trade in the 30
minutes before it; entries need the stock to have traded since 09:30 and a bar within 10
minutes; filings accepted between 09:25 and 09:30 are left out.
