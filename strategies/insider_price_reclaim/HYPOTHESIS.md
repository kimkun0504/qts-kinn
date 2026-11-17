# Insider purchase price reclaim

Registered before any run. A newly disclosed insider purchase provides
an observable price at which someone connected to the company spent
capital. If the stock trades materially below that reference in the
regular session and then reclaims part of the decline, later buyers
may regard the discount as temporary. The purchase can be private,
planned or made on terms unavailable to shareholders. Subsequent
information may also justify the lower price.

This is a rebound variant in `intraday_rebound`. The original brief
identified 48 prior trials. At registration the common store counts
83 family runs plus nine earlier declared looks. The earlier
intraday Form 4 opening-confirmation test and Claude's insider swing
work are related. This rule uses the disclosed dollars per share as
the reference and requires an intraday decline and recovery.

## Frozen definition

- Start with listed domestic common stocks including subsequent
  delistings while eligible. Require at least 20 matched prior
  sessions, a prior split-adjusted close of at least $2, 20-session
  prior median daily turnover of at least $1 million and prior
  capitalisation from $50 million inclusive to $2 billion exclusive.
- Declare one session of `form4`. Use newly available, original Form
  4 purchases with code P, direction A, a filing date strictly before
  the session, and the officer or director flag. Require at least
  $100,000 in a single accession's finite positive purchase amount,
  finite positive shares, and a present accession and issuer CIK.
  Require the session symbol to match the filing symbol. Skip the
  stock if qualifying filings disagree on issuer or a duplicate
  accession has conflicting purchase amounts or shares. Choose the
  largest purchase amount, breaking ties by ascending accession.
  The price reference is that accession's purchase amount divided by
  disclosed shares. Amount can omit unpriced lines included in
  shares, so this is a price proxy. The filing date governs
  availability. Actual transaction age and whether it was a market
  purchase are unknown to this strategy.
- Require the prior close and the observed 09:30 regular-session
  open each to be from 95.5% to 110% of the price reference,
  inclusive. Use completed regular-session bars only. From
  09:35 through 13:00 ET, and at least 15 clock minutes before the
  session close, take the first bar with all these properties.
  An earlier regular-session close was at or below 94% of the
  reference. The immediately preceding clock minute has an actual
  close below 95.5% of the reference. The decision close is from
  95.5% to 97% of the reference, inclusive, on at least $40,000
  turnover approximated by close times volume. This leaves a
  discount to the reference at decision time and the signal
  cannot assume a fill at that price.
- Buy at market on the next clock minute only, expiring at the
  end of that bar. Sell in the same day's closing auction with
  Kinn's normal forced-exit fallback. Use $20,000 equity and
  buying power, $2,000 target per position, at most ten positions
  or reservations, 5% bar participation and `ibkr_pro_tiered`.
  All positions open and close on the same date.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30.
   The archive begins in 2006. Judge `r_close` only. Require at least
   150 events on 90 dates and 40 events in 2013–2016. Require mean
   gross of at least +3%, positive mean net at doubled slippage
   both overall and in 2013–2016, and a strictly positive full-
   sample lower 95% day-clustered bound on gross mean. Reapply all
   gates to entries within expiry if the study admits late prints.
   Park after any miss.
2. After a committed develop verdict, run the `development`
   portfolio once on the same dates. Require at least 150 trades
   on 90 dates and 40 trades in 2013–2016. Require at least +2.5%
   mean net at 1× and above +1% at 2× overall and in 2013–2016,
   full-period daily annualised Sharpe above 1 at 2× and worst
   stressed end-of-day drawdown below $10,000.
3. If qualified, and only with complete pre-holdout Form 4
   coverage, run frozen `validation` once from 2017-01-03 through
   2023-11-08. Require +3% mean net across all completed trades at
   base costs and at least +1% at 2×, overall and separately from
   2022-01-03 through 2023-11-08. Require at least 150 trades on
   90 dates overall and at least 50 trades on 30 dates in the
   recent block, positive 1× mean in 2017–2021, full-period daily
   annualised Sharpe above 1 at 2×, and worst stressed end-of-day
   drawdown below $10,000. The present Form 4 archive stops on
   2023-09-29. Preserve the dates and wait for an owner-supplied
   pre-holdout extension if necessary.

Count each run. Report both cost cases, event or trade counts,
years, daily P&L t-statistics and drawdowns. Report conditional
mean wins and losses separately for portfolio trades. Record the
input version, concentration by issuer and any late-entry
sensitivity. The symbol match cannot rule out reuse or changes,
and the price bands can miss splits and cross-class transactions.
The study's cost approximation and bar-based fills do not confirm
available depth. The sealed holdout stays excluded.
