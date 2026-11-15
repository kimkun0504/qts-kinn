# Checkpoint: Phase 2 (research core), 2026-11-15

**Done.** Core types, features with declared availability, IBKR cost model, sizing, the intraday
simulator, `kinn run` with run folders and the registry, the tearsheet, and the validation
statistics. 72 tests pass; 5 import contracts hold.

## Canary results

| Canary | Result | Test |
|---|---|---|
| A hidden next-bar feature is caught | **Caught**: `LookaheadError` for the feature, for a strategy built on it, for a strategy that buys the day's low, and for a back-dated signal. An honest feature passes | `tests/canary/test_lookahead_canary.py` |
| Random entries lose money after costs | **Lose**, on synthetic random walks (test) and on real data (below) | `tests/canary/test_engine_canaries.py` |
| Identical configurations give identical results | **Identical** trade tables across two runs, different agents, serial and parallel | same file |
| The past does not change when later data is added | **Unchanged** | `tests/test_data_build.py` |

## Random-signal run on real data

Run `20261115T190228Z_claude_random_entry_475077bb`: ten random market buys a session in liquid
common stocks (price ≥ $5, ADV ≥ $2M), each held one hour, $500 positions, 2018–2019.

| | 1× slippage | 2× slippage |
|---|---|---|
| Net return per trade | −0.30% | −0.43% |
| Win rate | 26.2% | 19.8% |
| Total net on 4,990 trades | −$7,183 | −$10,179 |

Gross mean return per trade: −0.00% (no edge, as it must be). Round-trip costs in bps of entry
notional: commission 14.8, other fees 2.8, slippage 12.7. The tearsheet is in the run folder
(`tearsheet.html`).

**The number to remember: at $500 a position, a round trip in liquid stocks costs about 0.30%.**
Half of that is the $0.35 minimum commission on each order. A strategy targeting 3–4% a trade
clears this easily; one earning 0.3–0.7% a trade (the old stage-2 result) does not have much
left.

## How lookahead is prevented

1. `PRIOR_DAY` features are computed from prior-session columns only; they never receive
   today's bars.
2. The engine replays sampled sessions cut off at a random minute. If any signal up to the cut
   changes when later bars are removed, the run stops with `LookaheadError`.
3. A signal from bar *m* can fill from bar *m + 1* at the earliest.
4. Strategies see a `DayView` without the day's official close or any other outcome.

## Open points

- The half-spread table is a fallback, not a measurement (decision 0010).
- The lookahead replay is sampled (`lookahead_check_rate`, default 10% of sessions with
  signals). Use 1.0 for a strategy's first runs.
- Day-trading rules: FINRA replaced the pattern-day-trader rule on 2026-06-04 (brokers have
  until 2027-10-20 to implement). Whether IBKR already lets a $10k margin account day trade
  freely is for the owner to confirm; the simulator assumes it does.
- Deferred items: decision 0010.
