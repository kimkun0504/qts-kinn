# Intraday reversal in companies reporting operating profit and cash generation

Registered before any empirical run or financial-cohort return query.
The hypothesis is that a stock with recently reported positive operating
income and operating cash generation is more likely to recover from an
abrupt relative decline than one without those characteristics. The
information can be stale and a new adverse event can warrant repricing.
This tests a public stock selector, not fair value, signed demand,
an earnings beat or an assertion that the company is currently sound.

## Prior research and family

Use `intraday_rebound`, carrying 118 counted/declared trials including
nine pre-registry looks; the initial brief already carried 48. Size-peer,
volume, count, quote, price-history and filing-related reversals are
known. A recent disclosed-purchase selector improved descriptive means
but failed sample and gross-return bars. Its controls and favorable
subgroups cannot replace it. This selector uses broader accounting
information rather than another restrictive price transform or a rare
new filing event. The fields and zero thresholds are frozen here.

This is adaptive research in an extensively searched family, not a new
independent discovery. Prior definitions have examined 2017–2023; those
years are not globally pristine. The documentation-sample exposure is
recorded in docs/checkpoints/gpt-2026-11-18-documentation-exposure.md;
no sample value is used. No date on/after 2023-11-09 is allowed.

## Coherent public-data contract, required before either study

Both variants declare `inputs = {"fundamentals_art": {"sessions": 1}}`.
One session means the current session's pre-open snapshot. Source is
the existing build's Sharadar SF1 **ART** as-reported trailing-year
rows, using only `opinc` and `ncfo`; no restated MR dimension, analyst
estimate, price ratio or current data is used. No rebuild or download.

For each company on session D, use rows filed strictly before D
(`datekey` becomes `filed` in the typed view). Select the latest filing
date first, then the latest reportperiod within that filing date,
before checking the values. At those selected keys identical paired
values may collapse; conflicting values are unavailable. A missing
reportperiod at the latest filing date is unavailable. Never revive
an older row or independently forward-fill one field to repair an
invalid/missing/conflicting latest pair. A later old-period amendment
can conservatively make this snapshot stale; no synthetic current
TTM accounting is constructed.

Proposed immutable value:
`FundamentalSnapshot(symbol, permaticker, dimension, filed,
reportperiod, opinc, ncfo, status)` in `view.fundamentals[symbol]`.
Native view must represent missing/conflicting/invalid observations
explicitly and match the current traded symbol by company identity.
Unknown identity or absent adapter/parent entry is an error rather
than an inferred negative financial label.

Both variants require an available ART pair, finite opinc/ncfo,
reportperiod <= filed < D and reportperiod age from zero through
**180 calendar days** inclusive. This is a fixed data-freshness gate,
not a return-selected lookback. Negative or zero values are still
available for the control. Fields must come from one selected row.
The record is known before the open and remains identical under
intraday prefix replay. Version, source build/content and availability
semantics must be pinned in manifests, hashes, resume and workers.
Requested dates and source rows pass the seal, with no unseal path.

The required native snapshot does not exist yet. Strategy-private
data loading and use of daily per-field carried values are prohibited.
Platform implementation requires a new scoped owner authorization.
Contract tests do not establish native availability or source coverage.

## Primary and ineligible availability control

Primary `development`: require **opinc > 0 AND ncfo > 0** in that
coherent fresh snapshot. Zero thresholds are economic signs, not a
searched profitability margin. Using signs avoids mixing numerical
amounts across currency conventions. Do not compute a ratio to market
cap, a cross-currency comparison, growth or an earnings surprise.

Control `development_control`: require the same coherent/fresh
available pair but omit the two positive-sign conditions. Both share
the price event, universe, input and execution. The comparison is
conditional on observed valid fresh financials and does not establish
representativeness of companies without them. Only the primary can
advance; the control is never a substitute. Both studies run once,
even if primary fails.

## Shared universe and first price event

- Domestic common stocks, including later delistings while eligible;
  20 matched prior sessions, prior adjusted close >= $2, prior median
  daily dollar turnover >= $10 million, positive prior cap < $10
  billion. Group peers at prior cap $2 billion. Selection is pre-open.
- Keep every such peer in its group regardless of financial availability
  or profitability. At completed regular bar t, each median exact
  15-minute and one-minute close return requires 31 valid observed
  endpoints, including the candidate when available. No stale or missing
  endpoint is filled.
- From 09:50 through 14:45 ET inclusive, inside the exchange session,
  take the FIRST price event per stock: its 15-minute return minus
  the group median <= −0.08; C_t >= 1.01 C_(t−1); its one-minute
  return minus the group median >= 0.01; C_t V_t >= $40,000. All
  used prices are positive finite actual closes. Inclusive floating
  comparisons allow one adjacent representable value without changing
  economic thresholds. The eight-point definition is known adaptive
  history and is not independently selected again.
- Apply snapshot availability/freshness and the primary sign condition
  only at that first price event. Failure cannot move entry to a later
  event. No extra news, filing-event, trend, count, VWAP or price-history
  condition is registered.

## Execution

Market entry at t+1 only, expiry at that minute's end. Begin a market
exit 120 clock minutes after first fill, with normal same-day auction
fallback. No stop or target. $20,000 account/buying power, $2,000 target,
ten slots/reservations, 5% participation, `ibkr_pro_tiered`. Stress
doubles slippage while holding fees fixed. The regular study measures
r_120 capped at the close, ignores expiry/participation/capital and
uses entry conditions for both cost legs. Portfolio exit opens and
execution constraints must be tested separately before validation.

## Frozen sequence and qualification gates

1. After approved native support and its tests, run primary then control
   studies on 2003-09-10..2016-12-30. Judge r_120 only. Before interpreting
   returns, verify primary is an exact control subset on company/date,
   signal/entry minute, shares, price, fees, slippage and r_120. Require
   150 primary events on 90 dates overall, 40 in 2013–2016; gross mean
   >= +3% and stressed mean net > 0 in both windows; full 95%
   day-clustered gross lower bound > 0; stressed primary mean STRICTLY
   above control in both windows. Empty comparisons fail. If any study
   entry is late, apply every sample/return/comparison gate also to
   next-clock-minute samples. Park on any miss. No alternate control,
   accounting field, sign margin, freshness window or horizon can advance.
2. Only after every study gate passes and a committed develop verdict,
   run primary development portfolio once. Require 150 completed trades
   on 90 dates overall, 40 in 2013–2016; base mean net >= +2.5% and
   stressed mean > +1% in both windows; full stressed annualized daily
   Sharpe > 1 and stressed worst end-of-day drawdown loss < $10,000.
3. Only after all development gates pass, run primary validation ONCE,
   2017-01-03..2023-11-08. Require base mean net >= +3% and stressed
   mean >= +1% across ALL completed trades overall AND separately in
   2022-01-03..2023-11-08; 150 trades on 90 dates overall, 50 on 30
   dates recently; positive base mean in 2017–2021; full stressed daily
   annualized Sharpe > 1 and stressed drawdown loss < $10,000. No tuning
   or second attempt. Missing required source coverage must fail clearly.

At most four empirical runs: two studies, a qualifying development
portfolio, one qualifying validation. Count every run in the family.
Report run/input ids and source semantics, counts/dates, both costs,
annual results, daily P&L t-statistics, drawdowns, winner/loser means,
matching, late entries and above-participation target orders. Use
registered run-store rows for fixed-seed diagnostic calculations.

## Limits

As-reported vintage and filing-date mapping rely on vendor/build
semantics; this is not a consensus or first-release database. Operating
cash flow can be temporarily positive because of working capital or
other transient effects. Financial businesses can have different
accounting economics. No sector or additional quality filter is added.
Latest ART selection can exclude stale/missing reporters and creates
a conditional population. Cohort eligibility must never change the
price-reference peers. Snapshot cap/category, corporate-action and
company-mapping limitations persist. Minute opens/auctions, spreads,
depth and latency are unverified. A new information source and a
one-attempt validation do not erase the extensive prior search.

No platform edit is authorized by this hypothesis itself. No raw write,
download, bar/panel rebuild, sealed access or scratch performance is
proposed. The existing daily fundamental interface must retain its
current behavior.
