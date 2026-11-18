# Net-nets: small companies priced under their current assets less all liabilities

Written 2026-11-17 22:59 ET, before anything is measured. What has held up here is slow belief in small
companies. Graham's oldest rule is about the most neglected of them: a company whose market
value is under its current assets less **all** its liabilities is priced as if its business
were worth less than nothing. Such companies are small, unloved and too thin for funds, which
is where an account of $20,000 has room. Nothing in this repository has used the balance sheet
this way.

## Data

Sharadar SF1 quarterly reports (ARQ): current assets and total liabilities, with the date the
report was filed (datekey), copied from the raw table for reports filed before 2023-11-09. The
company's location from the ticker table, as it stands now.

## Events

A quarterly report, filed from 2005 to 13 October 2023, of a listed common stock with net
current assets (current assets less total liabilities) above zero. **S** is the first session
on or after the filing date. On S: market value (the panel's, at the session before) of
**$30M or more** and, as a share of net current assets, **under 1** (a net-net) or **under
0.67** (Graham's two thirds); $250,000 a day; a close of $1 or more. One event a company in
250 sessions.

## Trade

Bought at the open after S, held **120 or 250 sessions** (sold at the close). A stock that
stops trading during the hold is sold at its last close (so failures are not dropped). Costs:
the auction allowance and commission, as the earnings rule. Each trade is measured against
every stock of $30M to $300M bought at the same open and held as long, measured the same way.

## Cells

2 thresholds × 2 holds × 2 sets (every company; **companies located in China or Hong Kong
left out**, decided now because the net-nets of 2010–2012 included many reverse-merger
companies whose balance sheets proved false) = **8 cells**, family `net_net`.

## What counts

Search 2010–2017: against the average stock, **4% a trade for 120 sessions and 8% for 250**, a
weekly t (of that) of 3, six years of eight, positive after costs. Tests on 2005–2009 and
2018–2022, each cell that goes forward run once: half those, t of 2.5, four years of five, in
both. 2023 is a check (its holds run into the sealed period and are cut at 2023-11-08). The
holdout stays sealed.

**Results, 2026-11-17 23:02 ET.** In REPORT.md. **None of the 8 cells meets the bar.** 1,962 events before
the one-a-year rule (832 of them companies located in China or Hong Kong). In 2010–2017 the
means against the average small stock range from −2% to +22% but the **medians are −6% to
−23%** and every t is under 1.1: a few net-nets multiply and most trail. 8 trials. No tests
run.
