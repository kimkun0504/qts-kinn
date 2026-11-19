# Recovery above a volume-weighted bar-high reference

Registered before any run. After an abrupt decline, much trading at
lower prices can accompany a transfer of supply. A recovery above a
volume-weighted reference may indicate that the active recent price
distribution has moved below the current price. Buyers can still be
uninformed, supply can return, and the lower price may be justified.
Neither signed flow nor investor inventory is observed.

Use a deliberately conservative bar reference, not estimated true VWAP:
weight each completed preceding minute's HIGH by its reported share
volume. This is at least the corresponding close-volume proxy when
bars are consistent. Actual VWAP would lie below that reference only
if the included trades and reported volumes all conform to each OHLC
range; sale-condition aggregation can violate that assumption. No such
guarantee, executable price or participant cost basis is claimed.

## Family, prior looks and adaptive choice

Use `intraday_rebound`, carrying 114 counted/declared trials including
nine pre-registry looks, versus 48 at the beginning of this program.
Size-peer reversals, quiet price-baseline, ten-point shock, session-VWAP
cross, volume/momentum and turnover-stabilization work are known.
The air-pocket collapse primary produced no events; its positive control
was ineligible and had insufficient later development observations.
This is not that control relabeled for validation. The failed bid-size
experiment is also known and its observation rules remain unchanged.

The eight-point shock below is an adaptive choice after the earlier
six-point candidate pool and twelve-point reversal studies. It aims at
an earlier, less rare dislocation while testing a distinct volume-price
reference. It is not independently selected or one of a hidden threshold
grid. Eight points and the reference are frozen here; their outcome is
unknown at registration. Repeated search remains a material limitation.
Earlier definitions have examined 2017–2023; it is not globally pristine.
The documentation-sample exposure is recorded in
docs/checkpoints/gpt-2026-11-18-documentation-exposure.md. No sample value
is used. Nothing dated on/after 2023-11-09 is permitted.

## Shared frozen first price event

- Listed domestic common stocks, including later delistings while eligible.
  At least 20 matched prior sessions, prior adjusted close >= $2, prior
  median daily dollar turnover >= $10 million, positive prior cap < $10
  billion. Group references by prior cap below or at/above $2 billion.
  These are pre-open selections only.
- For each completed regular bar t, compute the same group's median exact
  15-minute and one-minute close returns, M15 and M1. Each needs 31 valid
  observed returns, including the candidate when available. Missing price
  endpoints remain missing. Keep all pre-open eligible peers regardless
  of their bar-history availability or the primary reference condition.
- From 09:50 through 14:45 ET inclusive, inside the exchange session,
  take the FIRST price event per symbol: 15-minute return minus M15 <=
  −0.08; C_t >= 1.01 C_(t−1); one-minute return minus M1 >= 0.01; and
  C_t V_t >= $40,000. The first event is final before history/reference
  checks. Failed availability or reference checks cannot move to a later
  price event.
- Both variants require all sixteen actual consecutive bars t−15..t.
  Each must have finite positive OHLC, high >= max(open, close), low <=
  min(open, close), high >= low, and positive integer share volume.
  No missing minute/price/volume is imputed. Transaction counts are not
  used. The anchor t−15 is available but excluded from the reference.

## Primary and ineligible control

Define U_t = sum(H_i V_i) / sum(V_i), for fourteen preceding bars
i=t−14..t−1. Exclude the recovery/decision bar t from numerator and
denominator. This uses only completed historical bars when t closes.

Primary `development`: at the shared first price event, additionally
require **C_t >= U_t**. Implement as C_t sum(V_i) >= sum(H_i V_i),
allowing one adjacent representable float at inclusive comparisons.
No threshold margin, second cross confirmation, size/count, news,
filing, prior trend or additional turnover-growth filter is registered.

Control `development_control`: the identical event and availability
contract without C_t >= U_t. Both studies run once, even if the primary
fails. Only the primary is eligible to advance. This isolates selection
at identical decision times; the control cannot be substituted for it.

## Execution and costs

Buy at market at t+1 only; expire at that minute's end. Start a market
exit 120 clock minutes after first fill, with normal closing-auction
fallback and same-day flattening. No stop or target. $20,000 account
and buying power, $2,000 target, ten slots/reservations, 5% participation,
`ibkr_pro_tiered`. Stress doubles slippage on the same trades with fees
fixed. The study measures r_120 (capped at the close) and ignores expiry,
capital and participation. The separate portfolio must test those
constraints. Study exit closes and portfolio exit opens can differ.

## Exact run sequence and qualification gates

1. Run primary then control studies on 2003-09-10..2016-12-30; evaluate
   r_120 only. Before interpreting returns, verify primary is an exact
   control subset on company/date, signal/entry minute, shares, price,
   fees, slippage and r_120. Require 150 primary events on 90 dates
   overall and 40 events in 2013–2016; gross mean >= +3% and stressed
   mean net > 0 in both windows; full 95% day-clustered gross lower bound
   > 0; and primary stressed mean STRICTLY above control in both windows.
   Empty comparisons fail. If either study admits late entries, apply
   every sample/return/comparison gate also to next-clock-minute samples.
   Park after any miss. No alternate horizon or control may advance.
2. Only after a committed develop verdict, run primary development
   portfolio once. Require 150 completed trades on 90 dates overall,
   40 trades in 2013–2016; base mean net >= +2.5% and stressed mean
   > +1% in both windows; full stressed annualized daily Sharpe > 1;
   worst stressed end-of-day drawdown loss < $10,000.
3. Only after every development gate passes, run frozen primary validation
   ONCE on 2017-01-03..2023-11-08. Require mean net across ALL completed
   trades >= +3% base and >= +1% stressed overall AND separately in
   2022-01-03..2023-11-08; 150 trades on 90 dates overall; 50 on 30 dates
   recently; positive base mean in 2017–2021; full stressed annualized
   daily Sharpe > 1 and stressed drawdown loss < $10,000. No tuning or
   second validation attempt.

At most four empirical runs: two studies, a qualifying development
portfolio and one qualifying validation. Count every run in the family.
Report both costs, event/trade and date counts, yearly results, daily
P&L t-statistics, drawdowns, conditional winner/loser means, exact-subset
checks, late entries and orders above entry-bar participation. Standard
bootstrap diagnostics use saved run-store rows and the native fixed seed.

## Limits

The reference is a bar statistic, not actual inventory, VWAP, bid support
or signed buying. High prints can be outliers and can make it too strict.
Reported volumes and OHLC may differ in trade-condition eligibility.
Complete observed histories select a population that excludes other
illiquid or halted stocks. The size-group median is an imperfect common
shock adjustment. Current-vintage category, capitalization and corporate
action caveats remain. Market opens, auction proceeds, full depth and
latency are unverified. No scratch empirical results, new platform edit,
raw write/download, rebuild or sealed access is proposed.
