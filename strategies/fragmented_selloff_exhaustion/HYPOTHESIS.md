# Smaller-print selloff exhaustion

Registered before any empirical run. A decline can continue
because information has changed or because a seller still
needs to trade. The candidate asks whether a change toward
smaller prints, while transaction activity persists and price
impact weakens, identifies temporary pressure that is ending.
It does not observe signed order flow, parent orders or trader
identity. Algorithms splitting orders and changes in trade
conditions can produce the same pattern without exhaustion.

The proxy combines an observed price drop, diminishing adverse
movement per transaction and fragmentation of average print
size. The owner-authorized count field makes the last component
available to a strategy with prefix replay. Its mathematical
definition supplies no evidence of profitability by itself.

## Family and prior looks

Use `intraday_rebound`, carrying 107 counted or declared looks
at registration, including nine earlier declared looks. It
began this program with 48 trials. The failed heavy-turnover
stabilization and closing-unwind impact-decay candidates are
directly related prior looks. Earlier price-only rebounds,
relative-dislocation variants and their recency failures are
known. This is a new count-based follow-up, not a fresh
independent family or untouched search.

The two-event earnings/trade-size study is also known. Its
larger-print continuation rule is parked and is not loosened
here. Claude's `big_prints` work and the other volume/momentum
studies remain broader search history. Previous strategies have
already been evaluated on 2017–2023; a one-attempt test of this
new rule does not make that period globally pristine.

## One base event, two registered development variants

- Listed domestic common stocks including later delistings
  while eligible. Require 20 prior matched sessions, prior
  split-adjusted close at least $3, prior median daily dollar
  turnover at least $2 million and prior market cap in
  [$50 million, $10 billion). Universe membership uses prior
  panel columns only.
- Use normal sessions closing at 16:00. At decision t from
  10:00 through 13:45 ET inclusive, require all sixteen actual
  consecutive regular-session bars t−15 through t, with finite
  positive closes, positive integer share volumes and observed
  positive integer transaction counts. No missing minute or
  missing count may be imputed. Let P_i, V_i and N_i be
  the close, volume and transaction count of each bar.
- The shock comprises ten ending bars t−14 through t−5,
  measured from anchor close P_(t−15). Require
  P_(t−5) <= 0.90 P_(t−15). Define Q_1 as the sum
  P_i V_i over those ten bars; require Q_1 at least 10%
  of prior median daily dollar turnover.
- The subsequent phase comprises t−4 through t. Let Q_2
  be its total proxy dollar turnover. Require Q_2 >= Q_1/4,
  corresponding to at least half the shock's turnover rate.
  Let n_1 and n_2 be transaction counts summed over the two
  phases, and v_1 and v_2 their summed share volumes.
  Require n_1 >= 200 and n_2 >= 100.
- Define J_1 = log(P_(t−15)/P_(t−5))/n_1 and
  J_2 = max(0, log(P_(t−5)/P_t))/n_2. Define the remaining
  discount D = 1 − P_t/P_(t−15), and score
  S = D × max(0, 1 − J_2/J_1).
  Require D >= 0.08, S >= 0.06, P_t >= 1.01 P_(t−1)
  and decision-bar proxy turnover at least $40,000. This
  measures diminishing adverse movement per aggregate-recorded
  transaction, not a true impact coefficient or causal supply.
- **Control:** use the first base event per symbol only.
- **Primary:** consider exactly the same first base event, then
  buy only if n_2/5 >= 1.5(n_1/10) and
  v_2/n_2 <= 0.5(v_1/n_1). Implement these as integer
  inequalities 4 n_2 >= 3 n_1 and 2 v_2 n_1 <= v_1 n_2.
  A rejected first base event cannot be rescued by a later
  event that day. This keeps the primary events an exact
  subset of control events and isolates the registered filter.

There are two development configurations: `development`
(primary, fragmentation required) and `development_control`
(base event only). Both will run, even if the primary fails.
Only the primary can advance. There is no threshold grid,
alternative timing rule, news filter or eligible control
validation. No favorable subset may replace the primary.

## Trading and cost contract

Use $20,000 equity and buying power, $2,000 target per order,
ten positions or reservations, five-percent share participation
and `ibkr_pro_tiered`. Buy at market only in t+1, cancelling
unfilled shares at that minute's end. Start market liquidation
120 clock minutes after first fill, with the platform's regular
session closing-auction fallback. Flatten-before-close is zero.
There are no stops or targets. Positions open and close that
date. Doubled slippage changes costs, with fees held fixed.

The regular event study estimates fixed-dollar entry and r_120
from minute closes, uses entry-bar costs for both legs, ignores
capital conflicts and can enter after the order's expiry. Report
both the whole study and its next-clock-minute subset; apply
all gates to both. The portfolio phase is required to test actual
participation, expiry and liquidation. These approximations do
not certify executable quotes, liquidity at the opening print,
halts or auction allocation. No platform changes are proposed.

## Selection and validation gates

1. Run both development event studies on 2003-09-10 through
   2016-12-30. Judge r_120 only. For the primary require
   150 events on 90 dates overall and 40 events in 2013–2016;
   mean gross at least +3% and positive mean stressed net
   in both windows; a strictly positive full-period 95%
   day-clustered lower gross bound. Apply these bars to the
   next-clock-minute subset as well. Additionally the primary
   stressed mean must exceed the control stressed mean both
   overall and in 2013–2016, in both full and on-time samples.
   This tests whether the extra filter helps. Park after any
   miss. The control cannot advance regardless of its outcome.
2. Only after a committed develop verdict, run the primary
   development portfolio once. Require 150 trades on 90 dates
   overall and 40 trades in 2013–2016, mean net at least
   +2.5% at base costs and above +1% at doubled slippage in
   both windows, full stressed annualised daily Sharpe above
   one and worst stressed end-of-day drawdown below $10,000.
3. If selected, run the frozen primary validation once on
   2017-01-03 through 2023-11-08. Require +3% mean net
   across all completed trades at base costs and at least
   +1% at doubled slippage both overall and separately on
   2022-01-03 through 2023-11-08; 150 trades on 90 dates
   overall and 50 on 30 dates recently; positive base mean
   in 2017–2021; full stressed daily Sharpe above one and
   stressed drawdown below $10,000. No tuning or second try.

Count every run in the family. Report both costs, counts,
annual results, daily P&L t-statistics, worst drawdown and mean
winners and losers, with event diagnostics distinguished from
portfolio results. Report capacity and expiry limitations,
the control and whether saved common events match exactly.

## Research limits and exposure record

Volume/count is a vendor-aggregate proxy. Trade conditions and
order splitting affect it; it does not establish that small
uninformed traders replaced informed sellers. No same-day news
absence or earnings surprise is inferred. The panel's market-cap,
category and corporate-action weaknesses remain. This is an
adaptive research follow-up with extensive prior looks.

An earlier documentation search exposed illustrative post-seal
AAPL rows. See `docs/checkpoints/gpt-2026-11-18-documentation-exposure.md`.
This new registration occurs after that recorded incident and
does not claim zero historical post-seal exposure. No sample
price or volume is used here. No new post-seal lookup, raw write,
download, rebuild, sealed-folder access or date on or after
2023-11-09 is permitted in the studies.

Implementation note before the first run: inclusive floating-
point price and score comparisons allow one adjacent representable
value, with economic thresholds unchanged. Fragmentation tests
use Python integer cross-products. Synthetic tests cover the
score, first-base-event restriction, primary/control subset,
missing bars and counts, both prefix replays, next-minute expiry
and the distinct study-close/portfolio-open exit conventions.
