# Busy day: a jump on results released on a day crowded with other results

Written 2026-11-17 23:56 ET, before anything is measured. Investors' attention is limited. On days when
very many companies report, each report gets less of it: the first reaction is smaller and
more of the move comes later (Hirshleifer, Lim and Teoh, 2009). The earnings drift that has
worked here is in companies under $300M; in companies of $300M to $2B it faded after 2017.
This asks whether it survives in those mid-sized companies on the crowded days, where the
first reaction should be most incomplete. The count of other reports is an indicator of our
own, read from the SEC's filing times.

## Events

Results 8-Ks (item 2.02) accepted before 2023-11-09, by a filer Sharadar maps to a stock;
the reaction session D is the first session whose close comes after the acceptance. The stock
must be common stock, $300M to $2B in market value, $1M a day or more, $2 or more, and close
5% or more above the previous close on D. 2005 to 13 October 2023.

**Crowding:** the number of results 8-Ks (any filer) whose reaction session is D. A day is
**busy** if that count is at or above the 80th percentile of the previous 250 sessions' counts,
**quiet** if at or below the 40th.

## Trade

Bought at the open of D+1, held 20 or 60 sessions. Costs: the auction allowance and
commission. Measured against the average common stock of $300M to $2B with $1M a day, bought
at the same open and held as long.

## Cells

day (busy, quiet) × hold (20, 60) = **4**, family `busy_day`. The quiet cells are the
comparison; only the busy cells can pass.

## What counts

Search 2010–2017: 150 trades, 1% a trade over the average for 20 sessions or 2% for 60,
weekly t of 3, six years of eight, positive after costs. Tests on 2005–2009 and 2018–2022 at
half those, t of 2.5, four years of five. 2023 is a check. The holdout stays sealed.
