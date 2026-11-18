# Distributed premarket price discovery

Registered before any empirical run of this rule. The owner
asked for earlier signals, short exits, small positions and
extended-hours research. The closing-unwind rule was too sparse
in development and is parked. This candidate studies upward
price discovery before the regular opening, as a separate
momentum hypothesis. It does not loosen the parked rule.

A move accompanied by activity across several minutes could
reflect repeated demand while information spreads. A solitary
print or one large-volume minute offers weaker evidence. The
competing explanation is temporary price pressure that reverses
as liquidity returns. Small order size does not remove spread,
adverse selection or depth constraints. Large institutions and
market makers can trade before the regular opening; their
absence is not an assumption of this hypothesis.

The formula below combines price-path efficiency and the
dispersion of turnover in one score. These are known statistical
ideas. This exact specification is new to this program; it
does not establish novelty across the market or profitability.
No contemporaneous news classification is used. The next-day
8-K input cannot establish the content or arrival time of that
morning's news. Timestamped news would require a separately
registered input contract and candidate.

## Family and prior looks

Use the existing `intraday_momentum` family, carrying the 169
prior looks declared in its metadata. Conservatively add four
GPT VWAP studies and one GPT regular-session volume-surge study
already seen in this program, for `prior_trials: 174`; those
runs also remain charged in their original families. Related
opening-gap and filing-momentum studies remain part of the
broader search history. This family charge is not a claim that
all these hypotheses are statistically independent, or a
complete correction for all research selection. No significance
claim may rely on treating this as the first momentum trial.

## One frozen signal

- Listed domestic common stocks, including later delistings
  while eligible. Require at least 20 prior matched sessions,
  split-adjusted prior close at least $2, prior 20-session
  median dollar volume at least $2 million and prior market
  capitalisation in [$50 million, $2 billion).
- Use normal sessions with a 16:00 ET calendar close. Consider
  completed decision bars t from 07:05 through 08:45 ET inclusive.
  Require six actual consecutive bars t−5 through t, with finite
  positive closes and positive volume. No stale close may bridge
  a missing minute in the signal.
- For the five price changes, r_i = log(P_i/P_(i−1)). Let
  R = sum r_i, A = sum |r_i|. Require R > 0. Define efficiency
  E = R/A. Let q_i = P_i V_i for these same five ending bars,
  Q = sum q_i, and breadth B = Q²/(5 sum q_i²).
  B is between 1/5 and 1; it falls when turnover concentrates
  in one minute. The score is S = R × E × B.
- Require S at least log(1.05), the current close at least
  1.15 times prior close, each q_i at least $10,000, and Q at
  least max($100,000, 0.05 × prior median daily dollar volume).
  These liquidity conditions and the score form one candidate,
  with no threshold grid or comparator. Send the first signal
  per symbol only. The current day’s regular-session prices
  never enter the decision.

## Entry and early liquidation

Use the tested platform `extended_v1` execution profile with
$20,000 equity and buying power, $2,000 target, ten simultaneous
positions or reservations and five-percent share participation.
The buy cap is 1.01 times decision-bar close. The order is live
only in the next clock minute. No later bar can rescue expiry.
Size whole shares against the cap.

Begin liquidation 30 clock minutes after the first fill.
An aggressive sell limit lies two percent below the last
observed positive-volume completed close and expires after
the next minute. Retry each minute through the profile's
20:00 boundary. A gap through the limit cannot fill at that
opening; a later intrabar high or low cannot invent an opening
fill. Missing bars do not fill. Record stale references and
delayed completion as limitations; report the share of exits
that reach or follow 09:30. Any unresolved position fails the
same-day requirement. There is no auction fallback.

Use `ibkr_pro_tiered`. The baseline multiplies the regular
marketable spread and impact estimate by two at every fill.
The stress doubles this extended baseline again. Both modeled
execution prices must fit the same cap, and both returns use
the same fills. Each filled replacement is a new commission
order. This bar approximation uses the execution bar's total
volume and range after the decision and cannot establish an
attainable opening fill or available depth. Quotes remain
necessary before making a trading claim.

## Research sequence, selection and failure bars

There is one variant. Parameters cannot change after the study.

1. Run `development --study` on 2003-09-10 through 2016-12-30,
   measuring only the registered thirty-minute exit policy.
   Require at least 150 completed events on 90 dates overall
   and 40 completed events in 2013–2016. Require mean gross
   at least +3% and positive mean net at 2× both overall and
   in 2013–2016, with a strictly positive full-period lower
   95% day-clustered gross confidence bound. All filled events
   must respect entry expiry. There may be no unresolved
   position. Any miss means park with no portfolio or validation.
2. After a committed develop verdict, run the same development
   portfolio once. Require 150 trades on 90 dates overall,
   40 trades in 2013–2016, base mean net at least +2.5% and
   stressed mean net above +1% in both windows. Require full
   stressed annualised daily Sharpe above one and worst stressed
   end-of-day loss from peak below $10,000. No unresolved position.
3. Only if selected, run validation once on 2017-01-03 through
   2023-11-08, with an independently specified 2022-01-03 through
   2023-11-08 recency check. Require +3% mean net at base costs
   and at least +1% at doubled slippage in both full validation
   and recency windows, 150 trades on 90 dates overall and
   50 on 30 dates in the recency window. Require positive base
   mean in 2017–2021, full stressed daily Sharpe above one,
   stressed drawdown below $10,000 and no unresolved position.

Report both costs, event/trade counts, active dates, years,
daily P&L t-statistics, worst drawdown, mean winners and losers,
and late exits. Event studies ignore portfolio capital constraints
and must be identified as such. Count every run; preserve all
results. The sealed period beginning 2023-11-09 is excluded.
