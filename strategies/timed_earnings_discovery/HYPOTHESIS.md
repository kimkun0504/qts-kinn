# Timed after-hours earnings discovery

Registered before any empirical run. A material earnings repricing
can begin after the regular close, when there are fewer competing
orders. An early advance distributed across several active minutes
might continue while more participants process the release.
The competing explanation is an immediate overshoot followed by
profit taking. Neither hypothesis is established.

The signal uses an earnings 8-K's SEC acceptance timestamp.
That establishes public-by timing for the filing. A press release
may have appeared earlier; this is not a test of the first
publication of the earnings announcement or of analyst surprise.

## Prior research and family

Use `intraday_momentum`, currently 175 declared or counted
looks: 174 prior looks recorded by the existing premarket rule,
plus its counted study. Date-level earnings continuation,
premarket price discovery, Claude's news-hours research and
the failed count-based candidates are known. The new question
is the first complete after-hours minutes following a typed,
timestamped earnings filing, with same-evening liquidation.
This is adaptive research, not a new independent family.

The documented documentation-sample exposure predates this
registration. No sample value enters the rule. Earlier rules
already examined 2017–2023; that period is not globally pristine.
No sealed-holdout data will be loaded.

## Input dependency and authorization boundary

The strategy declares
`inputs = {"form8k_timed": {"sessions": 1}}`.
This input is not implemented yet. Its proposed contract is in
`docs/requests/2026-11-18-timed-8k-input.md`.
For this timed input, one session means filings accepted during
the current New York session date, exposed only at their
usable minute. It differs from date-only form8k's prior-day rule.

No empirical run is permitted until the owner authorizes the
scoped platform adapter and a new derived-input build from the
existing raw files. No existing bar/panel build is rebuilt, and
nothing is downloaded or written to raw. Do not load an
undeclared second data stream inside strategy code.

## One frozen definition

- Listed domestic common stocks, including later delistings
  while eligible, with 20 matched prior sessions, prior
  split-adjusted close >= $3, prior median daily dollar
  turnover >= $2 million and prior market capitalisation in
  [$50 million, $2 billion). Pre-open selection only.
- Use normal sessions closing at 16:00. For each symbol, select
  the earliest original 8-K accepted from 16:00:00 inclusive
  through 17:00:00 exclusive, on that session's New York date,
  with item 2.02, an earnings flag, matching symbol/permaticker
  and nonempty accession. Amendments and other forms do not
  qualify. Do not merge later filing items into earlier filings.
  Once selected, a later filing cannot rescue a failed price event.
- Let m be the acceptance minute in New York. The timestamp must
  be timezone-aware; missing or ambiguous timing is ineligible.
  The input becomes usable at completed-bar label m+1, a
  conservative full-minute delay. Require actual finite positive
  closes and positive integer volume at m-1 and all three
  complete post-acceptance bars m+1, m+2, m+3. Ignore the
  within-acceptance bar m. Never interpolate absent minutes.
- Let P be close at m-1 and C close at m+3. Require
  1.05 P <= C <= 1.15 P. Sum close times volume across the
  three post bars; require >= max($100,000, 5% of prior median
  daily dollar turnover), >= $10,000 in each, and >= $40,000
  in the decision bar m+3. No positive outcome is assumed
  at this observation price.
- Signal at t=m+3. Send a capped buy for the next clock minute
  only, limit floor(C * 1.01 / $0.01) * $0.01, expiring at the
  end of that minute. Hold 30 clock minutes from first fill.
  Use the authorized extended_v1 opening-price proxy, 2×
  regular marketable slippage as the after-hours base case;
  its stress doubles slippage again. The liquidation cap is
  2% below the last observed completed positive-volume close
  preceding each attempted sell bar; retry through 19:59
  if necessary. No stop, profit target or alternative exit.
- $20,000 equity/buying power, $2,000 per target, ten reservations,
  5% per-bar participation, `ibkr_pro_tiered`, same-calendar-day
  positions. Any unliquidated residual invalidates flatness.
  The capped profile tests feasibility at both costs on the
  same inferred opening fills. Report its selection assumption.

## Frozen sequence and bars

1. Run one `development --study`, 2003-09-10 through 2016-12-30,
   judging only its actual 30-minute execution horizon. Require
   zero unresolved positions, at least 150 completed events
   on 90 dates overall and 40 events in 2013–2016. Require
   gross mean >= +3% and positive stressed mean net in both
   blocks, strictly positive full-period day-clustered 95%
   gross lower bound, and no regular-session exit. Park after
   any miss. Count and report all unfilled orders.
2. Only after all gates pass and a committed develop verdict,
   run the development portfolio once on the same dates.
   Require zero unresolved exposure; 150 completed trades on
   90 dates and 40 trades in 2013–2016; mean net >= +2.5%
   at base and > +1% at stressed costs in both blocks;
   full stressed annualised daily Sharpe > 1 and worst
   stressed end-of-day drawdown loss < $10,000.
3. Only if every portfolio gate passes, run the frozen validation
   once, 2017-01-03 through 2023-11-08. Require zero unresolved
   exposure; mean net over ALL completed trades >= +3% at base
   and >= +1% at stress overall AND separately for
   2022-01-03 through 2023-11-08; 150 trades on 90 dates
   overall, 50 on 30 dates recently; positive base mean in
   2017–2021; full stressed daily Sharpe > 1 and worst
   stressed drawdown loss < $10,000. No tuning or retry.

At most three runs. There is one variant and no alternate input
definition eligible for selection. Report run IDs, pinned input
id/version/coverage, counts and fill rate, unresolved exposure,
annual means and P&L, daily t-statistics, worst drawdown,
winner/loser means and exact base/stress assumptions.

## Material limitations

SEC acceptance may follow the press release, a revised item list
is not permitted to leak backward, and a bulk metadata archive
can have historical coverage or timestamp errors. CIK mapping
must establish the disclosing issuer and match the point-in-time
universe; stake filings with ambiguous subject/filer roles are
excluded from the input scope.

There are no historical quotes, halt flags, observed depth or
execution latency records here. After-hours spreads can be much
wider than the fallback. Execution-bar range and volume affect
the capped model's acceptance of an opening fill; a future
range or volume can change that inferred fill. This is a
selection assumption, not just uncertain costs. Prefix replay
can test signal availability, not certify those fills.
A numerical pass remains provisional pending quote/trade checks.

## Implementation addendum before the first empirical run

On 2026-11-18 the owner explicitly authorized the scoped native
input and separate derived-input build. The native type, view
prefix, input pinning and runner/CLI adapter were implemented.
The derived schema also retains issuer CIK for provenance.
Synthetic tests now exercise the actual native DayView rather
than the proposed fixture's prefix implementation. No event,
threshold, order, exit, selection gate or period changes.
