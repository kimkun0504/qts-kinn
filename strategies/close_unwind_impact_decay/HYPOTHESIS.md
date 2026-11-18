# Closing unwind and impact decay

Registered before any empirical run. The owner observed a sharp
drop near the close in a stock that had previously rallied and
asked for earlier entries, shorter exits and after-hours research
at a small position size. The observation is a source of a
hypothesis. Today's example is in the sealed period and its
market data is excluded from this research.

The proposed mechanism is temporary pressure from traders reducing
exposure around the close. A declining price impact per dollar
of activity, with activity still present, could indicate that
the pressure is being absorbed. The data cannot identify the
seller, signed order flow or whether the preceding rally was
caused by favorable news. This is a newly specified rule for
this program. Its distinct formula provides no evidence about
its expected return or how widely others use similar rules.

Count this as a variant in `intraday_rebound`, which began this
research with 48 trials and currently has 105 including nine
earlier declared looks. The earlier heavy-turnover stabilization
and late rally selloff are related looks. Both stopped in
development. The new signal uses the change in estimated price
impact across two short windows after the close.

## Frozen signal

- Use listed domestic common stocks including later delistings
  while eligible. Require at least 20 matched prior sessions,
  split-adjusted prior close at least $2, prior 20-session median
  dollar turnover at least $2 million and prior capitalisation
  from $50 million inclusive to $2 billion exclusive.
- Use normal calendar sessions with a 16:00 ET regular close.
  Require an actual positive 15:59 close C at least 10% above
  the split-adjusted prior close, and at least one valid
  regular-session minute close at least 20% above the prior
  close. This identifies an earlier rally through observed
  prices, without inferring news quality.
- At minute t from 16:07 through 17:00 ET inclusive, require all
  seven actual, positive-price, positive-volume completed bars
  from t−6 through t. The first endpoint is therefore after the
  16:00 bar. Exclude that boundary bar from the impact windows.
  Let P_i and V_i be each observed close and share volume.
- Define Q_old as the sum of P_i × V_i in the three bars
  t−5 through t−3 that close below the preceding minute.
  Define Q_new analogously for t−2 through t.
  This is turnover in down-closing bars, not signed sales.
  Require both Q values positive and Q_new at least half Q_old.
- Define I_old = log(P_(t−6) / P_(t−3)) / Q_old.
  Require P_(t−3) at least 3% below P_(t−6), ensuring I_old
  is positive. Define I_new =
  max(0, log(P_(t−3) / P_t)) / Q_new.
  The remaining discount is D = max(0, 1 − P_t / C).
- The score is S = D × max(0, 1 − I_new / I_old).
  Require D at least 0.08 and S at least 0.04. Require P_t
  at least $0.01 above P_(t−1), and at least $20,000 turnover
  in bar t. The partial recovery is one tick, allowing an
  earlier entry than a multi-bar confirmation above VWAP.
  Take the first qualifying signal per symbol.

## Entry and early exit

Use $20,000 equity and buying power, $2,000 target per order,
ten positions or reservations and 5% share participation.

The entry is an aggressive buy limit with cap P_t × 1.005,
live only during t+1. Charge marketable commissions, fees,
spread and impact. Model a fill only if the next observed
minute's opening execution price, including modeled slippage,
is within the cap. Do not use a later intrabar low to invent
a marketable opening fill. Partial fills obey the share cap.

Begin liquidation 15 clock minutes after first fill. The first
sell limit is 2% below the most recent completed close and
expires at the end of the next clock minute. Retry each
subsequent minute from its most recent completed close until
filled or extended-session close. Only observed executable
prices can fill the order. Record unresolved shares explicitly.
Passing requires every position to close on its entry date.
A regular-session auction price cannot settle an after-hours
position. This order policy needs engine support before testing.
[IBKR extended-hours order types](https://www.interactivebrokers.com/support/faq/content/did-market-stop-order-u-35803691)

Use `ibkr_pro_tiered`. For the initial extended-hours cost
profile, double its regular-session spread-and-impact estimate
at both entry and exit. The 2× slippage stress doubles that
extended-hours baseline again, with fees unchanged. This is a
preregistered fallback estimate pending executable quote checks.

## Research sequence and gates

There is one signal and one holding policy. The implementation
request is in `docs/requests/2026-11-17-extended-hours-execution.md`.
No empirical run starts until the owner-assigned platform
implementation can express this policy through `kinn run`.
A timestamped adjustment to the execution contract, if needed,
must be committed before the first run. Existing bars include
extended hours and require no rebuild.

1. Run `development --study` on 2003-09-10 through 2016-12-30
   using r_15 only. Require 150 events on 90 dates and 40 in
   2013–2016. Require mean gross at least +3% and positive
   mean net at 2× both overall and in 2013–2016, with a
   strictly positive full-period lower 95% day-clustered gross
   bound. Apply all gates to the subset with entries within
   the registered lifetime as well. Park after any miss.
2. After a committed develop verdict, run the same definition
   once as a development portfolio. Require 150 trades on
   90 dates and 40 in 2013–2016, mean net at least +2.5%
   at 1× and above +1% at 2× in both windows, full-period
   2× daily annualised Sharpe above 1 and worst 2× end-of-day
   drawdown below $10,000. Any unresolved overnight exposure
   fails the same-day holding requirement.
3. If qualified, run validation once on 2017-01-03 through
   2023-11-08 with identical parameters. Require +3% mean
   net across all completed trades at 1× and +1% at 2×
   overall and separately from 2022-01-03 through 2023-11-08.
   Require 150 trades on 90 dates overall, 50 on 30 dates
   in the recent block, positive 1× mean in 2017–2021,
   full-period stressed daily annualised Sharpe above 1,
   worst stressed drawdown below $10,000 and no positions
   carried overnight.

Count every run. Report both costs, counts, yearly results,
daily P&L t-statistics, drawdowns, mean winners and mean losers.
Extended-hours bars can contain sparse or isolated prints.
Small size reduces participation demands while spread, depth,
latency and adverse selection still affect attainable returns.
The sealed holdout stays excluded.
