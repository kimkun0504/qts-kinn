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
