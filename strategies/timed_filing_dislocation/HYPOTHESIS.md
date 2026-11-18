# Relative dislocation with an as-of-time filing exclusion

Registered before any empirical run. An abrupt stock-specific
decline may be temporary selling pressure or a repricing after
issuer information. The prior relative-dislocation rule earned
a substantial development mean but failed the required stressed
daily Sharpe. Its date-level filing screen could not see today's
filings. The new timed input allows that information exclusion
to be evaluated at the actual decision minute.

The sole change below excludes a stock whose original 8-K with
typed items was already usable when its first baseline event
occurred. A filing can be routine, and a stock without an observed
filing can still have important news. This does not establish
that the remaining shocks are uninformed.

## Family and known evidence

Use `intraday_rebound`, currently 110 counted or declared looks
including nine earlier declared looks. The original brief's 48
trials have been exceeded by later work. This is an adaptive
variant of my existing relative-dislocation and date-filing
rules, not a fresh independent family.

The date-filtered study is saved as
`20261118T011256Z_gpt_filing_aware_dislocation_2df4fa72`.
Its portfolio `20261118T011522Z_gpt_filing_aware_dislocation_bb58abd6`
failed the stressed daily Sharpe gate. The owner-requested
later-period result of the original relative-dislocation rule
and its weak 2022–2023 block remain known. No subsequent frozen
test can make those years globally pristine.

The new timed earnings/after-hours candidate failed development
and is parked. Its rule is not tuned here. This candidate uses
the timing data to remove known-information events from an
existing regular-session rebound.

The documentation-sample exposure recorded in
`docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`
predates registration. No sample value is used. All sealed
holdout restrictions remain.

## Exactly one variant

Retain the prior date-filtered rule's signal, universe, benchmark,
entry and exit:

- Listed domestic common stocks, including later delistings while
  eligible, prior split-adjusted close >= $2, prior median daily
  dollar turnover >= $10 million, at least 20 matched prior
  sessions, positive prior market cap below $10 billion.
- Separate size peers below $2 billion from those in
  [$2 billion, $10 billion). Use synchronous medians of observed
  regular-session 15-minute and one-minute close returns.
  Each median needs 31 valid peer returns. As before, include
  the candidate and every otherwise eligible peer in that
  reference, even if a peer has a filing. Do not fill missing
  price endpoints.
- Declare `form8k: {sessions: 1}` and preserve the date-level
  exclusion: a matching company/symbol report with nonempty
  typed items and filed strictly before the session removes
  that candidate for the day.
- From 09:50 through 14:45 ET inclusive, find the first base
  event per stock. Require its exact 15-minute return at least
  12 percentage points below its peer median; its close at
  least 1% above the preceding clock-minute close; its one-minute
  return at least one percentage point above its peer median;
  and $40,000 decision-bar turnover (close times volume).
- **New exclusion only:** declare
  `form8k_timed: {sessions: 1}`, using existing input
  `adba6fd432` / `form8k-timed-1`. At that first base
  event minute t, exclude the stock if a matching symbol and
  permaticker original 8-K has nonempty accession and typed
  items, was accepted on this New York date, and has
  usable_minute <= t. The native one-complete-minute delay
  defines usability. Do not inspect later filings or merge
  later items into earlier accessions. A rejection cannot be
  rescued by a later price event. Keep the rejected stock
  in peer benchmark calculations.
- Buy at market on the next clock minute only, expiring at
  its end. Hold 120 clock minutes after first fill, then sell
  at market with the ordinary closing-auction fallback.
  $20,000 equity/buying power, $2,000 target per position,
  ten reservations, 5% bar participation,
  `ibkr_pro_tiered`. Intraday only; no stops or targets.

No new input build, platform change, news-text model, parameter
sweep or alternate variant. The current-session filter must be
applied at the base event minute, never by end-of-day filing status.

## Exact comparison and development selection

1. Run one `development --study`, 2003-09-10 through 2016-12-30,
   judging only r_120. Before interpretation, verify it is an
   exact subset of the saved date-filtered study: common
   company/dates must have identical signal, entry, shares,
   prices, fees, slippage and r_120. If matching fails, report
   the discrepancy and do not advance.
2. Require at least 150 events on 90 dates overall and 40 events
   in 2013–2016; gross mean >= +3% and positive stressed
   mean net in both blocks; strictly positive full-period
   95% day-clustered gross lower bound. Additionally require
   stressed mean net strictly above the saved baseline in
   BOTH blocks. No removed events or an empty comparison
   fails the improvement criterion. Apply all gates to full
   and next-clock-minute samples if the legacy study admits
   later entries. Park after any miss. Report retained and
   removed diagnostics; no baseline rerun is registered.
3. Only after all study gates pass and a committed develop
   verdict, run the primary development portfolio once.
   Require 150 trades on 90 dates overall, 40 trades in
   2013–2016, mean net >= +2.5% at base and > +1% at doubled
   slippage in both blocks, full stressed annualised daily
   Sharpe > 1 and worst stressed end-of-day drawdown loss
   < $10,000.
4. Only after every portfolio gate passes, run frozen
   `validation` once, 2017-01-03 through 2023-11-08.
   Require mean net over ALL completed trades >= +3% at base
   and >= +1% at doubled slippage overall AND separately for
   2022-01-03 through 2023-11-08; 150 trades on 90 dates
   overall, 50 on 30 dates recently; positive base mean in
   2017–2021; full stressed daily Sharpe > 1 and stressed
   drawdown loss < $10,000. No retry or tuning.

At most three new empirical runs. Every run counts. Report
run IDs, inputs, trade counts, annual means and dollar P&L,
daily P&L t-statistics, drawdowns, winner/loser means,
capacity violations, on-time checks and subset matching.

## Limits

The timed archive excludes ambiguous identities, conflicting
accessions and unsupported item formats. Its observed archive
envelope is not complete issuer coverage. SEC acceptance can
follow an earlier press release, and the assumed one-minute
delay is not measured retrieval latency. Absence of a qualifying
record is not absence of news.

The normal event study ignores expiry, capital conflicts and
participation, uses the horizon close rather than the timed
portfolio exit open, and estimates both cost legs from the
entry bar. Quote spreads and depth remain unobserved. The
panel's static category, identity and market-cap assumptions
remain. This rule needs no passive or capped after-hours fill.
