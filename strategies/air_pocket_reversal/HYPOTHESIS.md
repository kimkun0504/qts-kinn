# Transaction-activity collapse during a relative selloff

Registered before any run. A large price decline on unusually few
transactions can reflect temporarily withdrawn liquidity rather than
persistent aggressive trading. A first price recovery may then continue.
The same observation can instead reflect a permanent information shock,
halting or shrinking demand. Aggregate counts do not observe signed flow,
order withdrawal, a participant or executable liquidity. This tests that
specific activity proxy; a formula supplies no evidence of an edge.

## Prior research and family

Charge every run to `intraday_rebound`, with 112 counted/declared trials
at registration, including nine pre-registry looks; the initial brief
already carried 48. Size-peer dislocations had a strong development
mean and failed portfolio risk or recent-period gates. The previously
tested fragmentation rule required sustained/increasing transaction
activity after a decline. This rule tests the opposite activity pattern
during the decline. Active-gap recovery inferred inactivity from missing
bars; this definition requires every minute to have observed trades.
Quiet price-baseline, volume/momentum, trend and deeper passive-limit
tests are also prior research and are not repeated as variants here.

The bid-replenishment experiment was parked because its frozen quote
coverage gates failed. Its observation rules are not relaxed or reused
as a new favorable subset. This new definition uses no quote input.
This is adaptive follow-up, not an independent family or globally fresh
validation. Earlier strategies have seen 2017–2023, and the earlier
documentation-sample exposure is recorded in
docs/checkpoints/gpt-2026-11-18-documentation-exposure.md. No sample value
is used. No date on or after 2023-11-09 is allowed.

## Frozen base event

- Listed domestic common stocks, including later delistings while eligible.
  Require 20 matched prior sessions, prior adjusted close >= $2, prior
  median daily turnover >= $10 million and positive prior cap < $10 billion.
  Split reference groups at $2 billion using pre-open cap. Include the
  candidate and every eligible peer regardless of transaction-history
  availability or the extra primary condition.
- At completed regular bar t, require at least 31 valid simultaneous
  observed returns in the group for both the exact 15-minute and exact
  one-minute close returns. No forward or stale price endpoint is filled.
  Let M15 and M1 be these group medians.
- From 10:00 through 14:45 ET inclusive, take the FIRST price event per
  stock: its 15-minute return minus M15 <= −0.12; close_t >= 1.01 close_(t−1);
  its one-minute return minus M1 >= 0.01; and close_t × volume_t >= $40,000.
  All endpoints are actual bars. The first price event is final even if
  its subsequent history-availability or primary check fails.
- At that event only, require all thirty consecutive actual bars t−29
  through t, with finite positive closes, positive integer share volumes
  and observed positive integer transaction counts. No missing minute,
  count or volume is imputed. Both variants apply this identical data gate.

## One extra condition, one ineligible control

Let N0 be transaction counts summed over fifteen bars t−29 through t−15,
and N1 over fourteen bars t−14 through t−1. The decision/recovery bar is
excluded from both count windows. The baseline precedes the fifteen-minute
price-return interval; the second window observes the decline before its
recovery bar. Their unequal lengths are normalized explicitly.

Primary `development`: require N1/14 <= (N0/15)/2, implemented exactly as
**15 N1 <= 7 N0** with Python integer arithmetic. The factor one half is
fixed as an economically material activity collapse, not searched.
No extra turnover-growth, print-size, VWAP, filing, news or trend condition.

Control `development_control`: the identical base event and data gate,
without the activity-collapse inequality. It is only an ablation, never
an alternate alpha eligible for validation. A rejected first event cannot
be replaced by a later event in either variant. Both development studies
will run once, even if the primary fails. There is no parameter sweep.

## Trading contract

Market entry only at t+1, expire at that minute's end. Start a market exit
120 clock minutes after first fill, retaining the ordinary closing-auction
fallback. Same-date positions, no stop or target. Use $20,000 equity and
buying power, $2,000 target, ten slots/reservations, 5% participation and
`ibkr_pro_tiered`. Doubling slippage keeps fees fixed.

The study ignores expiry/capital/participation and marks r_120 at a close;
the portfolio uses executable simulated orders and exit opens. Report
late entries and orders above entry-bar participation. Apply all study
gates to both full and next-clock-minute samples if any entries are late.
These are bar proxies and do not certify opening, auction or live fills.

## Fixed sequence, selection and validation bars

1. Run primary then control studies, 2003-09-10..2016-12-30; judge r_120
   only. Verify the primary is an exact control subset on company/date,
   signal/entry minute, shares, entry price, fees, slippage and r_120 before
   interpreting returns. Require 150 primary events on 90 dates overall,
   40 in 2013–2016, gross mean >= +3% and stressed net mean > 0 in both
   windows, full day-clustered 95% gross lower bound > 0, and primary
   stressed mean STRICTLY above control in both windows. Empty comparisons
   fail. Apply all sample/return/comparison gates to both full and on-time
   samples if the study contains late entries. Park on any miss.
2. Only after all study gates pass and a committed develop verdict, run
   primary development portfolio once. Require 150 completed trades on
   90 dates overall and 40 in 2013–2016; base mean net >= +2.5% and
   stressed mean > +1% in both windows; full stressed annualized daily
   Sharpe > 1 and worst stressed end-of-day drawdown loss < $10,000.
3. Only if all development gates pass, run primary validation ONCE,
   2017-01-03..2023-11-08. Require base mean net >= +3% and stressed
   mean >= +1% across ALL completed trades both overall and separately
   in 2022-01-03..2023-11-08; 150 trades on 90 dates overall, 50 on
   30 dates recently; positive base mean in 2017–2021; stressed daily
   annualized Sharpe > 1 and stressed drawdown loss < $10,000. No tuning
   or second validation attempt.

At most four empirical runs: two development studies, one qualifying
development portfolio, one qualifying validation. Count all in the family.
Report run ids, both costs, counts, annual results, daily P&L t-statistics,
worst drawdown and mean winners/losers. Standard bootstrap uses the saved
run-store rows and fixed seed; no scratch empirical output is evidence.

## Limits

An endogenous transaction slowdown need not identify temporary pressure.
Trade reporting conditions and order splitting affect counts; neither
volume/count nor transaction rate is investor identity. The prior-window
activity can itself be abnormal. Requiring complete observed history can
exclude halted or illiquid names and changes the population. The reference
median is an imperfect common-shock adjustment. Market-cap/category and
corporate-action snapshot caveats persist. No inferred news absence,
analyst surprise, full depth or measured latency is available. No platform
edit, raw write, download, rebuild or sealed access is proposed.
