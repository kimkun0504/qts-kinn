# Form 4 opening confirmation

Registered before any run. When a public Form 4 discloses a material
purchase in a smaller company, buyers may continue to incorporate that
information during the first session when Kinn can use it. A positive opening
rotation on unusual turnover is evidence of an immediate price reaction.
That reaction can exhaust demand or reflect unrelated information.
The rule tests the first session's continuation, using only public filings.

Count this one rule in the `intraday_form4_followthrough` family. The prior
`insider_buying` swing research motivated the purchase floor and the size
screen. Disclose that related search. The earlier Kinn intraday filing rule
used untyped 8-K counts. Neither prior test measures this intraday rule.

## Frozen definition

- Start with Kinn's domestic common-stock universe, including subsequently
  delisted securities while eligible, at least 20 matched prior sessions,
  prior split-adjusted close at least $2, 20-session prior median dollar
  turnover at least $1 million and prior market cap from $50 million
  inclusive to $2 billion exclusive. Use only the pre-open panel.
- Declare one session of the versioned `form4` input. Use original Form 4
  disclosures with a filing date before the session and transaction code P,
  acquired direction A, and positive finite purchase amount. Ignore
  amendments, awards, exercises and sales. Sum unique accession amounts by
  symbol. Require at least $100,000 disclosed. Skip a symbol if its qualifying
  accession rows have different or missing issuer identifiers, or a repeated
  accession has a conflicting amount. SEC code P includes private
  purchases. The current input has no footnotes to distinguish every case.
  Use filing date rather than transaction date for availability.
- Require the 09:30 regular-session bar and actual closes in the bars
  labelled 09:43 and 09:44 ET. Both closes must be at least 2% above the
  09:30 open. Completed regular-session turnover through the 09:44 bar must
  be at least 10% of the stock's prior full-day median, approximated by
  close times volume. Require $40,000 turnover in the decision bar, derived
  from the target order and 5% participation. Exclude premarket prints.
- Buy at market at 09:45 only, with order expiry at the end of that
  clock minute. Exit in the same session's closing auction using the
  normal forced-exit fallback. Use $20,000 equity and buying power,
  $2,000 target per order, ten reservations, 5% bar participation and
  `ibkr_pro_tiered`. All positions open and close on the same day.

## Run sequence and gates

1. Run `development --study` on 2003-09-10 through 2016-12-30 and
   judge `r_close` only. The Form 4 archive begins in 2006; prior dates
   have no eligible signal. Require at least 150 measured events on
   90 dates and 40 events in 2013–2016. Require +3% or greater mean
   gross and positive mean net at 2× in both development blocks, with
   a strictly positive full-period lower 95% day-clustered gross bound.
   Reapply all gates to on-time entries if the study admits late prints.
   Park after any miss.
2. After a committed develop verdict, run `development` once as a
   portfolio on the same dates. Require 150 trades on 90 dates and
   40 trades in 2013–2016, mean net at least +2.5% at 1× and above
   +1% at 2× overall and in 2013–2016, daily annualised Sharpe above
   1 at 2× and worst stressed end-of-day drawdown below $10,000.
3. Only if qualified, run `validation` once and unchanged from
   2017-01-03 through 2023-11-08 with verified Form 4 coverage through
   the eligible filing dates. Require +3% mean net across all completed
   trades at 1× and +1% at 2× overall and from 2022-01-03
   through 2023-11-08. Require at least 150 trades on 90 dates overall,
   50 trades over 30 dates in the recent block, positive 1× mean in
   2017–2021, full-period daily Sharpe above 1 at 2× and worst stressed
   end-of-day drawdown below $10,000. Keep the intended date range
   intact if the data extension is pending.

Report both costs, counts, yearly results, daily P&L t-statistics and
drawdown. In a portfolio report conditional winners and losers separately.
Record the Form 4 input version. The daily risk series includes sessions
without trades. The input currently matches filing ticker to session
ticker. Recent ticker changes or reuse and a mixed public/private purchase
can affect selection. The archive contains dates rather than first receipt
time. Study prices are hypothetical and fill depth is unverified. The
sealed holdout stays excluded.
