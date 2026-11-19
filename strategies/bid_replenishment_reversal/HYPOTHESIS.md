# Bid replenishment after an early relative selloff

Registered before the price-control run, data-window selection,
or any inspection of quotes for this experiment. The hypothesis
is that rebuilding displayed bid support after an abrupt
stock-specific decline identifies a more reversible imbalance.
Displayed liquidity can instead be fleeting, cancelled or
uninformative. This tests a particular observable pattern;
it does not identify an institution or a true parent order.

## Prior work and family

Use `intraday_rebound`, with 111 counted or declared looks
including nine earlier declared looks at registration.
My size-peer price reversal had a strong development mean and
failed its portfolio Sharpe gate; its later-period recent block
was weak. Both filing exclusions failed to improve it. Claude
already tested a nonnegative 60-session trend filter, which
failed validation, so that search is not repeated.

This experiment adds pre-decision best-quote dynamics. It uses
a broader six-percentage-point price trigger to observe bid
support earlier, instead of waiting for the old twelve-point
shock. The price trigger only defines the candidate population;
the unfiltered control cannot replace the primary. Six points
is fixed here without a threshold or time sweep.

This is an adaptive follow-up in the existing family, not a
fresh independent search. Other definitions have examined
2017–2023 and those years are not globally pristine. The
documented documentation-sample exposure predates registration;
no sample value is used. The sealed holdout remains excluded.

## Shared price candidate, computed identically in both variants

- Listed domestic common stocks, including later delistings
  while eligible. Prior split-adjusted close >= $2, prior
  median daily dollar turnover >= $10 million, 20 matched
  prior sessions and positive prior market cap below $10 billion.
- Split the pre-open cohort at $2 billion. Each group's
  synchronous median 15-minute and one-minute close returns
  requires 31 observed member returns. Include the candidate
  and all otherwise eligible peers, irrespective of quote
  availability or quote conditions. No filled price endpoints.
- At t from 09:50 through 14:45 ET inclusive, take the first
  completed event per stock: exact 15-minute return at least
  SIX percentage points below its size group's median;
  at least 1% absolute close recovery over the preceding
  clock minute; at least one percentage point above the
  simultaneous group one-minute median; and at least $40,000
  decision-bar turnover (close times volume).
- No news, prior-trend, sector, nominal-price-reclaim or
  additional volume filter. The first price event is final:
  an unavailable or failed quote test cannot move the order
  to a later price event.

## Frozen quote rule, primary only

Let T be the end of completed price bar t, in UTC nanoseconds.
At targets T−5 seconds and T−1 nanosecond, choose the latest
SIP-timestamped quote at or before the target. Each must be
no more than one second old at its target. Do not skip an
invalid latest observation to resurrect an earlier quote.
Conflicting records with the same latest timestamp are
unavailable unless identical on the feature fields.

Both snapshots need finite positive bid and ask, ask strictly
above bid, and finite positive integer bid/ask sizes. Use
displayed size in the vendor's same units on both sides;
no round-lot-to-share or available-capacity claim is made.

Write (B0,A0) for early bid/ask sizes, (B1,A1) for late sizes.
The primary qualifies only with ALL of:

- B0 <= A0;
- B1 >= 3 A1 (late bid share at least three quarters);
- B1 >= 2 B0;
- late bid price >= early bid price;
- late full spread / late midpoint <= 0.005 (50 basis points).

Use exact integer comparisons for the size rules. A change in
quote size can reflect order withdrawal or changing venues,
not demand or signed buying. No quote after T is a feature.

## Execution, fixed for both variants

Market order at the next clock minute only, expiry at that
minute's end; 120-clock-minute hold after first fill, then
market exit with the ordinary closing-auction fallback.
$20,000 equity/buying power, $2,000 target, ten reservations,
5% bar participation and `ibkr_pro_tiered`. Intraday only.
No stop, target or alternate exit.

The primary declares
`inputs = {"nbbo_replenishment": {"sessions": 1}}`.
The control declares no quote input. The native input/view
does not yet exist and requires a separate owner-approved
adapter. No private raw-data loader may enter strategy code.

## Two definitions and exact research sequence

1. Run `development_control --study` on 2003-09-10 through
   2016-12-30, judging r_120 only. This is a counted price-only
   control and candidate-data definition, not an eligible alpha.
   If it has fewer than 150 events on 90 dates or fewer than
   40 events in 2013–2016, park: the primary cannot meet its
   sample gates. Parent returns do not select a quote rule.
2. Before reading any quote prices, write the immutable
   acquisition plan for EVERY control event, using only its
   day, company, symbol, signal minute and pre-open metadata.
   No sampling by returns, fills or existing-file availability.
   Request the window [T−10s,T+2s) for each candidate.
   The two seconds after T permit a future registered entry
   audit; they are not exposed as decision features. Existing
   raw files may be reused only with recorded provenance and
   time-window coverage. Downloads/raw writes remain owner-only.
3. After scoped authorization and data acquisition, build one
   versioned snapshot input, then run primary
   `development --study` once on the same dates. Require
   valid pre-decision snapshot pairs for at least 95% of parent
   events overall and separately in 2013–2016. Missing/stale,
   invalid, empty and conflicting observations stay explicit.
   Missing files/unknown source coverage fail, not silently
   become a negative quote label.
4. Before interpreting returns, verify primary is an exact
   subset of the control on company/date, signal and entry
   minute, shares, entry price, costs and r_120.
   Require 150 primary events on 90 dates overall, 40 in
   2013–2016, gross mean >= +3% and positive stressed mean
   net in both blocks, positive full-period 95% day-clustered
   gross lower bound, AND primary stressed mean strictly
   above control in both blocks. An empty comparison fails.
   Apply all return/sample/comparison gates to full and
   next-clock-minute samples if the study admits late entries.
   Park after any miss. Do not substitute the control.
5. Only after all gates pass and a committed develop verdict,
   run the primary development portfolio once. Require 150
   completed trades on 90 dates, 40 in 2013–2016; mean net
   >= +2.5% at base and > +1% at doubled slippage in both
   blocks; full stressed annualised daily Sharpe > 1 and
   stressed worst end-of-day drawdown loss < $10,000.
6. Only after every portfolio gate passes, acquire validation
   quotes for the identical frozen rule. Candidate planning
   may enumerate price triggers without computing forward
   returns/P&L; it is data acquisition, not a second strategy
   performance test. No validation data is requested now.
   Run primary validation ONCE, 2017-01-03 through 2023-11-08.
   Require net mean across ALL completed trades >= +3% at
   base and >= +1% at doubled slippage overall AND separately
   for 2022-01-03 through 2023-11-08; 150 trades on 90 dates
   overall, 50 on 30 dates recently; positive base mean in
   2017–2021; full stressed Sharpe > 1 and stressed drawdown
   loss < $10,000. The input coverage gate also applies.
   No tuning, changed quote rule or second validation attempt.

At most four empirical runs: control study, primary study,
primary development portfolio, primary validation. Count all.
Report run ids, input ids/coverage, primary/control matching,
both costs, counts, annual returns and dollar P&L, daily
t-statistics, worst drawdown, mean winners/losers, late entries
and target orders exceeding actual entry-bar participation.

## Limits

Best quotes are public, transient and not the full order book.
SIP time is not measured client arrival time; a one-second
freshness rule does not establish actual execution latency.
The size ratios do not certify share units, firm executable
depth, a participant identity, an investor's intent or fills.

The normal bar study retains its modeled next-open execution,
entry-condition cost approximation for both legs, ignored
order expiry/capital conflicts/participation, and horizon-close
versus portfolio exit-open difference. The quote signal does
not repair those assumptions. A numerical pass remains a
bar-model candidate requiring execution checks.

Current-vintage category/identity and market-cap limitations
remain. A partial historical quote archive can bias the
observable population; report missingness and the control
returns of unavailable observations without changing the rule.
No raw write, download, sealed access or bar/panel rebuild by
GPT is allowed. The prior trend filter and earlier exits are
not additional variants in this registration.
