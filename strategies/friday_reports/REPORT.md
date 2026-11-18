# Friday reports: a little more drift, not enough to trade alone

**Verdict: closed.** 4 cells on 2010 to 2017, none meets the bar set in
[HYPOTHESIS.md](HYPOTHESIS.md), so no test was run. 4 trials. The holdout is untouched.

Rule A50's test read on the session after a results report whose first reaction fell on the
last session of a week (a Friday, or before a holiday): 94,022 of 422,205 reaction sessions.
Code: `research/claude/friday_reports.py`.

| 2010–2017, after costs | Friday reports | Weekly t | Same rule, other days | Weekly t |
|---|---|---|---|---|
| Rise of 15%+, $50M–$300M | 3.38% (136) | 2.05 | 2.99% (385) | 2.83 |
| Rise of 10%+, $50M–$300M | 2.47% (215) | 1.57 | 2.46% (598) | 3.24 |
| Rise of 15%+, $300M–$2B | 1.70% (378) | 2.76 | 1.39% (1,085) | 2.89 |
| Rise of 10%+, $300M–$2B | 1.52% (631) | 2.31 | 1.11% (1,903) | 3.05 |

Results read on a Friday drift a quarter to 0.4 of a point more over 15 sessions, which
agrees with the published finding that Friday news is absorbed more slowly. It is too little,
on too few trades, to be a rule of its own.

## Reproduce

```
cd research/claude
uv run python swing_timed.py table
uv run python friday_reports.py fridays
uv run python friday_reports.py search
```
