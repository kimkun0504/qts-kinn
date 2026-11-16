# Market recovery lag

Registered 2026-11-16. Large, liquid stocks can reflect common information
earlier than smaller stocks. Test whether a smaller stock still near its
low after a broad selloff recovers once the large-cap basket turns. The
smaller stock may have its own lasting impairment, and early recovery
among large caps may fail to transfer. Prior lead-lag research motivates
the order of events. It gives no evidence for this intraday definition,
cost model or target.
[Lo and MacKinlay, When Are Contrarian Profits Due to Stock Market Overreaction?](https://www.nber.org/papers/w2977)

The earlier relative-dislocation strategy subtracts a simultaneous broad
return from a stock shock. This rule requires the market's own down-then-up
sequence before the stock may qualify. Charge the one fixed variant to
`intraday_rebound` because it buys a recovery after a decline. Keep all
related trials in the record.

## Frozen definition

- Use listed domestic common stocks including later delistings while
  eligible, at least 20 matched prior sessions, prior split-adjusted
  price at least $3 and prior 20-session median daily dollar turnover
  at least $2 million. Tradable names have positive prior cap below
  $2 billion. Reference names have prior cap at least $10 billion and
  prior dollar turnover at least $20 million. All selections are known
  before the open.
- At a decision minute `t`, use the same set of reference names with
  valid observed closes at `t−45`, `t−15` and `t`. Require at least 30.
  The median first-window close-to-close return must be −1.50% or less
  and the median second-window close-to-close return must be +0.75% or
  more. The first leg measures the broad selloff and the second its
  partial recovery. All endpoints are completed regular-session bars.
- A candidate must have an observed close at those same endpoints
  and at `t−1`. It must fall at least 8% in the first window. By `t`
  it must have recovered between zero and one quarter of its absolute
  price decline from `t−45` to `t−15`, inclusive. The last one-minute
  close-to-close return must be at least +1%. Require at least $40,000
  of turnover in the decision bar. This allows stock-specific variation
  without requiring that the stock and basket have the same beta.
  Take the first qualifying bar from 10:15 to 14:45 ET, at least 75
  clock minutes before the calendar close.
- Buy at market on the next clock minute only, expiring at the end of
  that bar. Hold for 60 clock minutes from first fill and then sell at
  market, with Kinn's existing auction fallback and same-day exit.
  Use $20,000 equity and buying power, $2,000 target per order, no
  more than ten reservations, 5% volume participation, and
  `ibkr_pro_tiered`.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30.
   Judge `r_60` only. Require at least 150 events on 90 dates and
   40 events in 2013–2016. Require mean gross at least +3% and
   positive mean at 2× overall and in 2013–2016, and a strictly
   positive full-sample lower 95% day-clustered gross bound. Apply
   the same gates to entries within expiry if the study admits
   late entries. Park after any miss.
2. After committing a develop verdict, run the `development`
   portfolio on the same dates. Require 150 trades on 90 dates
   and 40 trades in 2013–2016. Require 1× net mean at least +2.5%
   and 2× net mean above +1% in both development blocks, stressed
   annualised daily Sharpe above 1 and worst stressed end-of-day
   drawdown below $10,000.
3. Only if qualified, run `validation` once on 2017-01-03 through
   2023-11-08. Require +3% mean net across all closed trades at 1×
   and +1% at 2×, both overall and in 2022 through 2023-11-08.
   Require 150 trades on 90 dates overall and 50 trades on 30
   dates in the recent block, positive 1× net mean in 2017–2021,
   stressed full-period annualised daily Sharpe above 1, and worst
   stressed end-of-day drawdown below $10,000.

Report years, trade or event counts, t-statistics and drawdowns at both
costs. Show winner and loser means separately for a portfolio. Market
stress can concentrate events on a few dates and expose multiple holdings
to the same move. Bar quotes, trade priority and halts remain unverified.
The holdout beginning 2023-11-09 stays sealed.
