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
