# Runner close: no trade in the last hour or overnight after a run

**Verdict: closed.** 16 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 16 trials. The holdout is untouched.

9,621 readings at 15:00 of a stock whose high was 30% or more over the previous close on five
times volume ($50M and over before the run), 2005 to October 2023. Bought at the high or sold
short at the low of the 15:00 minute. Code: `research/claude/runner_close.py`.

| 2010–2017, after costs | Trades | A trade | Weekly t | Years positive |
|---|---|---|---|---|
| Holding at 15:00, run 30–60%: bought, to the close | 1,458 | −0.44% | −4.66 | 0 of 8 |
| … to the next open | 1,458 | −0.18% | −1.68 | 3 of 8 |
| … to the next close | 1,458 | −0.51% | −2.68 | 2 of 8 |
| … sold short at the close, to the next open | 1,458 | −0.66% | −4.12 | 0 of 8 |
| Holding, run 60%+: bought, to the next open | 232 | +0.85% | 1.12 | 5 of 8 |
| … sold short at the close, to the next open | 232 | −1.73% | −2.79 | 1 of 8 |
| Fading, run 60%+: sold short, to the close | 33 | +1.46% | 1.31 | 6 of 8 |
| Fading, run 60%+: bought at the close, to the next open | 33 | +0.87% | 0.49 | 5 of 8 |

- **A runner still near its high at 15:00 slips a little into the close** (about a quarter of
  a percent before costs) **and is a little higher the next morning.** Neither is large
  enough to trade either way.
- **The collapse the owner saw is rare in this universe.** A stock of $50M or more that has
  run 30% and is already 25% under its high by 15:00 turned up 52 times in eight years.
  Sold short from there to the close it made 1.5% on 33 trades, which proves nothing.
- **Selling a runner short overnight loses** in every year for the 30% to 60% runs.

Not tested: runs in companies under $50M, where most such collapses happen and where borrow
is least likely; the middle group (10% to 25% under the high), which the plan did not trade.

## Reproduce

```
cd research/claude
uv run python runner_close.py events
uv run python runner_close.py collect 2005 2023
uv run python runner_close.py search
```
