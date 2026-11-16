# Hypothesis and development plan: rebound with a limit-order entry

Written 2026-11-15 by claude, before any run of it. Family `intraday_rebound` (11 trials so far).
The owner asked for the signal to be developed further and backtested on a much larger sample.

## Rationale

Two results so far: paying the spread kills the trade (market order: −0.09% net on 108,945
events), and a resting bid turned the point estimate positive on a 415-event tick sample (+0.56%
per fill, interval including zero). So the entry must be passive, and the remaining question is
which *events* are worth resting a bid on. The fills of a passive order are the weaker half of
the events (adverse selection), so a filter that removes the events that keep falling is worth
more than any exit rule.

## How this differs from the event study

- **A full backtest in the minute engine**, on every event, with portfolio limits: $10,000
  buying power, $500 a position, resting orders reserve capital, 5% of a bar's volume at most.
- **Entry:** a buy limit placed after the event bar at `event bar close × (1 − offset)`, resting
  for a fixed number of minutes. It fills only if a later bar trades at least one tick **below**
  the limit, at the limit price (no price improvement).
- **Exit:** the closing auction at the official close (10 bps modelled slippage, auction fees).
  No stops or targets: the event study and the old build both found they lower the average.
- Minute bars cannot see the queue. The tick sample is the check on that: bar-based fills here
  should be read against its 62% strict fill rate.

## Development protocol (fixed now)

1. **Development period: 2003-09-10 to 2016-12-30.** All variants run here.
2. **Validation period: 2017-01-03 to 2023-11-08.** Untouched by the search. Exactly **one**
   variant is run there: the one chosen by rule 4. (The base event study did show per-year
   numbers for these years, for the market-order form only.)
3. **The variants are listed below and nowhere else.** No variant is added after results are seen
   without a dated addendum, and every run is a counted trial.
4. **Selection rule:** among variants with at least 1,500 trades in development, the highest
   **t-statistic of daily P&L at 2× slippage**. Ties go to the simpler variant (fewer filters).
5. **Worth developing** if the chosen variant, in validation, has net return per trade at 1×
   slippage of at least **+0.5%** with a daily-P&L t-statistic of at least 2, and is positive at
   2× slippage. Otherwise park.
6. The holdout (from 2023-11-09) is not touched.

## Variants (17)

Common to all: the base event (first regular-session bar closing at least `drop` below the prior
close between 09:35 and 15:00; no gap-down open beyond 5%; no 8-K since the prior session;
pre-market dollar volume under 5% of ADV); universe: listed common stock, prior close ≥ $1,
ADV ≥ $250k.

| Config | Drop | Limit offset | Rest (min) | Extra filter |
|---|---|---|---|---|
| `base_o0`, `base_o1`, `base_o2` | 10% | 0, 1%, 2% | 10 | none |
| `deep15_o0`, `deep15_o1` | 15% | 0, 1% | 10 | none |
| `deep20_o0`, `deep20_o1` | 20% | 0, 1% | 10 | none |
| `liquid_o0`, `liquid_o1` | 10% | 0, 1% | 10 | ADV ≥ $10M |
| `calm_o0`, `calm_o1` | 10% | 0, 1% | 10 | at most 10 earlier events that session |
| `fast_o0`, `fast_o1` | 10% | 0, 1% | 10 | fell at least 5% in the last 15 minutes |
| `early_o0`, `early_o1` | 10% | 0, 1% | 10 | event before 11:00 |
| `rest30_o1` | 10% | 1% | 30 | none |
| `calm_liquid_o1` | 10% | 1% | 10 | calm session and ADV ≥ $10M |

Why each filter: **deep** drops are more likely liquidations; **liquid** names cost least and were
the only positive bucket; **calm** sessions exclude market-wide selloffs, where drops are
information; **fast** drops look like one seller; **early** events have the most time to recover.

## Risks

1. **Seventeen variants on a period the family has already seen** in aggregate: the best will
   look better than it is. Validation and the trial count are the defence.
2. **Bar-based fills** overstate or understate real queue outcomes.
3. **Auction exit** in thin names is modelled, not measured.
4. **Capital**: on selloff days there are hundreds of events and $10,000 runs out; the backtest
   takes orders in time order, which is what would happen live.

## Addendum, 2026-11-15 15:30 ET: sizing changed by the owner before any result

The owner set the account to **$20,000** and positions to **$2,000** (was $10,000 and $500). The
17 runs already started at the old sizing were stopped after 35 of 160 months and marked
abandoned; none had produced a result and none was read. The same 17 variants now run at the new
sizing. Expected effect: the $0.35 minimum commission matters less (about 2 bps a side instead of
7), while the 5% participation cap and market impact matter more, and at most ten positions or
resting orders fit at once.

## Addendum, 2026-11-15 15:50 ET: variant chosen for validation

Development finished (17 counted runs, sweep `20261115T202957Z_rebound_limit_17`). By rule 4 the
chosen variant is **`base_o2`**: drop 10%, limit 2% below the event bar's close, resting 10
minutes, no extra filter (7,269 trades; daily-P&L t-statistic at 2× slippage 2.93, the highest
among variants with at least 1,500 trades). It is run once on 2017-01-03 to 2023-11-08 as
`validation_base_o2`, with identical parameters and sizing.

## Addendum, 2026-11-15 16:25 ET: risk rules (written before any run of them)

The validated variant `base_o2` lost $20,763 peak to trough on a $20,000 account. The signal is
unchanged below; only risk rules are added. Three kinds, each using only what is known at the time:

- **Entry cap:** at most N filled entries a session.
- **Daily loss limit:** no new entries once the session's marked-to-market P&L (closed trades at
  their net result, open positions at the last traded price) is at or below −L dollars.
- **Circuit breaker:** after the last 20 sessions' net P&L is at or below −B dollars, stop trading
  for the next 10 sessions.

**Variants (7), development period only (2003-09-10 to 2016-12-30):**

| Config | Entry cap | Daily loss limit | Circuit breaker |
|---|---|---|---|
| `risk_cap5` | 5 | none | none |
| `risk_loss300` | none | $300 | none |
| `risk_loss600` | none | $600 | none |
| `risk_brk2000` | none | none | $2,000 |
| `risk_brk4000` | none | none | $4,000 |
| `risk_cap5_loss600` | 5 | $600 | none |
| `risk_all` | 5 | $600 | $4,000 |

**Selection rule:** among variants whose total net at 2× slippage is at least 70% of `base_o2`'s
in development ($52,772 × 0.7 = $36,940), the highest ratio of total net to worst drawdown, both
at 2× slippage. If none qualifies, no risk variant is validated and the finding is reported.

**Validation (one run, 2017-01-03 to 2023-11-08):** the chosen variant passes if its worst
drawdown at 1× slippage is at most **$8,000** (40% of the account), net per trade at 1× is at
least **+0.4%**, and the daily-P&L t-statistic at 1× is at least **2**.

Each of the 7 runs and the validation run is a counted trial (family total would reach 37).

## Addendum, 2026-11-15 18:40 ET: entry depth, exits and price (written before any run)

**Why.** Risk rules did not help (above). Three things have not been tried on the limit-order
version: a deeper limit (results improved steadily from 0% to 2% below the event bar's close),
any exit other than the close, and a minimum price (commission is 17.6 bps of a round trip here
because many events are in stocks under $5, where $2,000 buys many shares).

**Data.** These runs use build `6453bd3ec8`, in which dividend amounts, split dates and spinoffs
were corrected (docs/data/DATA_NOTES.md). `base_o2` is run again on it as the reference.

**Variants (10), development period only (2003-09-10 to 2016-12-30), $20,000 account, $2,000
positions.** Each differs from `base_o2` in one setting, except the last.

| Config | Change from `base_o2` |
|---|---|
| `x_ref` | none (the reference, on corrected data) |
| `x_o3` | limit 3% below the event bar's close |
| `x_o4` | limit 4% below |
| `x_t60` | sell at the market after 60 minutes |
| `x_t120` | sell at the market after 120 minutes |
| `x_tp3` | resting sell 3% above the entry price; otherwise the close |
| `x_tp5` | resting sell 5% above the entry price; otherwise the close |
| `x_sl7` | stop 7% below the entry price |
| `x_p5` | only stocks with a previous close of at least $5 |
| `x_o3_tp5` | limit 3% below and a resting sell 5% above |

**Selection rule:** among variants with at least 2,000 trades and a net return per trade of at
least +0.5% at 2× slippage, the highest t-statistic of daily P&L at 2× slippage.

**Validation (one run of the chosen variant, 2017-01-03 to 2023-11-08, corrected data):** passes
if net per trade at 1× is at least **+0.5%**, the daily-P&L t-statistic at 1× is at least **2**,
net per trade at 2× is **above zero**, and the worst drawdown at 1× is at most **$10,000**.

The validation years have now been used three times in this family. A pass here is weaker
evidence than the first pass was; the holdout and paper trading remain the real tests.

Each of the 10 runs and the validation run is a counted trial (family total would reach 48).

## Addendum, 2026-11-15 19:50 ET: targets changed by the owner; fill check on real trades

Written before any tick data for these orders was requested or read.

**Targets (owner, 2026-11-15).** The 3–4% a trade target is replaced. A strategy is a candidate
for paper trading when, out of sample, it has **net per trade of at least +1.0% at 2× slippage**,
**Sharpe above 1**, **worst drawdown under half the account**, and **fills confirmed against real
trades**. Intraday is the focus; the daily engine and momentum are parked (decision 0017).

`x_o4` meets the first three on 2017–2023 (+1.20% at 2×, Sharpe 1.43, drawdown $8,925 of
$20,000). This addendum is the fourth.

### Hypothesis

The minute-bar fill rule reports fills a real resting order would have had. For an `x_o4` order
that the simulator filled, real trades printed below the limit while the order was live, in at
least the order's size, late enough for a real order to have been in the book.

### Why it could be false

1. **The bar's low is one small print.** The simulator lets the order take 5% of the *whole
   bar's* volume once the low is a tick through the limit. Most of that volume may have traded
   above the limit, before the low.
2. **The print is not one a resting order could meet:** out of sequence, derivatively priced,
   an average-price or contingent trade, or later cancelled.
3. **Latency.** The order is assumed live in the first second after the event bar. A real order
   is live a few seconds later; the prints may already be over.
4. **Before 2007** (Regulation NMS) a trade on one venue could print below a better bid on
   another. A through-print then proves less.
5. **The opposite error.** The rule refuses orders where the price touched the limit and did not
   trade through. Live, some of those fill. They are not in the backtest and may be better or
   worse than the trades that are.

### What is measured

Orders: every traded order of the development run (`…84ff9c3d`, 3,200) and the validation run
(`…eec4a69e`, 1,789), plus a sample of orders the bar rule left unfilled. The orders of both runs
are rebuilt from the same strategy code, config and data build, with the simulator's own fill
function; the rebuilt traded orders must equal the runs' trades exactly. This is a listing of
orders, not a run: it produces no performance number.

For each order, from the vendor's trades and NBBO quotes between the start of the event bar and
the order's expiry (the live window is the 10 one-minute bars after the event bar):

- **Through-prints:** regular-session trades at least one tick below the limit, excluding
  corrected or cancelled trades and trades whose condition codes do not update the
  consolidated high and low (the vendor's own table, downloaded with the data; odd lots are
  therefore excluded, as they are from the bars). Reported also with odd lots included.
- **Confirmed:** at least one through-print while the order was live.
- **Through-volume:** shares in through-prints. A buy at the limit has price priority over every
  one of them.
- **Tick-rule quantity:** the smaller of the simulated quantity and the through-volume, counting
  only prints from **5 seconds** after the event bar ended. Zero means the order did not trade.
- **Tick-rule result:** the trade's P&L recomputed at the tick-rule quantity (same limit price,
  same closing-auction exit, same cost model).
- Supporting evidence, reported and not judged: whether the national best bid fell below the
  limit (every displayed bid at the limit was taken), whether the best ask reached it, volume
  printed exactly at the limit, through-volume as a multiple of the order, results with 0, 5 and
  30 seconds of latency, and 2003–2006 separately from 2007 on.

Everything is reported overall and by market cap of the previous session: under $300M,
$300M–$2B, over $2B.

**Unfilled sample.** Per period and market-cap group, drawn at random with a fixed seed from
orders the bar rule did not fill (whether or not the account had capital for them): 100 where
the low touched the limit, 50 where it came within 1% of it, 30 others. For these the report
gives the share that real trades would have filled (a through-print: the rule missed a fill) and
the share only touched, with what a fill at the limit would have earned to the close.

### Pass bars (set now)

1. **Coverage:** tick data for at least 95% of the traded orders. Below that the check is
   inconclusive and goes back to the owner.
2. **Confirmed:** at least 97% of the traded orders in each period have a through-print while
   live.
3. **Tick-rule result:** on validation, net per trade at 2× slippage of at least **+1.0%** over
   the orders with a tick-rule quantity above zero; and in each period the tick-rule total net
   at 2× is at least **80%** of the simulated total.

All three pass: fills are confirmed, and the deeper-limit search may be registered. Any fails:
the fill rule is replaced by one that matches the ticks before any further search, and `x_o4`'s
numbers are restated under it.

### Micro-caps: how the check decides (set now)

The universe has no market-cap floor. For the under-$300M group alone:

- **Exclude** (a floor at $300M) if under 90% of its traded orders are confirmed, or its
  tick-rule total net at 2× is under 60% of its simulated total in either period: the simulated
  profit there is not obtainable.
- **Keep and stay small** if it passes those and its through-volume is thin (median
  through-volume under 5 times the order): fills are real at $2,000 and would not be at a
  multiple of it.
- **A floor as a variant in the next search** if fills pass and the group's results are not
  consistent between the two periods, so that no floor can be justified from results alone
  without fitting.

### Trials

The tick study is recorded in the run store and charged as one trial (family total 49). It
selects nothing: one variant, fixed. The order listing and the unfilled sample add none.

## Addendum, 2026-11-15 20:10 ET: the losing development years, and a hypothesis from them

Development period only (2003–2016). Nothing below was computed on, or checked against, any
date after 2016-12-30. Script: `research/claude/losing_years.py`, on the 3,200 trades of the
development run `…84ff9c3d`. No run was started.

**What 2013–2015 have in common** (each lost: −$1,235, −$1,176, −$2,302):

1. **Quiet markets.** 80% of their trades came on sessions with fewer than 30 signals (55% in
   the other years), and 70% while SPY was flat or up at the signal. Broad selloff days, where
   the strategy earns most, were rare.
2. **All of the loss is in stocks that were already falling.** Split by the stock's own return
   over the 60 sessions before the event day:

   | | 2003–07 | 2008–09 | 2010–12 | 2013–15 | 2016 | All |
   |---|---|---|---|---|---|---|
   | Had fallen: trades, net/trade at 2×, total | 397, +1.08%, +$6,499 | 821, +1.33%, +$17,767 | 224, +0.20%, +$1,100 | 282, **−1.97%, −$11,462** | 133, +0.50%, +$473 | 1,857, +0.58%, +$14,376 |
   | Had risen | 424, +2.44%, +$18,692 | 360, +2.89%, +$20,170 | 222, +1.36%, +$5,714 | 221, **+1.65%, +$6,750** | 116, +1.22%, +$2,384 | 1,343, +2.15%, +$53,709 |

   Stocks that had risen were profitable in **every one of the 14 years** (+0.78% to +2.99% a
   trade at 2×). Stocks that had fallen lost in 6 of the 14.
3. **Fallers pay only when the market is selling.** On sessions with 30 or more signals they
   earned +1.43% a trade; on quieter sessions −0.28% (−2.30% in 2013–15). With SPY down 0.3% or
   more at the signal: +1.24%; flat or up: +0.11%.

**What did not explain it:** market cap, price, sector (biotech made money in 2013–15; energy
and materials lost, and they were fallers), time of day, size of the drop, and volume up to the
signal. Volume over the *whole day* separates winners from losers strongly (days ending above
5× normal volume lose in every period), but it is known only after the close; the same measure
at the signal time is weak.

**Hypothesis (not tested).** A 10% intraday drop in a stock that has been rising is a liquidity
shock, and it is bought back. The same drop in a stock that has been falling for three months,
on a day when the market is not falling, is the bad news continuing. So: *take the event only
if the stock's return over the 60 sessions before the event day is zero or more.*

**Why to distrust it.** It was found by looking at 14 features of the development trades after
seeing which years lost, so it will look better here than it is. Per trade the relation is weak
(rank correlation 0.02 to 0.17 by period); the evidence is the consistency of the group
averages across periods, not a tight fit. It cuts trades by more than half (to about 100 a year).
It has not been run as a variant even on development: these are the filled trades of the
unfiltered run, and a filter also changes which orders get capital.

**Status.** Proposed to the owner. It is not run on 2017–2023 without the owner's word, and
any run of it, on any period, is a counted trial with its bars written first.

## Addendum, 2026-11-15 20:30 ET: deeper limits and ladders (written before any run of them)

**Why now.** The fill check passed (REPORT.md): the 4%-below fills are real trades, in size, at
$2,000. The entry-depth round ended with the best variant at the edge of the tested range
(0% to 4% below: +0.26% to +1.34% a trade). This round looks past the edge.

**Fixed for every variant, by the owner (not tuned):**

- **No order with a limit price under $1** (`min_limit_price: 1.0`). The universe rule is on the
  previous close, so `x_o4` bought 121 times under $1 (lowest $0.72); those trades earned about
  nothing after 105 bps of costs.
- Everything else as `x_o4`: the same event, 10 minutes of rest, exit in the closing auction,
  $20,000 account, $2,000 a position, build `6453bd3ec8`.

**Variants (12), development period only (2003-09-10 to 2016-12-30).** Six entries, each for all
stocks and for market cap under $300M only (`_m`; companies with unknown market cap are out):

| Config | Entry |
|---|---|
| `s_o4`, `s_o4_m` | one limit 4% below the event bar's close (the reference) |
| `s_o5`, `s_o5_m` | one limit 5% below |
| `s_o6`, `s_o6_m` | one limit 6% below |
| `s_o8`, `s_o8_m` | one limit 8% below |
| `s_l48`, `s_l48_m` | ladder: half the position 4% below, half 8% below |
| `s_l468`, `s_l468_m` | ladder: a third each 4%, 6% and 8% below |

A ladder's orders go in together and each reserves its own capital; each filled rung is one
trade in the counts and averages.

**Why the under-$300M versions.** The owner wants to focus there, and the fill check found
those fills real at this size. Against it: in development micro-caps were the weakest size group
(+1.07% a trade at 2× against +1.27% and +2.83%); the case for them comes from the validation
years. So they compete on development under the same rule as everything else.

**Not in this round:** the prior-trend filter (addendum of 20:10 ET). The owner has not decided,
and it needs a new column in the data build.

**Selection rule.** Among variants with at least 1,000 trades in development, net per trade of
at least +1.0% at 2× slippage and a worst drawdown at 2× of at most $10,000: the highest
t-statistic of daily P&L at 2× slippage. Ties go to the simpler variant (one limit before a
ladder, all stocks before under-$300M).

**Validation (one run of the chosen variant, 2017-01-03 to 2023-11-08).** It passes on the
owner's targets: net per trade at 2× of at least **+1.0%**, Sharpe at 2× **above 1**, worst
drawdown at 2× **under $10,000** (half the account).

- If the rule chooses `s_o4` or `s_o4_m`, **no validation run is made**: the validation result
  of the 4% limit is already known (`x_o4`, and its under-$300M trades), and the finding is that
  going deeper does not beat it.
- A pass for an under-$300M variant is weak evidence: the 4% limit's under-$300M trades are
  already known to have done well in those years.
- The validation years have been used four times in this family. This would be the fifth.
- Before paper trading, the chosen variant needs its own fill check: a deeper limit fills on
  rarer, sharper prints than the ones checked so far.

**Trials.** 12 development runs and at most one validation run: the family total goes from 49
to 61 or 62.

## Addendum, 2026-11-15 20:40 ET: variant chosen for validation

Development finished (12 counted runs, sweep `20261116T013106Z_rebound_limit_12`). Eligible by
the rule: all but `s_o8`, `s_o6_m` and `s_o8_m` (under 1,000 trades). The highest daily-P&L
t-statistic at 2× slippage among the eligible is **`s_l468`** (5.30): all stocks, a third of the
position each 4%, 6% and 8% below the event bar's close. It is run once on 2017-01-03 to
2023-11-08 as `validation_s_l468`, with identical parameters and sizing.

## Addendum, 2026-11-15 21:05 ET: fill check for the ladder (written before its plan is built)

**What is checked.** The same hypothesis, measures and pass bars as the fill check of `x_o4`
(addendum of 19:50 ET), unchanged, applied to every filled rung of `s_l468`: development run
`…3d866b2f` (5,653 rung trades) and validation run `…437947d4` (3,001), plus the same sample
of unfilled orders per period, market-cap group and kind, drawn from the ladder's rung orders.
Results are also reported by rung (4%, 6%, 8%).

**Pass bars (the same three):** tick data for at least 95% of the traded rungs; at least 97%
confirmed by a through-print in each period; on validation, net per trade at 2× of at least
+1.0% at the tick-rule quantity with 5 seconds of latency, keeping at least 80% of the
simulated net at 2× in each period.

**What has already been seen.** A preview on the ticks downloaded for `x_o4` covered 96% of the
ladder's validation rung trades and 95% of development's, all confirmed (REPORT.md). The rungs
not covered are events `x_o4` had no capital for; they earn more than average, so the preview
could not stand in for the check. The bars above were set before the preview and are not
changed by it.

**Data.** Windows already downloaded for `x_o4` (plan `fillcheck_x_o4`) are read where they
are; the owner downloads only the missing windows (plan `fillcheck_s_l468`). A ladder's rungs
share one window: the event bar to the orders' expiry.

**Trials.** Recorded in the run store and charged as one trial (family total 66).

## Addendum, 2026-11-15 21:22 ET: the prior-trend filter (written before any run of it)

The owner asked for the hypothesis of the 20:10 ET addendum to be developed and, if it earns
it, validated.

**Hypothesis.** A 10% intraday drop in a stock that has not been falling is bought back; in a
stock that has fallen over the previous 60 sessions it is the bad news continuing. Rule: *take
the event only if `ret60_prev` is zero or more.*

**Data.** `ret60_prev` is a new panel column in build `447e58e098` (data-6): the split-adjusted
price return over the 60 sessions ending at the previous close, known before the open, empty
until a company has 60 sessions (those companies are left out by the rule). Every other column
of the build is identical to `6453bd3ec8`, row for row (26.4 million rows compared), so runs
on the two builds are comparable; the column matches an independent calculation.

**Variants (2), development period only (2003-09-10 to 2016-12-30):**

| Config | What | Compared with |
|---|---|---|
| `t_l468` | `s_l468` (thirds at 4%, 6%, 8% below) with the rule | `s_l468` |
| `t_o4` | `s_o4` (one limit 4% below) with the rule | `s_o4` |

One threshold only (zero), as the hypothesis was stated. `t_o4` is there to read the rule's
effect on the plain strategy; it is not a candidate.

**Gate to validation (on development).** `t_l468` is validated only if its Sharpe at 2×
slippage is above `s_l468`'s (1.45), with net per trade at 2× of at least +1.0% and a worst
drawdown at 2× of at most $10,000. Otherwise there is no validation run and the rule is parked.

**Validation (one run of `t_l468`, 2017-01-03 to 2023-11-08).**

- It **passes** on the owner's targets: net per trade at 2× at least +1.0%, Sharpe at 2× above
  1, worst drawdown at 2× under $10,000.
- It **replaces `s_l468` as the candidate** only if it passes and also has a higher Sharpe at
  2× than `s_l468` had in validation (1.37) and at least 70% of its total net at 2×
  ($29,201 × 0.7 = $20,441). A pass that is not better leaves `s_l468` the candidate.

**Why to distrust a good development result.** The rule was found on the development trades of
`x_o4`, which are most of `s_l468`'s 4% rungs. Development will flatter it. Validation is the
test, and it would be the sixth use of those years in this family.

**Trials.** Two development runs and at most one validation run.

## Addendum, 2026-11-15 21:29 ET: the trend filter passed the development gate

Development (sweep `20261116T022246Z_rebound_limit_2`, build `447e58e098`): `t_l468` has a
Sharpe at 2× of 1.64 against `s_l468`'s 1.45, +2.64% a trade at 2× and a worst drawdown at 2×
of $1,682. The gate is passed, so `t_l468` is run once on 2017-01-03 to 2023-11-08 as
`validation_t_l468`, with identical parameters and sizing. (`t_o4`: Sharpe 1.77, +2.26%.)

## Addendum, 2026-11-15 22:24 ET: the holdout (written before the data is unsealed)

The owner proposed spending the holdout now. Reason: 2022 and 2023 lost a little (−$884,
−$406), more than half the validation profit is 2020, and validation cannot say whether the
strategy is flat in grinding markets and pays in panics, or has faded. The holdout (from
2023-11-09) is the only data that can.

**What is run: one run, one variant.** `s_l468` exactly as validated: the same strategy code
and parameters, $20,000 account, $2,000 positions, no order under $1. Config
`holdout_s_l468`, 2023-11-09 to 2026-11-06 (the last session before the Sharadar snapshot of
2026-11-09, which is where filings and splits end). Nothing else is run on the holdout: not
`x_o4`, not the trend filter, no second variant.

**Rule, set now and followed whatever the result:**

| Holdout result at 2× slippage | What it means | What happens |
|---|---|---|
| Net per trade at least +1.0%, Sharpe above 1, worst drawdown under $10,000 | **Pass** | Paper trading. A fill check on the holdout trades follows |
| Net per trade at or below zero | **Fail** | The strategy is parked. No change is made and re-tested on the holdout |
| Anything between | **Not proven** | Paper trading at small size is the tiebreaker. No tuning on the holdout |

**How much three years can say.** About 750 sessions. A strategy whose true Sharpe is 1.4
shows under 1 in roughly one sample in four of this length, so a narrow miss on Sharpe alone
is weak evidence. A negative result is strong evidence.

**Reported, not judged:** by year, by market-cap group, by rung, the sessions with the most
signals, and the same figures beside validation.

**Who does what.** Unsealing is the owner's action (AGENTS.md): the owner runs the commands
with `KINN_UNSEAL_TOKEN`; every unseal is logged. The agent writes and tests the commands on
synthetic data and on open data, never reads `MarketData/sealed/`, and reads only the run's
outputs afterwards. The unsealed data is built into its own folder; the research build and its
seal stay as they are, and the unsealed build must reproduce the research build exactly on
every date before 2023-11-09, checked by the build itself.

**After the unseal.** The holdout is spent for this family. No later variant of the rebound can
be judged on it. The run is a counted trial.

## Addendum, 2026-11-15 22:55 ET: the holdout data check, before the run

The owner built the unsealed data. No strategy has been run on it. The first check compared
whole rows exactly and reported 4.75 million of 26.4 million pre-seal rows as different, with
6,062 more rows in the unsealed build. I have not read the unsealed build; what follows is from
the code and from a test on open data.

- **Cause of most of it (shown on open data):** `ret60_prev` is a running sum of logarithms.
  Recomputing it for 2021-2022 with 1% of companies removed changed the last digits of 8% of
  the remaining rows, by about 1e-16. The unsealed build holds a slightly different set of
  companies and was built on another machine. `s_l468` does not use this column.
- **One real inconsistency, fixed:** the unsealed build kept names with no first price date,
  which the research build drops. It now drops them too, and is rebuilt.
- **Expected extra rows:** companies delisted after the seal whose ticker was reused. The
  research build cannot match them (it does not know they were delisted); the unsealed build
  can. That is the unsealed build being right, not a fault in it.

**The check is replaced, before any run, by a stricter and more specific one:**

1. Row by row and column by column on every date before the seal. No research row may be
   missing. Every column must be equal, decimals within one part in 10^9. Extra rows are
   allowed only for the delisted-and-reused reason; anything unexplained fails.
2. **Rehearsal:** the validation config `validation_s_l468` is run through the unsealed data
   (a scratch run, not a trial, dates before the seal only) and must reproduce the research
   validation run trade for trade: same trades, prices and profit.

The holdout run starts only if both pass. The rule for the result (Pass / Fail / Not proven)
is unchanged.

## Addendum, 2026-11-15 23:20 ET: check and rehearsal results; one named exception

Still no strategy run on the holdout. The owner ran the new check and the rehearsal.

- **Rehearsal passed.** `validation_s_l468` through the unsealed build gave the research
  run's 3,001 trades exactly: same trades, prices and profit ($31,159.76).
- **Rounding confirmed.** 4,751,651 rows differ in `ret60_prev` by at most 4e-13; 19 and 20
  rows differ in `prev_close` and `split_ratio` by at most 2e-13. Nothing beyond tolerance.
- **Extra rows, as expected:** two companies delisted after the seal with reused tickers
  (`SIX1`, 3,371 rows; `SUPN1`, 2,796 rows).
- **One exception, not expected:** 105 research rows of `SUPN` (2023-06-12 to 2023-11-08) are
  missing from the unsealed build. Sharadar holds two records for that one traded symbol:
  `SUPN1` (history from 2012, delisted after the seal) and `SUPN` (first priced 2023-06-12).
  The research build cannot match `SUPN1`, so it sees one claim on the symbol. The unsealed
  build matches both, and from 2023-06-12 the symbol has two claims. The panel's standing
  rule drops a symbol with two claims.

**Decision (proposed; the owner confirms by running):** keep the standing rule. One stock is
left out of the unsealed universe while both records claim its symbol. The cause is a vendor
record, not anything about returns, and the rehearsal shows it changes no validation trade.
Choosing between the two records by hand, after seeing unsealed data, would be a rule made
for this run. The check now recognises this case by its mechanism (a research row whose symbol
is also claimed, on that date, by a company delisted after the seal with a reused ticker) and
fails on any other missing row.
