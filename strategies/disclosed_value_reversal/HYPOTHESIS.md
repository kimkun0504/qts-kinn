# Intraday reversal with a recently disclosed insider purchase

Registered before any run. An officer or director who recently disclosed
a material purchase supplies public information distinct from a price
pattern. Such purchases might identify companies where a later abrupt
stock-specific decline contains temporary pressure. The purchase can be
private, planned, stale or poorly timed; new adverse information may
justify the entire decline. This does not identify informed buying,
an executable insider price or a guaranteed valuation floor.

## Family and known research

Charge every run to `intraday_rebound`, with 116 counted/declared trials
including nine pre-registry looks, versus 48 in the original brief.
Earlier Form 4 opening confirmation used newly available filings and
positive morning momentum. Insider-price reclaim used a newly available
filing's dollars/share proxy and tight price bands. This test instead
uses a fixed trailing disclosure window as a pre-open stock selector,
with no purchase-price reference and no positive opening-price condition.

Size-peer reversals, liquidity/price-history selection, filing exclusions,
volume/count, VWAP and rebound studies are known. The air-pocket and
volume-cost primaries failed; their controls cannot replace them. The
insider swing research is also prior context. This is adaptive follow-up
in an extensively searched family, not a new independent family.
Prior strategies have examined 2017–2023, which is not globally pristine.
The documentation-sample exposure is recorded in
docs/checkpoints/gpt-2026-11-18-documentation-exposure.md; no sample
value is used. No date on/after 2023-11-09 is permitted.

## Input and pre-open universe

- Domestic common stocks including later delistings while eligible;
  20 matched prior sessions, prior adjusted close >= $2, prior median
  daily dollar turnover >= $1 million, prior cap >= $50 million and
  < $2 billion. Membership uses pre-open panel values only.
- Both variants declare `inputs = {"form4": {"sessions": 20}}`.
  The native store supplies filings available over the last twenty
  sessions, strictly before the current date. The window is fixed at
  one trading month; no lookback/amount/role sweep is registered.
- Eligible signals begin 2006-02-01 for BOTH variants, after a complete
  twenty-session window within the available SEC quarterly archive.
  The registered development run still spans 2003-09-10..2016-12-30.
  Earlier sessions deliberately have no eligible signal; unknown
  pre-archive filings are not interpreted as observed absence.

## One pre-open selector and its ineligible control

For each symbol, consider valid disclosed records with the same symbol,
filing date strictly before the session, original document type 4,
transaction code P, acquired direction A, officer OR director flag,
nonempty accession and issuer CIK, finite positive purchase amount and
finite positive shares. Skip invalid records. Deduplicate valid records
by accession; conflicting issuer/amount/shares within an accession make
the symbol ineligible. Valid original purchases with different issuer
CIKs also make it ineligible. A valid record below the dollar threshold
still participates in these conflict checks.

Primary `development`: require at least one such unique accession with
purchase_amount >= **$100,000**. This is the fixed materiality floor
used in earlier insider research, not selected from this experiment.
Do not sum duplicated accessions, use transaction date as availability,
infer a purchase price or use footnotes not present in the input.

Control `development_control`: omit this selector only. It shares the
archive warmup date, price event, universe, costs and input declaration.
All pre-open eligible peers remain in the price reference regardless of
their purchase eligibility. Both studies run even if primary fails.
Only primary can advance; the control is never a replacement alpha.

## Shared fixed intraday price event

At each completed regular-session minute t, calculate the median exact
15-minute and one-minute close returns of this pre-open universe. Each
requires at least 31 valid observed endpoints; include the candidate
when available. Do not fill missing endpoints or remove peers using
their disclosure status.

Between 09:50 and 14:45 ET inclusive, inside the exchange session,
take the FIRST price event per stock: its 15-minute return minus the
reference median <= −0.08; C_t >= 1.01 C_(t−1); its one-minute return
minus the reference one-minute median >= 0.01; and C_t V_t >= $40,000.
All used price endpoints are actual positive finite closes. Inclusive
floating comparisons allow one adjacent representable value without
changing economic thresholds. There is no extra history, count, VWAP,
news, trend, stop or profit-target condition.

The filing selector is known before the open and cannot move a stock
to a later price event. Send one market order per stock from t+1 only;
expire at that minute's end. Start market liquidation 120 clock minutes
after first fill with the ordinary auction fallback. Same-date positions.
$20,000 equity/buying power, $2,000 target, ten slots/reservations,
5% participation and `ibkr_pro_tiered`. Stress doubles slippage only.

## Fixed research sequence and gates

1. Run primary then control development studies, 2003-09-10..2016-12-30;
   judge r_120 only. Before interpreting returns, verify primary is an
   exact control subset on company/date, signal/entry minute, shares,
   price, fees, slippage and r_120. Require 150 primary events on 90
   dates overall, 40 events in 2013–2016; gross mean >= +3% and mean
   stressed net > 0 in both windows; full 95% day-clustered gross lower
   bound > 0; and stressed primary mean STRICTLY above control in both
   windows. Empty comparisons fail. If any study entry is late, apply
   every count/return/comparison gate also to next-clock-minute subsets.
   Park after any miss, without choosing another horizon or control.
2. Only after a committed develop verdict, run primary development
   portfolio once. Require 150 completed trades on 90 dates overall,
   40 trades in 2013–2016; base mean net >= +2.5% and stressed mean
   > +1% in both windows; full stressed annualized daily Sharpe > 1;
   worst stressed end-of-day drawdown loss < $10,000.
3. Only after all development gates and source coverage pass, run
   primary validation ONCE on 2017-01-03..2023-11-08. Require base mean
   net >= +3% and stressed mean >= +1% across ALL completed trades
   overall AND separately in 2022-01-03..2023-11-08; 150 trades on 90
   dates overall, 50 on 30 dates recently; positive base mean in
   2017–2021; full stressed annualized daily Sharpe > 1 and stressed
   drawdown loss < $10,000. No tuning or second validation attempt.

At most four empirical runs: two studies, a qualifying development
portfolio, one qualifying validation. Count all in the family. Report
run/input ids, both costs, counts/dates, yearly results, daily P&L
t-statistics, drawdowns, winner/loser means, exact-subset audit,
late entries and orders above entry-bar participation. Use saved
run-store rows for fixed-seed bootstrap and descriptive diagnostics.

## Source coverage and limits

Current Form 4 input `fe7c80978b` is form4-1, with filings through
2023-09-29. No rebuild/download is proposed. If development qualifies,
the owner must supply a pre-seal extension through 2023-11-08 before
validation. Preserve the validation dates rather than truncate them
or label unknown later coverage as no purchases. No extension is
requested unless the development candidate qualifies.

Date-only availability is conservative about within-day release but
does not measure feed delivery. Form 4 P can include private purchases;
footnotes, amendments and transaction age are not resolved here.
The ticker match cannot eliminate every reuse or rename; conflicting
issuer records fail closed, but this does not certify company identity.
The one-month window may retain stale information. Snapshot cap/category
and corporate-action caveats persist. Minute-bar fills, spreads, depth
and latency are unverified. The study ignores expiry, participation
and capital conflicts, estimates both cost legs from entry conditions,
and marks horizon closes rather than portfolio exit opens. No platform
edit, raw write/download, rebuild, sealed access or scratch performance
is proposed.
