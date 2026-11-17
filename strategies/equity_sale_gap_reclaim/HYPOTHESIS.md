# Equity sale gap reclaim

Registered before any run. Selling unregistered equity can dilute
existing holders and can also ease a company's financing pressure.
A steep opening decline after the filing followed by a partial
recovery on active trading may indicate that the opening sale
overshot. The stock could resume falling if the dilution or other
bad news warrants the discount. The filing code does not reveal
the terms, amount or use of proceeds. Some transactions deliver
equity in exchange for services or other noncash consideration.
[SEC Form 8-K and the rule adopting Item 3.02](https://www.sec.gov/rules-regulations/2004/03/additional-form-8-k-disclosure-requirements-acceleration-filing-date)

This is one variant in `intraday_rebound`. The family carried 48
trials at the start of this research and 94 at the close of the
heavy-turnover stabilization study. Related research includes the
unconditional opening gap reclaim, Claude's broad news-item and
gap cells, and the typed earnings-gap continuation. The rationale
for this rule depends on the capital structure event and the
price path after the gap.

## Frozen definition

- Use listed domestic common stocks including subsequent
  delistings while eligible. Require at least 20 matched prior
  sessions, prior split-adjusted close of at least $2, prior
  20-session median daily dollar turnover of at least $1 million
  and prior market cap from $50 million inclusive to $2 billion
  exclusive.
- Declare one session of versioned `form8k`. Require a matching
  symbol and company identifier and at least one Item 3.02
  filing dated on or after the item's effective date (2004-08-23)
  and strictly before the entry session. Exclude a symbol if an
  available report matched on the same identifiers and dates also
  carries Item 2.02 earnings. This removes overlapping labeled
  earnings disclosures in the visible filing set. The signal uses
  no filing dated that session. The filing marks availability
  under Kinn's convention. The underlying news can be older.
- Require the 09:30 regular-session bar with an opening price
  between 65% and 90% of the prior close, inclusive. At 09:59,
  require actual 09:58 and 09:59 bar closes. Each must have
  recovered from 25% through 60% of the dollar difference between
  the prior close and opening price, inclusive. This requires
  persistence and leaves a gap for further recovery. Turnover
  summed across completed bars from 09:30 through 09:59 must
  reach 15% of the prior full-day median. Use close times volume
  to estimate turnover. The 09:59 bar must have at least $40,000
  turnover. Exclude premarket prints.
- Enter at market only at 10:00, with any remaining order
  expiring at the end of that minute. Sell in the same session's
  closing auction using Kinn's standard fallback. Use $20,000
  equity and buying power, $2,000 target per order, at most ten
  positions or reservations, 5% bar participation and
  `ibkr_pro_tiered`.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30 and
   judge `r_close` only. Require at least 150 events on 90 dates
   with at least 40 events in 2013–2016. Require gross mean of at
   least +3% and positive net mean at 2× in both date windows.
   Require a strictly positive full-period 95% day-clustered
   lower gross bound. Apply the same gates to entries on the
   next clock minute if the study admits later entries.
   Park after any miss.
2. After a committed develop verdict, run the `development`
   portfolio once on the same dates, using the frozen signal.
   Require at least 150 trades on 90 dates and at least 40 trades
   in 2013–2016. Require mean net per trade of at least +2.5%
   at 1× and above +1% at 2× both overall and in 2013–2016.
   Require 2× full-period annualised daily Sharpe above 1 and
   2× worst end-of-day drawdown below $10,000.
3. If qualified, run frozen `validation` once from 2017-01-03
   through 2023-11-08. Require mean net across all completed trades
   of at least +3% at base costs and +1% at 2× both overall and
   separately from 2022-01-03 through 2023-11-08. Require at least
   150 trades on 90 dates overall and at least 50 trades on 30 in
   the recent block, positive 1× mean in 2017–2021, full-period
   2× daily annualised Sharpe above 1, and 2× worst end-of-day
   drawdown below $10,000.

Count every run. Report the input version, date concentration,
counts, risk and annual results at both costs. Report the mean
winners and losers for portfolio results. The research cannot
attribute the opening move to the filing from contemporaneous
data alone. An issuer may have other news or corporate actions,
and the study approximates market order costs from the entry bar.
The sealed holdout stays excluded.
