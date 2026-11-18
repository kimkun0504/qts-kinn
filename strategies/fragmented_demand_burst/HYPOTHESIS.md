# Fragmented demand burst in low estimated share-count stocks

Registered before any empirical run. A sharp increase in the
number of transactions while average shares per transaction
decreases may reflect demand spreading across more orders.
When the price has risen only modestly, subsequent demand
might still move a stock with a small share supply. The
alternative is churn, order splitting or attention that has
already peaked. Aggregate counts have no buy/sell sign,
investor identity or parent-order information.

Prior market capitalisation divided by prior split-adjusted
price supplies an estimated outstanding-share proxy. It does
not measure free float, available inventory or borrow. The
selection is a conjecture about price sensitivity, not an
observed supply constraint. No claim of a new mathematical law
or proprietary market mechanism is made.

## Family and prior looks

Charge both declared studies to `big_prints`, currently 52
looks (49 earlier declared looks and three counted run-store
trials). The failed earnings/trade-size and narrow-range
large-print candidates are known. The smaller-print selloff
study in `intraday_rebound` is related, although its direction
and shock definition differ. The broader momentum family
already has 175 looks. This rule is adaptive follow-up
research; it is not a clean new family.

The documentation-sample exposure in
`docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`
predates registration. No sample value is used. Other rules
have already examined 2017–2023, so a new frozen evaluation
does not make that period globally pristine.

## One base event and two development variants

- Listed domestic common stocks, including later delistings
  while eligible. Require 20 matched prior sessions, prior
  split-adjusted close >= $3, prior median daily dollar
  turnover >= $2 million, and prior market capitalisation
  in [$50 million, $300 million). Require
  marketcap_prev / prev_close <= 20 million estimated shares.
  Membership and this final pre-open screen use only prior
  panel fields. Missing or nonpositive values are ineligible.
- Only normal 09:30–16:00 sessions. At 09:49 ET, require all
  eleven actual consecutive bars 09:39–09:49, with positive
  finite closes, positive integer share volume and observed
  positive integer transaction counts. No minute or missing
  count is filled or inferred.
- Let V_1 and N_1 be summed share volume and transaction count
  in 09:40–09:44; V_2 and N_2 are the sums in 09:45–09:49.
  Require N_1 >= 100 and N_2 >= 4 N_1. Require proxy dollar
  turnover in the second window (sum of close times volume)
  >= 10% of prior median daily dollar turnover and at least
  $40,000 proxy turnover in the completed 09:49 bar.
- The 09:49 close must be from 2% through 5% above the 09:44
  close, inclusive. This measures a modest advance during the
  count burst and does not assume execution at that close.
- **Control:** every base event above.
- **Primary:** the identical base event only if
  V_2 / N_2 <= 0.5 V_1 / N_1, evaluated by exact integer
  cross-products, 2 V_2 N_1 <= V_1 N_2. This isolates the
  smaller-print condition. Common stock-dates must have
  identical signal, entry, costs, shares and measured return
  in the two studies. The control cannot replace the primary.
- Send one market order per eligible symbol at 09:50 only,
  expiring at that minute's end. Hold for 60 clock minutes
  from first fill, then sell at market with the engine's
  normal closing fallback. No stop, target, re-entry or
  alternative threshold, time or exit is registered.
- $20,000 equity and buying power, $2,000 target per position,
  ten reservations, 5% per-bar participation and
  `ibkr_pro_tiered`. All positions open and close the same day.

## Exact sequence and gates

1. Run primary `development --study`, then
   `development_control --study`, on 2003-09-10 through
   2016-12-30. Judge only r_60. The primary needs at least
   150 events on 90 dates overall and 40 events in 2013–2016,
   mean gross >= +3% and positive net at doubled slippage
   both overall and in 2013–2016, and a strictly positive
   full-period 95% day-clustered lower gross bound.
   Primary stressed mean must exceed control stressed mean
   in both blocks; an empty comparison fails. Apply every
   gate to full and next-clock-minute samples if the legacy
   study allows later entries. Park after any miss.
2. Only after all gates pass and a committed develop verdict,
   run the primary `development` portfolio once. Require
   150 completed trades on 90 dates overall, 40 trades in
   2013–2016, mean net >= +2.5% at base and > +1% at
   doubled slippage in both blocks, full stressed annualised
   daily Sharpe > 1 and stressed worst end-of-day drawdown
   loss < $10,000.
3. Only if every portfolio gate passes, run one frozen primary
   `validation`, 2017-01-03 through 2023-11-08. Require
   mean net across all completed trades >= +3% at base and
   >= +1% at doubled slippage overall AND separately in
   2022-01-03 through 2023-11-08. Require 150 trades on
   90 dates overall, 50 on 30 dates recently, positive base
   mean in 2017–2021, full stressed daily Sharpe > 1 and
   stressed drawdown loss < $10,000. No retry or tuning.

At most four empirical runs. Both studies count even if the
primary fails. Report run IDs, counts, annual returns and
dollar P&L, daily P&L t-statistics, worst end-of-day drawdown,
mean winners and losers, capacity violations, on-time
sensitivity and primary/control identity checks at both costs.

## Limits

The normal study ignores capital conflicts, entry expiry and
per-bar participation, uses a horizon close rather than the
portfolio's timed exit open, and prices both cost legs from
the entry bar. A pass cannot establish actual executable depth.
Costs are stated fallbacks without quotes. The same inferred
fills underpin both slippage cases.

Share count is a rough proxy derived from an assumed historical
market-cap field. It does not establish a small tradable float.
Sale-condition eligibility, automated splitting and odd-lot
reporting can affect aggregate counts and size ratios. No
same-day news absence, investor type, signed flow, short squeeze
or true VWAP is inferred. The latest category and company
identity weaknesses of the panel remain. No raw writes,
downloads, rebuild, new platform input or sealed-holdout access.
