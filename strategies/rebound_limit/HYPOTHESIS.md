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
